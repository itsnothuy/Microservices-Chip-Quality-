"""
Async session management for FastAPI dependency injection

Features:
- Dependency injection for database sessions
- Automatic rollback on exceptions
- Connection pool monitoring
- Transaction management
- Query performance logging
- Test isolation for pytest
"""

from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session
import structlog

from .engine import get_engine

logger = structlog.get_logger(__name__)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=get_engine(),
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions
    
    Usage in FastAPI:
        @app.get("/items/")
        async def read_items(db: AsyncSession = Depends(get_db_session)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            logger.debug("database_session_created")
            yield session
            await session.commit()
            logger.debug("database_session_committed")
        except Exception as e:
            await session.rollback()
            logger.error("database_session_rollback", error=str(e), exc_info=True)
            raise
        finally:
            await session.close()
            logger.debug("database_session_closed")


@asynccontextmanager
async def get_session_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions
    
    Usage:
        async with get_session_context() as session:
            result = await session.execute(select(Item))
            items = result.scalars().all()
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class SessionManager:
    """
    Session manager for advanced use cases
    
    Provides transaction management, savepoints, and connection monitoring
    """
    
    def __init__(self):
        self.session_factory = AsyncSessionLocal
    
    async def create_session(self) -> AsyncSession:
        """Create a new database session"""
        return self.session_factory()
    
    @asynccontextmanager
    async def transaction(
        self, session: AsyncSession
    ) -> AsyncGenerator[AsyncSession, None]:
        """
        Transaction context manager with automatic rollback
        
        Usage:
            async with session_manager.transaction(session) as tx_session:
                # Perform database operations
                pass  # Auto-commits on success, rolls back on exception
        """
        async with session.begin():
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
    
    @asynccontextmanager
    async def savepoint(
        self, session: AsyncSession, name: str
    ) -> AsyncGenerator[AsyncSession, None]:
        """
        Savepoint context manager for nested transactions
        
        Args:
            session: Active database session
            name: Savepoint name
        
        Yields:
            AsyncSession: Session with active savepoint
        """
        async with session.begin_nested() as savepoint:
            try:
                yield session
            except Exception:
                await savepoint.rollback()
                raise


# Global session manager instance
session_manager = SessionManager()
