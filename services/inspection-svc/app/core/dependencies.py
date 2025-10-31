"""FastAPI dependencies for dependency injection"""

from typing import AsyncGenerator

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from .config import settings
from .exceptions import ConfigurationError

logger = structlog.get_logger()


# Database engine and session factory
_engine = None
_async_session_maker = None


def get_engine():
    """Get or create database engine"""
    global _engine
    
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.db_echo,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            poolclass=NullPool if "sqlite" in settings.database_url else None,
        )
    
    return _engine


def get_session_maker():
    """Get or create session maker"""
    global _async_session_maker
    
    if _async_session_maker is None:
        engine = get_engine()
        _async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    
    return _async_session_maker


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session"""
    session_maker = get_session_maker()
    
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("Database session error", error=str(e), exc_info=True)
            raise
        finally:
            await session.close()


async def get_settings():
    """Dependency for getting application settings"""
    return settings


class ServiceDependencies:
    """Container for service dependencies"""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    @classmethod
    async def create(cls, db_session: AsyncSession) -> "ServiceDependencies":
        """Create service dependencies"""
        return cls(db_session)


async def get_service_deps(
    db_session: AsyncSession = None
) -> ServiceDependencies:
    """Get service dependencies"""
    if db_session is None:
        raise ConfigurationError("Database session is required")
    
    return await ServiceDependencies.create(db_session)
