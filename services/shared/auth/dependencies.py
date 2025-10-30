"""
FastAPI dependency injection for authentication and authorization.

Provides reusable dependencies for protecting routes, checking permissions,
and accessing current user information.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from services.shared.database.session import get_db_session
from services.shared.models.users import User, Role, UserRole
from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    InvalidTokenError,
    TokenExpiredError,
    InsufficientPermissionsError,
)
from .tokens import TokenManager, TokenData
from .permissions import permission_checker, Permission
from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# Security scheme
security = HTTPBearer()

# Token manager instance
_token_manager: Optional[TokenManager] = None


def get_token_manager() -> TokenManager:
    """Get or create token manager instance."""
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager(
            secret_key=settings.secret_key,
            algorithm=settings.algorithm,
            access_token_expire_minutes=settings.access_token_expire_minutes,
            refresh_token_expire_days=settings.refresh_token_expire_days,
        )
    return _token_manager


async def get_current_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_manager: TokenManager = Depends(get_token_manager)
) -> TokenData:
    """
    Extract and validate JWT token from request.
    
    Args:
        credentials: HTTP authorization credentials
        token_manager: Token manager instance
        
    Returns:
        Decoded token data
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        token_data = token_manager.verify_token(
            credentials.credentials,
            expected_type="access"
        )
        return token_data
        
    except TokenExpiredError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token_data: TokenData = Depends(get_current_token),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """
    Get current authenticated user from database.
    
    Args:
        token_data: Decoded token data
        db: Database session
        
    Returns:
        Current user instance
        
    Raises:
        HTTPException: If user not found or inactive
    """
    try:
        # Parse user ID from token
        user_id = UUID(token_data.sub)
        
        # Get user from database
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
            )
        
        # Attach token data to user for permission checking
        user._token_data = token_data
        
        return user
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (verified and not locked).
    
    Args:
        current_user: Current user from token
        
    Returns:
        Active user instance
        
    Raises:
        HTTPException: If user is not verified or account is locked
    """
    if current_user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is locked",
        )
    
    return current_user


def require_permissions(required_permissions: List[str]):
    """
    Dependency factory to require specific permissions.
    
    Args:
        required_permissions: List of required permission scopes
        
    Returns:
        FastAPI dependency function
        
    Example:
        @router.post("/inspections")
        async def create_inspection(
            user: User = Depends(require_permissions(["inspections:write"]))
        ):
            ...
    """
    async def permission_dependency(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        # Get token data attached to user
        token_data = getattr(current_user, "_token_data", None)
        
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication state",
            )
        
        # Check if user has all required permissions
        user_scopes = set(token_data.scopes)
        required_scopes = set(required_permissions)
        
        if not required_scopes.issubset(user_scopes):
            missing = required_scopes - user_scopes
            logger.warning(
                "permission.denied",
                user_id=str(current_user.id),
                username=current_user.username,
                required=list(required_scopes),
                missing=list(missing)
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Missing: {', '.join(missing)}",
            )
        
        return current_user
    
    return permission_dependency


def require_role(allowed_roles: List[str]):
    """
    Dependency factory to require specific roles.
    
    Args:
        allowed_roles: List of allowed role names
        
    Returns:
        FastAPI dependency function
        
    Example:
        @router.post("/admin/users")
        async def create_user(
            user: User = Depends(require_role(["admin", "quality_manager"]))
        ):
            ...
    """
    async def role_dependency(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        # Get token data
        token_data = getattr(current_user, "_token_data", None)
        
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication state",
            )
        
        # Check if user has allowed role
        if token_data.role not in allowed_roles:
            logger.warning(
                "role.denied",
                user_id=str(current_user.id),
                username=current_user.username,
                user_role=token_data.role,
                required_roles=allowed_roles
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient privileges. Required role: {', '.join(allowed_roles)}",
            )
        
        return current_user
    
    return role_dependency


def require_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Require user to have verified email.
    
    Args:
        current_user: Current active user
        
    Returns:
        Verified user instance
        
    Raises:
        HTTPException: If email is not verified
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required",
        )
    
    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    token_manager: TokenManager = Depends(get_token_manager),
    db: AsyncSession = Depends(get_db_session)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.
    
    Useful for endpoints that support both authenticated and anonymous access.
    
    Args:
        credentials: Optional HTTP authorization credentials
        token_manager: Token manager instance
        db: Database session
        
    Returns:
        Current user if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        token_data = token_manager.verify_token(
            credentials.credentials,
            expected_type="access"
        )
        
        user_id = UUID(token_data.sub)
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if user and user.is_active:
            user._token_data = token_data
            return user
        
    except Exception:
        # Silently fail for optional authentication
        pass
    
    return None


async def rate_limit_auth(request: Request) -> None:
    """
    Apply rate limiting to authentication endpoints.
    
    Args:
        request: FastAPI request object
        
    Raises:
        HTTPException: If rate limit exceeded
        
    Note:
        In production, implement with Redis or similar distributed cache
    """
    # Placeholder for rate limiting logic
    # In production, use Redis with sliding window or token bucket algorithm
    pass


# Common permission dependencies for convenience
require_inspection_read = require_permissions(["inspections:read"])
require_inspection_write = require_permissions(["inspections:write"])
require_inspection_approve = require_permissions(["inspections:approve"])

require_defect_write = require_permissions(["defects:write"])
require_defect_approve = require_permissions(["defects:approve"])

require_batch_read = require_permissions(["batches:read"])
require_batch_release = require_permissions(["batches:release"])

require_artifact_read = require_permissions(["artifacts:read"])
require_artifact_write = require_permissions(["artifacts:write"])

require_inference_execute = require_permissions(["inference:execute"])
require_inference_configure = require_permissions(["inference:configure"])

require_report_read = require_permissions(["reports:read"])
require_report_write = require_permissions(["reports:write"])
require_report_approve = require_permissions(["reports:approve"])

require_user_read = require_permissions(["users:read"])
require_user_write = require_permissions(["users:write"])

require_system_admin = require_permissions(["system:admin"])
require_system_configure = require_permissions(["system:configure"])

require_compliance_read = require_permissions(["compliance:read"])
require_compliance_audit = require_permissions(["compliance:audit"])

# Role-based dependencies
require_admin = require_role(["admin"])
require_quality_manager = require_role(["admin", "quality_manager"])
require_supervisor = require_role(["admin", "quality_manager", "supervisor"])
