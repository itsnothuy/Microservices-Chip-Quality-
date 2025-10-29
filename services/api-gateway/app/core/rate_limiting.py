"""Rate limiting with Redis and SlowAPI"""

import redis.asyncio as redis
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
import structlog

from app.core.config import Settings


logger = structlog.get_logger()
limiter: Limiter = None
redis_client: redis.Redis = None


def rate_limit_key_func(request: Request) -> str:
    """Generate rate limit key based on user or IP"""
    # Try to get user ID from JWT token
    authorization = request.headers.get("authorization")
    if authorization and authorization.startswith("Bearer "):
        try:
            # In a real implementation, you'd decode the JWT to get user ID
            # For now, use the token as identifier
            return f"user:{authorization[7:50]}"  # Use first part of token
        except Exception:
            pass
    
    # Fallback to IP address
    return f"ip:{get_remote_address(request)}"


async def setup_rate_limiting(settings: Settings) -> None:
    """Setup rate limiting with Redis backend"""
    global limiter, redis_client
    
    try:
        # Connect to Redis
        redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        
        # Test connection
        await redis_client.ping()
        logger.info("Connected to Redis for rate limiting")
        
        # Setup limiter
        limiter = Limiter(
            key_func=rate_limit_key_func,
            storage_uri=settings.redis_url,
            default_limits=[f"{settings.rate_limit_per_minute}/minute"]
        )
        
    except Exception as e:
        logger.warning(
            "Failed to connect to Redis, using in-memory rate limiting",
            error=str(e)
        )
        # Fallback to in-memory storage
        limiter = Limiter(
            key_func=rate_limit_key_func,
            default_limits=[f"{settings.rate_limit_per_minute}/minute"]
        )


def get_limiter() -> Limiter:
    """Get the configured rate limiter"""
    return limiter


async def close_redis():
    """Close Redis connection"""
    if redis_client:
        await redis_client.close()