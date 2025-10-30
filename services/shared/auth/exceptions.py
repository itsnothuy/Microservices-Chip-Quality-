"""
Authentication and authorization exceptions.

Custom exception hierarchy for auth-related errors with proper
HTTP status codes and security event logging support.
"""

from typing import Optional, Dict, Any


class AuthenticationError(Exception):
    """Base exception for authentication errors."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        status_code: int = 401,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class InvalidCredentialsError(AuthenticationError):
    """Invalid username or password."""
    
    def __init__(self, message: str = "Invalid username or password"):
        super().__init__(message=message, status_code=401)


class TokenExpiredError(AuthenticationError):
    """JWT token has expired."""
    
    def __init__(self, message: str = "Token has expired"):
        super().__init__(message=message, status_code=401)


class InvalidTokenError(AuthenticationError):
    """Invalid or malformed JWT token."""
    
    def __init__(self, message: str = "Invalid token"):
        super().__init__(message=message, status_code=401)


class AuthorizationError(Exception):
    """Base exception for authorization errors."""
    
    def __init__(
        self,
        message: str = "Authorization failed",
        status_code: int = 403,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class InsufficientPermissionsError(AuthorizationError):
    """User lacks required permissions for the operation."""
    
    def __init__(
        self,
        message: str = "Insufficient permissions",
        required_permissions: Optional[list] = None
    ):
        details = {"required_permissions": required_permissions} if required_permissions else {}
        super().__init__(message=message, status_code=403, details=details)


class AccountLockedError(AuthenticationError):
    """User account is locked due to security policy."""
    
    def __init__(
        self,
        message: str = "Account is locked",
        lockout_until: Optional[str] = None
    ):
        details = {"lockout_until": lockout_until} if lockout_until else {}
        super().__init__(message=message, status_code=403, details=details)


class MFARequiredError(AuthenticationError):
    """Multi-factor authentication is required."""
    
    def __init__(
        self,
        message: str = "MFA verification required",
        challenge_type: str = "totp",
        challenge_id: Optional[str] = None
    ):
        details = {
            "requires_mfa": True,
            "challenge_type": challenge_type,
            "challenge_id": challenge_id
        }
        super().__init__(message=message, status_code=401, details=details)


class PasswordValidationError(Exception):
    """Password does not meet security requirements."""
    
    def __init__(self, message: str, validation_errors: Optional[list] = None):
        self.message = message
        self.validation_errors = validation_errors or []
        super().__init__(self.message)


class SessionExpiredError(AuthenticationError):
    """User session has expired."""
    
    def __init__(self, message: str = "Session has expired"):
        super().__init__(message=message, status_code=401)


class DuplicateUserError(Exception):
    """User with this identifier already exists."""
    
    def __init__(self, message: str = "User already exists"):
        self.message = message
        super().__init__(self.message)


class UserNotFoundError(Exception):
    """User not found in the system."""
    
    def __init__(self, message: str = "User not found"):
        self.message = message
        super().__init__(self.message)


class RoleNotFoundError(Exception):
    """Role not found in the system."""
    
    def __init__(self, message: str = "Role not found"):
        self.message = message
        super().__init__(self.message)
