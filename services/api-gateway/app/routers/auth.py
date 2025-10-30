"""Authentication endpoints"""

from datetime import timedelta
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.auth import (
    verify_password, get_password_hash, create_access_token, 
    create_refresh_token, verify_token, get_current_user, User
)
from app.core.config import get_settings
from app.core.rate_limiting import get_limiter
from services.shared.database.session import get_db_session
from services.shared.auth.dependencies import (
    get_current_user as get_auth_user,
    get_token_manager,
    require_verified_user,
)
from services.shared.auth.handlers import AuthenticationHandler
from services.shared.auth.schemas import (
    LoginRequest,
    LoginResponse,
    TokenResponse,
    RefreshTokenRequest,
    UserResponse,
    PasswordChangeRequest,
)
from services.shared.auth.tokens import TokenManager
from services.shared.models.users import User as DBUser


logger = structlog.get_logger()
router = APIRouter()
settings = get_settings()
limiter = get_limiter()


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """User response model"""
    id: str
    email: str
    username: str
    is_active: bool
    scopes: list[str]


class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str


class RefreshRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, login_data: LoginRequest):
    """Authenticate user and return tokens"""
    
    # In a real implementation, you would:
    # 1. Query user from database
    # 2. Verify password hash
    # 3. Check if user is active
    
    # For demo purposes, we'll use hardcoded users
    demo_users = {
        "admin": {
            "id": "user_001",
            "password_hash": get_password_hash("admin123"),
            "email": "admin@example.com",
            "is_active": True,
            "scopes": ["admin:access", "inspections:read", "inspections:write", 
                      "artifacts:read", "artifacts:write", "inference:access", "reports:read"]
        },
        "operator": {
            "id": "user_002", 
            "password_hash": get_password_hash("operator123"),
            "email": "operator@example.com",
            "is_active": True,
            "scopes": ["inspections:read", "inspections:write", "artifacts:read", "inference:access"]
        },
        "viewer": {
            "id": "user_003",
            "password_hash": get_password_hash("viewer123"),
            "email": "viewer@example.com", 
            "is_active": True,
            "scopes": ["inspections:read", "artifacts:read", "reports:read"]
        }
    }
    
    user_data = demo_users.get(login_data.username)
    if not user_data or not verify_password(login_data.password, user_data["password_hash"]):
        logger.warning(
            "Failed login attempt",
            username=login_data.username,
            ip=request.client.host if request.client else None
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    if not user_data["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    
    # Create tokens
    token_data = {
        "sub": user_data["id"],
        "username": login_data.username,
        "email": user_data["email"],
        "scopes": user_data["scopes"]
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": user_data["id"]})
    
    logger.info(
        "User logged in successfully",
        user_id=user_data["id"],
        username=login_data.username,
        scopes=user_data["scopes"]
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")
async def refresh_token(request: Request, refresh_data: RefreshRequest):
    """Refresh access token using refresh token"""
    
    try:
        token_payload = verify_token(refresh_data.refresh_token)
        
        if token_payload.type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # In a real implementation, you would:
        # 1. Check if refresh token is still valid in database
        # 2. Fetch current user data
        # 3. Check if user is still active
        
        # For demo, we'll create new tokens with basic data
        token_data = {
            "sub": token_payload.sub,
            "scopes": token_payload.scopes
        }
        
        access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token({"sub": token_payload.sub})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.access_token_expire_minutes * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        is_active=current_user.is_active,
        scopes=current_user.scopes
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user (invalidate tokens)"""
    
    # In a real implementation, you would:
    # 1. Add tokens to blacklist in Redis/database
    # 2. Update user's last_logout timestamp
    
    logger.info(
        "User logged out",
        user_id=current_user.id,
        username=current_user.username
    )
    
    return {"message": "Successfully logged out"}