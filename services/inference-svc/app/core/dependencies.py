"""
FastAPI dependencies for inference service.

Dependency injection for database, cache, and service instances.
"""

from typing import AsyncGenerator
import structlog
from redis import asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from .config import settings


logger = structlog.get_logger()


# Database engine and session maker
engine = create_async_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=settings.debug,
    future=True
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session.
    
    Yields:
        AsyncSession: Database session
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error("Database session error", error=str(e))
            await session.rollback()
            raise
        finally:
            await session.close()


# Redis connection pool
redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """
    Get Redis client.
    
    Returns:
        Redis: Redis client instance
    """
    global redis_client
    if redis_client is None:
        redis_client = await aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
    return redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


# Service dependencies
from ..services.triton_client import TritonClient
from ..services.inference_service import InferenceService
from ..services.model_service import ModelService
from ..services.preprocessing import PreprocessingService
from ..services.postprocessing import PostprocessingService
from ..services.performance_monitor import PerformanceMonitor


_triton_client: TritonClient | None = None
_inference_service: InferenceService | None = None
_model_service: ModelService | None = None
_preprocessing_service: PreprocessingService | None = None
_postprocessing_service: PostprocessingService | None = None
_performance_monitor: PerformanceMonitor | None = None


async def get_triton_client() -> TritonClient:
    """Get Triton client instance."""
    global _triton_client
    if _triton_client is None:
        _triton_client = TritonClient(
            server_url=settings.triton_server_url,
            http_url=settings.triton_http_url,
            timeout=settings.triton_timeout,
            max_retries=settings.triton_max_retries
        )
    return _triton_client


async def get_preprocessing_service() -> PreprocessingService:
    """Get preprocessing service instance."""
    global _preprocessing_service
    if _preprocessing_service is None:
        _preprocessing_service = PreprocessingService()
    return _preprocessing_service


async def get_postprocessing_service() -> PostprocessingService:
    """Get postprocessing service instance."""
    global _postprocessing_service
    if _postprocessing_service is None:
        _postprocessing_service = PostprocessingService()
    return _postprocessing_service


async def get_performance_monitor() -> PerformanceMonitor:
    """Get performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        redis = await get_redis()
        _performance_monitor = PerformanceMonitor(redis)
    return _performance_monitor


async def get_model_service() -> ModelService:
    """Get model service instance."""
    global _model_service
    if _model_service is None:
        triton_client = await get_triton_client()
        redis = await get_redis()
        _model_service = ModelService(triton_client, redis)
    return _model_service


async def get_inference_service() -> InferenceService:
    """Get inference service instance."""
    global _inference_service
    if _inference_service is None:
        triton_client = await get_triton_client()
        preprocessing = await get_preprocessing_service()
        postprocessing = await get_postprocessing_service()
        model_service = await get_model_service()
        performance_monitor = await get_performance_monitor()
        _inference_service = InferenceService(
            triton_client=triton_client,
            preprocessing_service=preprocessing,
            postprocessing_service=postprocessing,
            model_service=model_service,
            performance_monitor=performance_monitor
        )
    return _inference_service


async def cleanup_services() -> None:
    """Cleanup all service instances."""
    global _triton_client, _inference_service, _model_service
    global _preprocessing_service, _postprocessing_service, _performance_monitor
    
    if _triton_client:
        await _triton_client.close()
        _triton_client = None
    
    await close_redis()
    
    _inference_service = None
    _model_service = None
    _preprocessing_service = None
    _postprocessing_service = None
    _performance_monitor = None
