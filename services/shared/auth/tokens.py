"""
JWT token management with enhanced security features.

Provides JWT token generation, validation, refresh, and revocation
with support for different token types and security policies.
"""

import secrets
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import jwt
from pydantic import BaseModel

from .exceptions import TokenExpiredError, InvalidTokenError


class TokenData(BaseModel):
    """Decoded token payload data."""
    
    sub: str  # Subject (user ID)
    username: str
    email: str
    role: str
    scopes: List[str]
    exp: datetime
    iat: datetime
    jti: str  # JWT ID for revocation
    token_type: str  # 'access' or 'refresh'
    session_id: Optional[str] = None


class TokenManager:
    """
    Manages JWT token lifecycle including generation, validation, and revocation.
    
    Features:
    - RS256 signing for distributed systems
    - Token blacklisting for revocation
    - Refresh token rotation
    - Session tracking
    """
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7
    ):
        """
        Initialize token manager.
        
        Args:
            secret_key: Secret key for JWT signing
            algorithm: JWT signing algorithm (HS256 or RS256)
            access_token_expire_minutes: Access token expiry time
            refresh_token_expire_days: Refresh token expiry time
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.blacklisted_tokens: set = set()  # In production, use Redis
    
    def create_access_token(
        self,
        user_id: str,
        username: str,
        email: str,
        role: str,
        scopes: List[str],
        session_id: Optional[str] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token.
        
        Args:
            user_id: Unique user identifier
            username: Username
            email: User email
            role: User role
            scopes: List of permission scopes
            session_id: Optional session identifier
            expires_delta: Custom expiration time
            
        Returns:
            Encoded JWT access token
        """
        now = datetime.utcnow()
        
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=self.access_token_expire_minutes)
        
        jti = secrets.token_urlsafe(32)
        
        payload = {
            "sub": user_id,
            "username": username,
            "email": email,
            "role": role,
            "scopes": scopes,
            "exp": expire,
            "iat": now,
            "nbf": now,  # Not before
            "jti": jti,
            "token_type": "access",
            "session_id": session_id or f"sess_{secrets.token_urlsafe(16)}"
        }
        
        encoded_jwt = jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.algorithm
        )
        
        return encoded_jwt
    
    def create_refresh_token(
        self,
        user_id: str,
        session_id: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT refresh token.
        
        Args:
            user_id: Unique user identifier
            session_id: Session identifier
            expires_delta: Custom expiration time
            
        Returns:
            Encoded JWT refresh token
        """
        now = datetime.utcnow()
        
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(days=self.refresh_token_expire_days)
        
        jti = secrets.token_urlsafe(32)
        
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": now,
            "jti": jti,
            "token_type": "refresh",
            "session_id": session_id
        }
        
        encoded_jwt = jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.algorithm
        )
        
        return encoded_jwt
    
    def verify_token(
        self,
        token: str,
        expected_type: str = "access"
    ) -> TokenData:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token string
            expected_type: Expected token type ('access' or 'refresh')
            
        Returns:
            Decoded token data
            
        Raises:
            TokenExpiredError: If token has expired
            InvalidTokenError: If token is invalid or revoked
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Check if token is blacklisted
            jti = payload.get("jti")
            if jti and jti in self.blacklisted_tokens:
                raise InvalidTokenError("Token has been revoked")
            
            # Verify token type
            token_type = payload.get("token_type", "access")
            if token_type != expected_type:
                raise InvalidTokenError(f"Expected {expected_type} token, got {token_type}")
            
            # Convert timestamps to datetime
            exp = datetime.fromtimestamp(payload["exp"])
            iat = datetime.fromtimestamp(payload["iat"])
            
            # For access tokens, include full user data
            if token_type == "access":
                return TokenData(
                    sub=payload["sub"],
                    username=payload.get("username", ""),
                    email=payload.get("email", ""),
                    role=payload.get("role", ""),
                    scopes=payload.get("scopes", []),
                    exp=exp,
                    iat=iat,
                    jti=jti,
                    token_type=token_type,
                    session_id=payload.get("session_id")
                )
            else:
                # For refresh tokens, minimal data
                return TokenData(
                    sub=payload["sub"],
                    username="",
                    email="",
                    role="",
                    scopes=[],
                    exp=exp,
                    iat=iat,
                    jti=jti,
                    token_type=token_type,
                    session_id=payload.get("session_id")
                )
            
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"Invalid token: {str(e)}")
        except Exception as e:
            raise InvalidTokenError(f"Token validation failed: {str(e)}")
    
    def revoke_token(self, jti: str) -> None:
        """
        Revoke a token by adding its JTI to blacklist.
        
        Args:
            jti: JWT ID to revoke
            
        Note:
            In production, use Redis with expiration for blacklist storage
        """
        self.blacklisted_tokens.add(jti)
    
    def is_token_revoked(self, jti: str) -> bool:
        """
        Check if token is revoked.
        
        Args:
            jti: JWT ID to check
            
        Returns:
            True if token is revoked, False otherwise
        """
        return jti in self.blacklisted_tokens
    
    def create_token_pair(
        self,
        user_id: str,
        username: str,
        email: str,
        role: str,
        scopes: List[str]
    ) -> Dict[str, Any]:
        """
        Create access and refresh token pair.
        
        Args:
            user_id: Unique user identifier
            username: Username
            email: User email
            role: User role
            scopes: List of permission scopes
            
        Returns:
            Dictionary with access_token, refresh_token, and metadata
        """
        session_id = f"sess_{secrets.token_urlsafe(16)}"
        
        access_token = self.create_access_token(
            user_id=user_id,
            username=username,
            email=email,
            role=role,
            scopes=scopes,
            session_id=session_id
        )
        
        refresh_token = self.create_refresh_token(
            user_id=user_id,
            session_id=session_id
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60,
            "session_id": session_id
        }
    
    def refresh_access_token(
        self,
        refresh_token: str,
        user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create new access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            user_data: Current user data (username, email, role, scopes)
            
        Returns:
            New token pair with rotated refresh token
            
        Raises:
            InvalidTokenError: If refresh token is invalid
        """
        # Verify refresh token
        token_data = self.verify_token(refresh_token, expected_type="refresh")
        
        # Create new token pair
        new_tokens = self.create_token_pair(
            user_id=token_data.sub,
            username=user_data["username"],
            email=user_data["email"],
            role=user_data["role"],
            scopes=user_data["scopes"]
        )
        
        # Revoke old refresh token (token rotation)
        self.revoke_token(token_data.jti)
        
        return new_tokens


def create_password_reset_token(email: str, secret_key: str, expires_minutes: int = 30) -> str:
    """
    Create a password reset token.
    
    Args:
        email: User email address
        secret_key: Secret key for signing
        expires_minutes: Token expiration time
        
    Returns:
        Encoded password reset token
    """
    now = datetime.utcnow()
    expire = now + timedelta(minutes=expires_minutes)
    
    payload = {
        "sub": email,
        "exp": expire,
        "iat": now,
        "jti": secrets.token_urlsafe(16),
        "token_type": "password_reset"
    }
    
    return jwt.encode(payload, secret_key, algorithm="HS256")


def verify_password_reset_token(token: str, secret_key: str) -> str:
    """
    Verify password reset token and extract email.
    
    Args:
        token: Password reset token
        secret_key: Secret key for verification
        
    Returns:
        Email address from token
        
    Raises:
        InvalidTokenError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        if payload.get("token_type") != "password_reset":
            raise InvalidTokenError("Invalid token type")
        
        return payload["sub"]
    
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Password reset token has expired")
    except jwt.InvalidTokenError:
        raise InvalidTokenError("Invalid password reset token")
