"""
Authentication business logic handlers.

Implements core authentication operations including user registration,
login, password management, and session handling with comprehensive
security features.
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import structlog

from services.shared.models.users import (
    User, Role, UserRole, UserSession, AuthEvent, PasswordHistory
)
from .exceptions import (
    InvalidCredentialsError,
    AccountLockedError,
    DuplicateUserError,
    UserNotFoundError,
    PasswordValidationError,
)
from .password import (
    hash_password,
    verify_password,
    validate_password_strength,
    check_password_history,
)
from .tokens import TokenManager
from .permissions import get_role_scopes, MANUFACTURING_ROLES
from .schemas import (
    UserCreate,
    UserUpdate,
    LoginRequest,
    TokenResponse,
    UserResponse,
)

logger = structlog.get_logger()


class AuthenticationHandler:
    """
    Handles authentication operations with security features.
    
    Features:
    - User registration with email verification
    - Secure login with brute force protection
    - Password reset workflow
    - Session management
    - Audit logging
    """
    
    def __init__(
        self,
        db: AsyncSession,
        token_manager: TokenManager,
        max_login_attempts: int = 5,
        lockout_duration_minutes: int = 15
    ):
        """
        Initialize authentication handler.
        
        Args:
            db: Database session
            token_manager: Token management instance
            max_login_attempts: Maximum failed login attempts before lockout
            lockout_duration_minutes: Account lockout duration
        """
        self.db = db
        self.token_manager = token_manager
        self.max_login_attempts = max_login_attempts
        self.lockout_duration_minutes = lockout_duration_minutes
    
    async def register_user(
        self,
        user_data: UserCreate,
        client_ip: str,
        assigned_by: Optional[UUID] = None
    ) -> User:
        """
        Register a new user.
        
        Args:
            user_data: User registration data
            client_ip: Client IP address
            assigned_by: User ID who created this account (for admin creation)
            
        Returns:
            Created user instance
            
        Raises:
            DuplicateUserError: If username or email already exists
            PasswordValidationError: If password doesn't meet requirements
        """
        logger.info("user.registration.started", username=user_data.username)
        
        # Check if user already exists
        existing_user = await self._get_user_by_username_or_email(
            user_data.username, user_data.email
        )
        
        if existing_user:
            logger.warning(
                "user.registration.duplicate",
                username=user_data.username,
                email=user_data.email
            )
            raise DuplicateUserError("Username or email already exists")
        
        # Validate password strength
        validate_password_strength(user_data.password)
        
        # Hash password
        password_hash = hash_password(user_data.password)
        
        # Create user
        user = User(
            username=user_data.username.lower(),
            email=user_data.email.lower(),
            password_hash=password_hash,
            full_name=user_data.full_name,
            department=user_data.department,
            employee_id=user_data.employee_id,
            is_active=True,
            is_verified=False,  # Requires email verification
            last_password_change=datetime.utcnow(),
        )
        
        self.db.add(user)
        await self.db.flush()  # Get user ID
        
        # Assign default role
        await self._assign_role(user.id, user_data.role, assigned_by)
        
        # Create password history entry
        await self._add_password_history(user.id, password_hash)
        
        # Log registration event
        await self._log_auth_event(
            event_type="user_registered",
            user_id=user.id,
            username=user.username,
            client_ip=client_ip,
            success=True,
        )
        
        await self.db.commit()
        await self.db.refresh(user)
        
        logger.info("user.registration.completed", user_id=str(user.id), username=user.username)
        
        return user
    
    async def authenticate(
        self,
        credentials: LoginRequest,
        client_ip: str,
        user_agent: str
    ) -> Dict[str, Any]:
        """
        Authenticate user and create session.
        
        Args:
            credentials: Login credentials
            client_ip: Client IP address
            user_agent: Client user agent
            
        Returns:
            Token response with user data
            
        Raises:
            InvalidCredentialsError: If credentials are invalid
            AccountLockedError: If account is locked
        """
        logger.info("authentication.attempt", username=credentials.username, ip=client_ip)
        
        # Get user with roles
        user = await self._get_user_by_username_or_email(credentials.username)
        
        if not user:
            await self._log_auth_event(
                event_type="login_failed",
                username=credentials.username,
                client_ip=client_ip,
                success=False,
                failure_reason="invalid_username",
            )
            raise InvalidCredentialsError()
        
        # Check if account is locked
        if user.is_locked:
            if user.locked_until and user.locked_until > datetime.utcnow():
                await self._log_auth_event(
                    event_type="login_failed",
                    user_id=user.id,
                    username=user.username,
                    client_ip=client_ip,
                    success=False,
                    failure_reason="account_locked",
                )
                raise AccountLockedError(
                    lockout_until=user.locked_until.isoformat()
                )
            else:
                # Unlock account if lockout period has passed
                user.is_locked = False
                user.locked_until = None
                user.failed_login_attempts = 0
        
        # Verify password
        if not verify_password(credentials.password, user.password_hash):
            await self._handle_failed_login(user, client_ip)
            raise InvalidCredentialsError()
        
        # Check if user is active
        if not user.is_active:
            await self._log_auth_event(
                event_type="login_failed",
                user_id=user.id,
                username=user.username,
                client_ip=client_ip,
                success=False,
                failure_reason="account_inactive",
            )
            raise InvalidCredentialsError("Account is inactive")
        
        # Get user role and permissions
        user_role = await self._get_user_primary_role(user.id)
        scopes = get_role_scopes(user_role)
        
        # Reset failed login attempts
        user.failed_login_attempts = 0
        user.last_failed_login = None
        user.last_login = datetime.utcnow()
        
        # Create token pair
        tokens = self.token_manager.create_token_pair(
            user_id=str(user.id),
            username=user.username,
            email=user.email,
            role=user_role,
            scopes=scopes
        )
        
        # Create session record
        session = await self._create_session(
            user_id=user.id,
            session_id=tokens["session_id"],
            jti=self.token_manager.verify_token(tokens["access_token"]).jti,
            client_ip=client_ip,
            user_agent=user_agent,
            expires_in_seconds=tokens["expires_in"]
        )
        
        # Log successful login
        await self._log_auth_event(
            event_type="login_success",
            user_id=user.id,
            username=user.username,
            session_id=tokens["session_id"],
            client_ip=client_ip,
            success=True,
        )
        
        await self.db.commit()
        
        logger.info(
            "authentication.success",
            user_id=str(user.id),
            username=user.username,
            role=user_role
        )
        
        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": tokens["token_type"],
            "expires_in": tokens["expires_in"],
            "user": UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=user_role,
                department=user.department,
                employee_id=user.employee_id,
                is_active=user.is_active,
                is_verified=user.is_verified,
                mfa_enabled=user.mfa_enabled,
                scopes=scopes,
                created_at=user.created_at,
                last_login=user.last_login,
            )
        }
    
    async def logout(
        self,
        session_id: str,
        user_id: UUID,
        client_ip: str
    ) -> None:
        """
        Logout user and revoke session.
        
        Args:
            session_id: Session identifier
            user_id: User ID
            client_ip: Client IP address
        """
        # Find and revoke session
        result = await self.db.execute(
            select(UserSession).where(
                UserSession.session_id == session_id,
                UserSession.user_id == user_id
            )
        )
        session = result.scalar_one_or_none()
        
        if session:
            session.is_active = False
            session.revoked_at = datetime.utcnow()
            session.revoked_reason = "user_logout"
            
            # Revoke token
            self.token_manager.revoke_token(session.jti)
            
            await self._log_auth_event(
                event_type="logout",
                user_id=user_id,
                session_id=session_id,
                client_ip=client_ip,
                success=True,
            )
            
            await self.db.commit()
        
        logger.info("user.logout", user_id=str(user_id), session_id=session_id)
    
    async def change_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str,
        client_ip: str
    ) -> None:
        """
        Change user password.
        
        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password
            client_ip: Client IP address
            
        Raises:
            InvalidCredentialsError: If current password is incorrect
            PasswordValidationError: If new password doesn't meet requirements
        """
        # Get user
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise UserNotFoundError()
        
        # Verify current password
        if not verify_password(current_password, user.password_hash):
            await self._log_auth_event(
                event_type="password_change_failed",
                user_id=user_id,
                client_ip=client_ip,
                success=False,
                failure_reason="invalid_current_password",
            )
            raise InvalidCredentialsError("Current password is incorrect")
        
        # Validate new password
        validate_password_strength(new_password)
        
        # Check password history
        password_history = await self._get_password_history(user_id, count=5)
        if not check_password_history(new_password, password_history):
            raise PasswordValidationError(
                "Password was used recently. Please choose a different password."
            )
        
        # Update password
        new_hash = hash_password(new_password)
        user.password_hash = new_hash
        user.last_password_change = datetime.utcnow()
        
        # Add to password history
        await self._add_password_history(user_id, new_hash)
        
        # Log password change
        await self._log_auth_event(
            event_type="password_changed",
            user_id=user_id,
            client_ip=client_ip,
            success=True,
        )
        
        await self.db.commit()
        
        logger.info("password.changed", user_id=str(user_id))
    
    async def _get_user_by_username_or_email(
        self,
        username: Optional[str] = None,
        email: Optional[str] = None
    ) -> Optional[User]:
        """Get user by username or email."""
        query = select(User)
        
        if username and email:
            query = query.where(
                (User.username == username.lower()) | (User.email == email.lower())
            )
        elif username:
            query = query.where(User.username == username.lower())
        elif email:
            query = query.where(User.email == email.lower())
        else:
            return None
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_user_primary_role(self, user_id: UUID) -> str:
        """Get user's primary role."""
        result = await self.db.execute(
            select(Role)
            .join(UserRole)
            .where(UserRole.user_id == user_id)
            .order_by(UserRole.created_at)
            .limit(1)
        )
        role = result.scalar_one_or_none()
        return role.name if role else "operator"
    
    async def _assign_role(
        self,
        user_id: UUID,
        role_name: str,
        assigned_by: Optional[UUID] = None
    ) -> None:
        """Assign role to user."""
        # Get or create role
        result = await self.db.execute(
            select(Role).where(Role.name == role_name)
        )
        role = result.scalar_one_or_none()
        
        if not role:
            # Create role from definition
            role_def = MANUFACTURING_ROLES.get(role_name)
            if role_def:
                role = Role(
                    name=role_def.name,
                    display_name=role_def.display_name,
                    description=role_def.description,
                    permissions=[p.value for p in role_def.permissions],
                    requires_mfa=role_def.requires_mfa,
                    max_session_hours=role_def.max_session_hours,
                )
                self.db.add(role)
                await self.db.flush()
        
        if role:
            user_role = UserRole(
                user_id=user_id,
                role_id=role.id,
                assigned_by=assigned_by,
            )
            self.db.add(user_role)
    
    async def _create_session(
        self,
        user_id: UUID,
        session_id: str,
        jti: str,
        client_ip: str,
        user_agent: str,
        expires_in_seconds: int
    ) -> UserSession:
        """Create user session record."""
        session = UserSession(
            user_id=user_id,
            session_id=session_id,
            jti=jti,
            client_ip=client_ip,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(seconds=expires_in_seconds),
        )
        self.db.add(session)
        return session
    
    async def _handle_failed_login(self, user: User, client_ip: str) -> None:
        """Handle failed login attempt with account lockout."""
        user.failed_login_attempts += 1
        user.last_failed_login = datetime.utcnow()
        
        if user.failed_login_attempts >= self.max_login_attempts:
            user.is_locked = True
            user.locked_until = datetime.utcnow() + timedelta(
                minutes=self.lockout_duration_minutes
            )
            
            await self._log_auth_event(
                event_type="account_locked",
                user_id=user.id,
                username=user.username,
                client_ip=client_ip,
                success=False,
                failure_reason="max_failed_attempts",
            )
        
        await self._log_auth_event(
            event_type="login_failed",
            user_id=user.id,
            username=user.username,
            client_ip=client_ip,
            success=False,
            failure_reason="invalid_password",
        )
        
        await self.db.commit()
    
    async def _log_auth_event(
        self,
        event_type: str,
        client_ip: str,
        success: bool,
        user_id: Optional[UUID] = None,
        username: Optional[str] = None,
        session_id: Optional[str] = None,
        failure_reason: Optional[str] = None,
    ) -> None:
        """Log authentication event."""
        event = AuthEvent(
            event_type=event_type,
            user_id=user_id,
            username=username,
            session_id=session_id,
            client_ip=client_ip,
            user_agent="",
            success=success,
            failure_reason=failure_reason,
        )
        self.db.add(event)
    
    async def _add_password_history(
        self,
        user_id: UUID,
        password_hash: str
    ) -> None:
        """Add password to history."""
        history = PasswordHistory(
            user_id=user_id,
            password_hash=password_hash,
        )
        self.db.add(history)
    
    async def _get_password_history(
        self,
        user_id: UUID,
        count: int = 5
    ) -> List[str]:
        """Get recent password hashes."""
        result = await self.db.execute(
            select(PasswordHistory.password_hash)
            .where(PasswordHistory.user_id == user_id)
            .order_by(PasswordHistory.changed_at.desc())
            .limit(count)
        )
        return [row[0] for row in result.all()]
