"""
Password hashing and validation utilities.

Provides secure password hashing using bcrypt with configurable rounds,
password strength validation, and password history management.
"""

import secrets
import string
from typing import List, Optional
from passlib.context import CryptContext
import re

from .exceptions import PasswordValidationError


# Configure password hashing context
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Configurable rounds for bcrypt
)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string
        
    Example:
        >>> hashed = hash_password("MySecurePass123!")
        >>> verify_password("MySecurePass123!", hashed)
        True
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Previously hashed password
        
    Returns:
        True if password matches, False otherwise
        
    Example:
        >>> hashed = hash_password("MySecurePass123!")
        >>> verify_password("MySecurePass123!", hashed)
        True
        >>> verify_password("WrongPassword", hashed)
        False
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def validate_password_strength(
    password: str,
    min_length: int = 8,
    require_uppercase: bool = True,
    require_lowercase: bool = True,
    require_digits: bool = True,
    require_special: bool = True,
    forbidden_passwords: Optional[List[str]] = None
) -> tuple[bool, List[str]]:
    """
    Validate password strength against security requirements.
    
    Args:
        password: Password to validate
        min_length: Minimum password length
        require_uppercase: Require at least one uppercase letter
        require_lowercase: Require at least one lowercase letter
        require_digits: Require at least one digit
        require_special: Require at least one special character
        forbidden_passwords: List of forbidden passwords (common passwords)
        
    Returns:
        Tuple of (is_valid, list_of_errors)
        
    Raises:
        PasswordValidationError: If password doesn't meet requirements
        
    Example:
        >>> is_valid, errors = validate_password_strength("Weak123")
        >>> print(is_valid)
        False
        >>> print(errors)
        ['Password must contain at least one special character']
    """
    errors = []
    
    # Check length
    if len(password) < min_length:
        errors.append(f"Password must be at least {min_length} characters long")
    
    # Check for uppercase letters
    if require_uppercase and not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")
    
    # Check for lowercase letters
    if require_lowercase and not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter")
    
    # Check for digits
    if require_digits and not re.search(r"\d", password):
        errors.append("Password must contain at least one number")
    
    # Check for special characters
    if require_special and not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\;'/`~]", password):
        errors.append("Password must contain at least one special character")
    
    # Check against forbidden passwords
    if forbidden_passwords and password.lower() in [p.lower() for p in forbidden_passwords]:
        errors.append("This password is too common and not allowed")
    
    # Check for sequential characters (e.g., "123456", "abcdef")
    if re.search(r"(012|123|234|345|456|567|678|789|890|abc|bcd|cde|def|efg|fgh)", password.lower()):
        errors.append("Password contains sequential characters")
    
    # Check for repeated characters (e.g., "aaa", "111")
    if re.search(r"(.)\1{2,}", password):
        errors.append("Password contains too many repeated characters")
    
    is_valid = len(errors) == 0
    
    if not is_valid:
        raise PasswordValidationError(
            "Password does not meet security requirements",
            validation_errors=errors
        )
    
    return is_valid, errors


def generate_random_password(
    length: int = 16,
    include_uppercase: bool = True,
    include_lowercase: bool = True,
    include_digits: bool = True,
    include_special: bool = True
) -> str:
    """
    Generate a cryptographically secure random password.
    
    Args:
        length: Password length
        include_uppercase: Include uppercase letters
        include_lowercase: Include lowercase letters
        include_digits: Include digits
        include_special: Include special characters
        
    Returns:
        Randomly generated password
        
    Example:
        >>> password = generate_random_password(12)
        >>> len(password)
        12
        >>> is_valid, _ = validate_password_strength(password)
        >>> is_valid
        True
    """
    characters = ""
    
    if include_lowercase:
        characters += string.ascii_lowercase
    if include_uppercase:
        characters += string.ascii_uppercase
    if include_digits:
        characters += string.digits
    if include_special:
        characters += "!@#$%^&*()_-+=[]{}|:;<>,.?"
    
    if not characters:
        raise ValueError("At least one character set must be enabled")
    
    # Generate password ensuring at least one character from each required set
    password_chars = []
    
    if include_lowercase:
        password_chars.append(secrets.choice(string.ascii_lowercase))
    if include_uppercase:
        password_chars.append(secrets.choice(string.ascii_uppercase))
    if include_digits:
        password_chars.append(secrets.choice(string.digits))
    if include_special:
        password_chars.append(secrets.choice("!@#$%^&*()_-+=[]{}|:;<>,.?"))
    
    # Fill remaining length
    remaining_length = length - len(password_chars)
    for _ in range(remaining_length):
        password_chars.append(secrets.choice(characters))
    
    # Shuffle to avoid predictable patterns
    secrets.SystemRandom().shuffle(password_chars)
    
    return "".join(password_chars)


def check_password_history(
    new_password: str,
    password_history: List[str],
    history_count: int = 5
) -> bool:
    """
    Check if password was used recently (for password history enforcement).
    
    Args:
        new_password: New password to check
        password_history: List of previous password hashes
        history_count: Number of previous passwords to check
        
    Returns:
        True if password is not in history, False if it was used recently
        
    Example:
        >>> history = [hash_password("OldPass1!"), hash_password("OldPass2!")]
        >>> check_password_history("NewPass123!", history)
        True
        >>> check_password_history("OldPass1!", history)
        False
    """
    # Check only the most recent passwords based on history_count
    recent_history = password_history[-history_count:] if len(password_history) > history_count else password_history
    
    for old_hash in recent_history:
        if verify_password(new_password, old_hash):
            return False
    
    return True


# Common weak passwords to block
COMMON_WEAK_PASSWORDS = [
    "password", "password123", "12345678", "qwerty", "abc123",
    "monkey", "1234567", "letmein", "trustno1", "dragon",
    "baseball", "111111", "iloveyou", "master", "sunshine",
    "ashley", "bailey", "passw0rd", "shadow", "123123",
    "654321", "superman", "qazwsx", "michael", "football",
]


def is_password_compromised(password: str) -> bool:
    """
    Check if password is in list of commonly compromised passwords.
    
    Args:
        password: Password to check
        
    Returns:
        True if password is compromised, False otherwise
        
    Note:
        This is a simplified check against common passwords.
        For production, integrate with HaveIBeenPwned API or similar service.
    """
    return password.lower() in COMMON_WEAK_PASSWORDS
