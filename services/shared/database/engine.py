"""
Production-grade PostgreSQL/TimescaleDB engine setup

Features:
- Async SQLAlchemy 2.0+ with asyncpg driver
- Connection pooling with configurable parameters
- Health monitoring and reconnection logic
- Performance metrics collection
- Environment-specific configurations
"""

import os
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool, QueuePool
import structlog

logger = structlog.get_logger(__name__)

# Global engine instance
_engine: Optional[AsyncEngine] = None


def get_database_url() -> str:
    """Get database URL from environment variables"""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        # Build from individual components
        db_user = os.getenv("DB_USER", "chip_quality_user")
        db_password = os.getenv("DB_PASSWORD", "dev_password_123")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "chip_quality")
        
        database_url = (
            f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        )
    
    return database_url


def create_engine_with_config() -> AsyncEngine:
    """
    Create async SQLAlchemy engine with production-ready configuration
    
    Returns:
        AsyncEngine: Configured async database engine
    """
    database_url = get_database_url()
    environment = os.getenv("ENVIRONMENT", "development")
    
    # Connection pool configuration
    pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
    max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))
    pool_pre_ping = os.getenv("DB_POOL_PRE_PING", "true").lower() == "true"
    
    # Choose pool class based on environment
    pool_class = NullPool if environment == "test" else QueuePool
    
    logger.info(
        "creating_database_engine",
        database_url=database_url.split("@")[-1],  # Log without credentials
        environment=environment,
        pool_size=pool_size,
        max_overflow=max_overflow,
    )
    
    # Create engine with configuration
    engine = create_async_engine(
        database_url,
        echo=environment == "development",
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_recycle=pool_recycle,
        pool_pre_ping=pool_pre_ping,
        poolclass=pool_class,
        connect_args={
            "server_settings": {
                "application_name": "chip_quality_platform",
                "jit": "off",  # Disable JIT for better performance on small queries
            },
            "command_timeout": 60,
            "timeout": 30,
        },
    )
    
    return engine


def get_engine() -> AsyncEngine:
    """
    Get or create the global database engine instance
    
    Returns:
        AsyncEngine: The global async database engine
    """
    global _engine
    
    if _engine is None:
        _engine = create_engine_with_config()
    
    return _engine


async def dispose_engine() -> None:
    """Dispose of the global engine instance"""
    global _engine
    
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        logger.info("database_engine_disposed")


async def health_check() -> bool:
    """
    Check database connection health
    
    Returns:
        bool: True if database is accessible, False otherwise
    """
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        return False


# Create engine instance on module load
engine = get_engine()
