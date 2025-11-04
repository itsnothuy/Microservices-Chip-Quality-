"""
FastAPI dependencies for Report Service.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import structlog

from .config import settings

logger = structlog.get_logger()

# Database engine (singleton)
_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """Get or create the async database engine"""
    global _engine
    
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_pool_timeout,
            pool_recycle=settings.database_pool_recycle,
            echo=settings.environment == "development",
        )
        logger.info(
            "Database engine created",
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow
        )
    
    return _engine


# Session factory - lazy initialization
_async_session_factory = None


def get_async_session_factory():
    """Get or create the async session factory"""
    global _async_session_factory
    
    if _async_session_factory is None:
        _async_session_factory = sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    
    return _async_session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session"""
    factory = get_async_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
