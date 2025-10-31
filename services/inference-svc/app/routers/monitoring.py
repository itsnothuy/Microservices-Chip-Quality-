"""
Performance monitoring API endpoints.

Performance Monitoring:
GET    /health            - Service health check
GET    /metrics           - Model performance metrics
GET    /models/{name}/health - Model-specific health status
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
import structlog

from ..core.dependencies import (
    get_performance_monitor,
    get_model_service,
    get_triton_client
)
from ..services.performance_monitor import PerformanceMonitor
from ..services.model_service import ModelService
from ..services.triton_client import TritonClient


logger = structlog.get_logger()
router = APIRouter()


@router.get("/health")
async def service_health(
    triton_client: TritonClient = Depends(get_triton_client)
):
    """
    Service health check.
    
    Returns overall health status of the inference service.
    """
    logger.debug("Checking service health")
    
    try:
        triton_healthy = await triton_client.health_check()
        
        return {
            "status": "healthy" if triton_healthy else "degraded",
            "service": "inference-service",
            "triton_connected": triton_healthy,
            "components": {
                "triton": "healthy" if triton_healthy else "unhealthy",
                "api": "healthy"
            }
        }
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/models/{model_name}/health")
async def model_health(
    model_name: str,
    model_version: Optional[str] = Query(None, description="Model version"),
    performance_monitor: PerformanceMonitor = Depends(get_performance_monitor)
):
    """
    Model-specific health status.
    
    Returns health metrics and status for a specific model.
    """
    logger.info("Checking model health", model_name=model_name)
    
    try:
        health_status = await performance_monitor.get_model_health_status(
            model_name=model_name,
            model_version=model_version or ""
        )
        
        return health_status
        
    except Exception as e:
        logger.error(
            "Failed to get model health",
            model_name=model_name,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get model health: {str(e)}"
        )


@router.get("/models/{model_name}/metrics")
async def model_metrics(
    model_name: str,
    model_version: Optional[str] = Query(None, description="Model version"),
    period_minutes: int = Query(60, description="Time period in minutes"),
    performance_monitor: PerformanceMonitor = Depends(get_performance_monitor)
):
    """
    Model performance metrics.
    
    Returns detailed performance metrics for a model.
    """
    logger.info(
        "Getting model metrics",
        model_name=model_name,
        period_minutes=period_minutes
    )
    
    try:
        metrics = await performance_monitor.get_metrics(
            model_name=model_name,
            model_version=model_version or "",
            period_minutes=period_minutes
        )
        
        return metrics
        
    except Exception as e:
        logger.error(
            "Failed to get model metrics",
            model_name=model_name,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get metrics: {str(e)}"
        )


@router.get("/models/{model_name}/anomalies")
async def model_anomalies(
    model_name: str,
    model_version: Optional[str] = Query(None, description="Model version"),
    performance_monitor: PerformanceMonitor = Depends(get_performance_monitor)
):
    """
    Detect model performance anomalies.
    
    Returns list of detected performance anomalies.
    """
    logger.info("Detecting model anomalies", model_name=model_name)
    
    try:
        anomalies = await performance_monitor.detect_anomalies(
            model_name=model_name,
            model_version=model_version or ""
        )
        
        return {
            "model_name": model_name,
            "model_version": model_version or "latest",
            "anomaly_count": len(anomalies),
            "anomalies": anomalies
        }
        
    except Exception as e:
        logger.error(
            "Failed to detect anomalies",
            model_name=model_name,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to detect anomalies: {str(e)}"
        )


@router.post("/models/{model_name}/metrics/clear")
async def clear_model_metrics(
    model_name: str,
    model_version: Optional[str] = Query(None, description="Model version"),
    performance_monitor: PerformanceMonitor = Depends(get_performance_monitor)
):
    """
    Clear metrics for a model.
    
    Resets all stored metrics for the specified model.
    """
    logger.info("Clearing model metrics", model_name=model_name)
    
    try:
        await performance_monitor.clear_metrics(
            model_name=model_name,
            model_version=model_version or ""
        )
        
        return {
            "status": "success",
            "message": f"Metrics cleared for model {model_name}"
        }
        
    except Exception as e:
        logger.error(
            "Failed to clear metrics",
            model_name=model_name,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear metrics: {str(e)}"
        )
