"""
Pydantic schemas for authentication and user management.

These schemas define the API contracts for authentication endpoints,
user management, and related operations.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class TokenResponse(BaseModel):
    """OAuth2 token response."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiry in seconds")
    scope: Optional[str] = Field(None, description="Granted scopes")


class LoginRequest(BaseModel):
    """User login credentials."""
    
    username: str = Field(..., min_length=3, max_length=50, description="Username or email")
    password: str = Field(..., min_length=8, description="User password")
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format."""
        if not v.strip():
            raise ValueError("Username cannot be empty")
        return v.strip().lower()


class LoginResponse(BaseModel):
    """Successful login response."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"


class RefreshTokenRequest(BaseModel):
    """Token refresh request."""
    
    refresh_token: str = Field(..., description="Valid refresh token")


class UserCreate(BaseModel):
    """User registration schema."""
    
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    full_name: Optional[str] = Field(None, max_length=200, description="Full name")
    role: str = Field(default="operator", description="User role")
    department: Optional[str] = Field(None, max_length=100, description="Department")
    employee_id: Optional[str] = Field(None, max_length=50, description="Employee ID")
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format."""
        if not re.match(r"^[a-z0-9_-]+$", v):
            raise ValueError("Username must contain only lowercase letters, numbers, underscores, and hyphens")
        return v.lower()
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserUpdate(BaseModel):
    """User profile update schema."""
    
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=200)
    department: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """User information response."""
    
    id: UUID
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    department: Optional[str] = None
    employee_id: Optional[str] = None
    is_active: bool
    is_verified: bool
    mfa_enabled: bool
    scopes: List[str]
    created_at: datetime
    last_login: Optional[datetime] = None
    
    model_config = {
        "from_attributes": True
    }


class PasswordChangeRequest(BaseModel):
    """Password change request."""
    
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class PasswordResetRequest(BaseModel):
    """Password reset request."""
    
    email: EmailStr = Field(..., description="User email address")


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation."""
    
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class MFASetupResponse(BaseModel):
    """MFA setup information."""
    
    secret: str = Field(..., description="TOTP secret key")
    qr_code: str = Field(..., description="QR code data URL")
    backup_codes: List[str] = Field(..., description="Backup recovery codes")


class MFAVerifyRequest(BaseModel):
    """MFA verification request."""
    
    code: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP code")


class SessionResponse(BaseModel):
    """Active session information."""
    
    session_id: str
    user_id: UUID
    client_ip: str
    user_agent: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime


class PermissionResponse(BaseModel):
    """User permissions response."""
    
    user_id: UUID
    role: str
    permissions: List[str]
    scopes: List[str]


class RoleResponse(BaseModel):
    """Role information."""
    
    id: UUID
    name: str
    display_name: str
    description: Optional[str] = None
    permissions: List[str]
    created_at: datetime
