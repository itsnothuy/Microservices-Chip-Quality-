"""
Dependency Health Checks

Provides health check implementations for various dependencies:
- PostgreSQL database
- Redis cache
- Kafka message broker
- MinIO object storage
- NVIDIA Triton inference server
- External APIs
"""

from typing import Optional
import asyncio
from datetime import datetime
import structlog

from services.shared.observability.health.checks import (
    HealthCheckResult,
    HealthStatus,
    ServiceHealthCheck,
)

logger = structlog.get_logger()


async def check_database_health(
    db_url: str,
    timeout_seconds: float = 5.0
) -> HealthCheckResult:
    """
    Check PostgreSQL database health.
    
    Args:
        db_url: Database connection URL
        timeout_seconds: Query timeout
    
    Returns:
        Health check result
    """
    try:
        # Import here to avoid circular dependencies
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        
        engine = create_async_engine(db_url, pool_pre_ping=True)
        
        async with engine.connect() as conn:
            # Simple query to verify connectivity
            result = await conn.execute(text("SELECT 1"))
            await result.fetchone()
            
            # Get database metrics
            version_result = await conn.execute(text("SELECT version()"))
            version = (await version_result.fetchone())[0]
            
            # Get connection pool info
            pool_size = engine.pool.size()
            pool_checked_out = engine.pool.checkedout()
            
        await engine.dispose()
        
        return HealthCheckResult(
            status=HealthStatus.HEALTHY,
            component="database",
            message="Database is healthy and responsive",
            details={
                "database_version": version.split()[1] if version else "unknown",
                "pool_size": pool_size,
                "pool_checked_out": pool_checked_out,
            }
        )
        
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            component="database",
            message=f"Database health check failed: {str(e)}",
            details={"error": str(e), "error_type": type(e).__name__}
        )


async def check_redis_health(
    redis_url: str,
    timeout_seconds: float = 5.0
) -> HealthCheckResult:
    """
    Check Redis cache health.
    
    Args:
        redis_url: Redis connection URL
        timeout_seconds: Operation timeout
    
    Returns:
        Health check result
    """
    try:
        import redis.asyncio as aioredis
        
        redis_client = aioredis.from_url(
            redis_url,
            decode_responses=True,
            socket_timeout=timeout_seconds
        )
        
        # Ping Redis
        await redis_client.ping()
        
        # Get Redis info
        info = await redis_client.info()
        
        await redis_client.close()
        
        return HealthCheckResult(
            status=HealthStatus.HEALTHY,
            component="redis",
            message="Redis is healthy and responsive",
            details={
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "uptime_days": info.get("uptime_in_days"),
            }
        )
        
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        return HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            component="redis",
            message=f"Redis health check failed: {str(e)}",
            details={"error": str(e), "error_type": type(e).__name__}
        )


async def check_kafka_health(
    bootstrap_servers: str,
    timeout_seconds: float = 10.0
) -> HealthCheckResult:
    """
    Check Kafka message broker health.
    
    Args:
        bootstrap_servers: Kafka bootstrap servers
        timeout_seconds: Connection timeout
    
    Returns:
        Health check result
    """
    try:
        from aiokafka import AIOKafkaClient
        
        client = AIOKafkaClient(
            bootstrap_servers=bootstrap_servers,
            request_timeout_ms=int(timeout_seconds * 1000)
        )
        
        await client.bootstrap()
        
        # Get cluster metadata
        cluster = client.cluster
        
        broker_count = len(cluster.brokers())
        topics = cluster.topics()
        
        await client.close()
        
        return HealthCheckResult(
            status=HealthStatus.HEALTHY,
            component="kafka",
            message="Kafka is healthy and responsive",
            details={
                "broker_count": broker_count,
                "topic_count": len(topics),
                "controller_id": cluster.controller.nodeId if cluster.controller else None,
            }
        )
        
    except Exception as e:
        logger.error("Kafka health check failed", error=str(e))
        return HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            component="kafka",
            message=f"Kafka health check failed: {str(e)}",
            details={"error": str(e), "error_type": type(e).__name__}
        )


async def check_minio_health(
    endpoint: str,
    access_key: str,
    secret_key: str,
    timeout_seconds: float = 5.0
) -> HealthCheckResult:
    """
    Check MinIO object storage health.
    
    Args:
        endpoint: MinIO endpoint URL
        access_key: MinIO access key
        secret_key: MinIO secret key
        timeout_seconds: Request timeout
    
    Returns:
        Health check result
    """
    try:
        from minio import Minio
        from urllib3 import Timeout
        
        # Remove http:// or https:// from endpoint
        endpoint_clean = endpoint.replace("http://", "").replace("https://", "")
        
        client = Minio(
            endpoint_clean,
            access_key=access_key,
            secret_key=secret_key,
            secure=False,  # Use True in production with HTTPS
            http_client=None  # Could add custom timeout here
        )
        
        # List buckets to verify connectivity
        buckets = client.list_buckets()
        
        return HealthCheckResult(
            status=HealthStatus.HEALTHY,
            component="minio",
            message="MinIO is healthy and responsive",
            details={
                "bucket_count": len(buckets),
                "buckets": [b.name for b in buckets],
            }
        )
        
    except Exception as e:
        logger.error("MinIO health check failed", error=str(e))
        return HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            component="minio",
            message=f"MinIO health check failed: {str(e)}",
            details={"error": str(e), "error_type": type(e).__name__}
        )


async def check_triton_health(
    triton_url: str,
    timeout_seconds: float = 5.0
) -> HealthCheckResult:
    """
    Check NVIDIA Triton inference server health.
    
    Args:
        triton_url: Triton server URL (gRPC endpoint)
        timeout_seconds: Request timeout
    
    Returns:
        Health check result
    """
    try:
        import tritonclient.grpc as grpcclient
        
        # Parse URL to get host and port
        # Expected format: triton-server:8001 or http://triton-server:8001
        url = triton_url.replace("http://", "").replace("https://", "")
        
        client = grpcclient.InferenceServerClient(
            url=url,
            verbose=False
        )
        
        # Check if server is live
        if not client.is_server_live():
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                component="triton",
                message="Triton server is not live",
            )
        
        # Check if server is ready
        if not client.is_server_ready():
            return HealthCheckResult(
                status=HealthStatus.DEGRADED,
                component="triton",
                message="Triton server is live but not ready",
            )
        
        # Get server metadata
        metadata = client.get_server_metadata()
        
        # Get model repository info
        models = client.get_model_repository_index()
        
        return HealthCheckResult(
            status=HealthStatus.HEALTHY,
            component="triton",
            message="Triton inference server is healthy",
            details={
                "server_name": metadata.name,
                "server_version": metadata.version,
                "model_count": len(models.models) if hasattr(models, 'models') else 0,
            }
        )
        
    except Exception as e:
        logger.error("Triton health check failed", error=str(e))
        return HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            component="triton",
            message=f"Triton health check failed: {str(e)}",
            details={"error": str(e), "error_type": type(e).__name__}
        )


async def check_external_service_health(
    service_name: str,
    health_url: str,
    timeout_seconds: float = 5.0
) -> HealthCheckResult:
    """
    Check external service health via HTTP endpoint.
    
    Args:
        service_name: Name of the service
        health_url: Health check endpoint URL
        timeout_seconds: Request timeout
    
    Returns:
        Health check result
    """
    try:
        import httpx
        
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.get(health_url)
            
            if response.status_code == 200:
                status = HealthStatus.HEALTHY
                message = f"{service_name} is healthy"
            elif response.status_code in [503, 504]:
                status = HealthStatus.UNHEALTHY
                message = f"{service_name} is unhealthy (status: {response.status_code})"
            else:
                status = HealthStatus.DEGRADED
                message = f"{service_name} returned unexpected status: {response.status_code}"
            
            # Try to parse JSON response
            try:
                details = response.json()
            except Exception:
                details = {"status_code": response.status_code}
            
            return HealthCheckResult(
                status=status,
                component=service_name,
                message=message,
                details=details
            )
            
    except Exception as e:
        logger.error(
            "External service health check failed",
            service=service_name,
            error=str(e)
        )
        return HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            component=service_name,
            message=f"{service_name} health check failed: {str(e)}",
            details={"error": str(e), "error_type": type(e).__name__}
        )


def create_database_check(db_url: str) -> ServiceHealthCheck:
    """Create database health check."""
    return ServiceHealthCheck(
        name="database",
        check_fn=lambda: check_database_health(db_url),
        timeout_seconds=5.0,
        critical=True,
    )


def create_redis_check(redis_url: str) -> ServiceHealthCheck:
    """Create Redis health check."""
    return ServiceHealthCheck(
        name="redis",
        check_fn=lambda: check_redis_health(redis_url),
        timeout_seconds=5.0,
        critical=False,  # Non-critical, system can degrade gracefully
    )


def create_kafka_check(bootstrap_servers: str) -> ServiceHealthCheck:
    """Create Kafka health check."""
    return ServiceHealthCheck(
        name="kafka",
        check_fn=lambda: check_kafka_health(bootstrap_servers),
        timeout_seconds=10.0,
        critical=True,
    )


def create_minio_check(
    endpoint: str,
    access_key: str,
    secret_key: str
) -> ServiceHealthCheck:
    """Create MinIO health check."""
    return ServiceHealthCheck(
        name="minio",
        check_fn=lambda: check_minio_health(endpoint, access_key, secret_key),
        timeout_seconds=5.0,
        critical=True,
    )


def create_triton_check(triton_url: str) -> ServiceHealthCheck:
    """Create Triton health check."""
    return ServiceHealthCheck(
        name="triton",
        check_fn=lambda: check_triton_health(triton_url),
        timeout_seconds=5.0,
        critical=True,
    )


def create_external_service_check(
    service_name: str,
    health_url: str,
    critical: bool = False
) -> ServiceHealthCheck:
    """Create external service health check."""
    return ServiceHealthCheck(
        name=service_name,
        check_fn=lambda: check_external_service_health(service_name, health_url),
        timeout_seconds=5.0,
        critical=critical,
    )
