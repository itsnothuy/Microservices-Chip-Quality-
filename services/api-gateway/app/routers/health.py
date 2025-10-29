"""Health check endpoints"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
import structlog

from app.core.config import get_settings
from app.core.http_client import (
    get_ingestion_client, get_inference_client, get_metadata_client,
    get_artifact_client, get_report_client
)


logger = structlog.get_logger()
router = APIRouter()
settings = get_settings()


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: str
    services: dict[str, str] = {}


@router.get("/", response_model=HealthResponse)
async def health_check():
    """Basic health check"""
    from datetime import datetime
    
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/ready", response_model=HealthResponse)
async def readiness_check():
    """Readiness check with upstream service validation"""
    from datetime import datetime
    
    services = {}
    overall_status = "healthy"
    
    # Check upstream services
    service_checks = [
        ("ingestion", settings.ingestion_service_url, get_ingestion_client),
        ("inference", settings.inference_service_url, get_inference_client),
        ("metadata", settings.metadata_service_url, get_metadata_client),
        ("artifact", settings.artifact_service_url, get_artifact_client),
        ("report", settings.report_service_url, get_report_client),
    ]
    
    for service_name, service_url, client_factory in service_checks:
        try:
            async with client_factory() as client:
                response = await client.get("/health", timeout=5.0)
                if response.status_code == 200:
                    services[service_name] = "healthy"
                else:
                    services[service_name] = f"unhealthy (status: {response.status_code})"
                    overall_status = "degraded"
        except Exception as e:
            services[service_name] = f"unreachable ({str(e)})"
            overall_status = "degraded"
            
            logger.warning(
                "Service health check failed",
                service=service_name,
                url=service_url,
                error=str(e)
            )
    
    return HealthResponse(
        status=overall_status,
        version="0.1.0",
        timestamp=datetime.utcnow().isoformat(),
        services=services,
    )


@router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"status": "ok"}