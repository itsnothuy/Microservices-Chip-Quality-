"""
Authentication and authorization module for the Chip Quality Platform.

This module provides comprehensive OAuth2/JWT authentication with RBAC,
FDA 21 CFR Part 11 compliance, and enterprise security features.

Exports:
    - Authentication handlers and dependencies
    - Password management utilities
    - Token management (JWT)
    - Permission and role management
    - Audit logging
    - MFA support
"""

from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    InvalidCredentialsError,
    TokenExpiredError,
    InvalidTokenError,
    InsufficientPermissionsError,
    AccountLockedError,
    MFARequiredError,
)

from .schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    LoginRequest,
    LoginResponse,
    TokenResponse,
    RefreshTokenRequest,
    PasswordChangeRequest,
    PasswordResetRequest,
)

from .password import (
    hash_password,
    verify_password,
    validate_password_strength,
    generate_random_password,
)

from .tokens import TokenManager, TokenData

from .handlers import AuthenticationHandler

from .dependencies import (
    get_current_user,
    get_current_active_user,
    require_permissions,
    require_role,
    require_verified_user,
    get_token_manager,
)

__all__ = [
    # Exceptions
    "AuthenticationError",
    "AuthorizationError",
    "InvalidCredentialsError",
    "TokenExpiredError",
    "InvalidTokenError",
    "InsufficientPermissionsError",
    "AccountLockedError",
    "MFARequiredError",
    # Schemas
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "LoginRequest",
    "LoginResponse",
    "TokenResponse",
    "RefreshTokenRequest",
    "PasswordChangeRequest",
    "PasswordResetRequest",
    # Password utilities
    "hash_password",
    "verify_password",
    "validate_password_strength",
    "generate_random_password",
    # Token management
    "TokenManager",
    "TokenData",
    # Handlers
    "AuthenticationHandler",
    # Dependencies
    "get_current_user",
    "get_current_active_user",
    "require_permissions",
    "require_role",
    "require_verified_user",
    "get_token_manager",
]
