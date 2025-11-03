"""
Health Check API Endpoints

Provides FastAPI endpoints for health monitoring:
- Basic health check
- Readiness probe (for Kubernetes)
- Liveness probe (for Kubernetes)
- Detailed health report
- Component-specific checks
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime
import structlog

from services.shared.observability.health.checks import (
    HealthStatus,
    health_checker,
)

logger = structlog.get_logger()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str
    components: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, int]] = None
    message: Optional[str] = None


def create_health_router(
    service_name: str = "chip-quality-service",
    service_version: str = "0.1.0"
) -> APIRouter:
    """
    Create health check router with all endpoints.
    
    Args:
        service_name: Name of the service
        service_version: Version of the service
    
    Returns:
        Configured FastAPI router
    """
    router = APIRouter()
    
    @router.get("/", response_model=HealthResponse)
    async def health_check():
        """
        Basic health check endpoint.
        
        Returns simple health status without checking dependencies.
        Useful for quick availability checks.
        """
        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow().isoformat(),
            message=f"{service_name} v{service_version} is running"
        )
    
    @router.get("/live", response_model=HealthResponse)
    async def liveness_probe():
        """
        Kubernetes liveness probe endpoint.
        
        Returns:
            200 if service is alive
            503 if service should be restarted
        
        This endpoint should only check if the service process is running,
        not external dependencies.
        """
        return HealthResponse(
            status="ok",
            timestamp=datetime.utcnow().isoformat(),
            message=f"{service_name} is alive"
        )
    
    @router.get("/ready", response_model=HealthResponse)
    async def readiness_probe():
        """
        Kubernetes readiness probe endpoint.
        
        Returns:
            200 if service is ready to accept traffic
            503 if service is not ready (dependencies unavailable)
        
        This endpoint checks critical dependencies before marking
        the service as ready.
        """
        try:
            # Check all registered health checks
            results = await health_checker.check_all(parallel=True)
            overall_status = health_checker.get_overall_status()
            
            # Get critical component statuses
            critical_unhealthy = []
            for name, result in results.items():
                check = health_checker._checks.get(name)
                if check and check.critical and result.status == HealthStatus.UNHEALTHY:
                    critical_unhealthy.append(name)
            
            if overall_status == HealthStatus.UNHEALTHY:
                logger.warning(
                    "Readiness check failed",
                    critical_unhealthy=critical_unhealthy
                )
                raise HTTPException(
                    status_code=503,
                    detail={
                        "status": "not_ready",
                        "message": "Critical dependencies are unavailable",
                        "critical_unhealthy": critical_unhealthy
                    }
                )
            
            response_status = "ready" if overall_status == HealthStatus.HEALTHY else "degraded"
            
            return HealthResponse(
                status=response_status,
                timestamp=datetime.utcnow().isoformat(),
                components={
                    name: {
                        "status": result.status.value,
                        "message": result.message
                    }
                    for name, result in results.items()
                },
                message=f"{service_name} is {'ready' if response_status == 'ready' else 'degraded but accepting traffic'}"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Readiness check failed", error=str(e), exc_info=True)
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "error",
                    "message": f"Health check failed: {str(e)}"
                }
            )
    
    @router.get("/detailed", response_model=Dict[str, Any])
    async def detailed_health():
        """
        Detailed health report with all component information.
        
        Returns comprehensive health status including:
        - Overall system status
        - Individual component statuses
        - Performance metrics (latency)
        - Summary statistics
        """
        try:
            results = await health_checker.check_all(parallel=True)
            report = health_checker.get_health_report()
            
            # Add service metadata
            report["service"] = {
                "name": service_name,
                "version": service_version,
            }
            
            return report
            
        except Exception as e:
            logger.error("Detailed health check failed", error=str(e), exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": f"Health check failed: {str(e)}"
                }
            )
    
    @router.get("/component/{component_name}", response_model=Dict[str, Any])
    async def component_health(component_name: str):
        """
        Health check for a specific component.
        
        Args:
            component_name: Name of the component to check
        
        Returns:
            Detailed health status for the specified component
        """
        try:
            result = await health_checker.check_component(component_name)
            
            if result is None:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "status": "error",
                        "message": f"Component '{component_name}' not found"
                    }
                )
            
            return result.to_dict()
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Component health check failed",
                component=component_name,
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": f"Health check failed: {str(e)}"
                }
            )
    
    @router.get("/dependencies", response_model=Dict[str, Any])
    async def dependencies_health(
        critical_only: bool = Query(False, description="Only show critical dependencies")
    ):
        """
        Health status of all dependencies.
        
        Args:
            critical_only: If True, only return critical dependencies
        
        Returns:
            Health status of all (or critical) dependencies
        """
        try:
            results = await health_checker.check_all(parallel=True)
            
            # Filter by critical if requested
            if critical_only:
                results = {
                    name: result
                    for name, result in results.items()
                    if health_checker._checks[name].critical
                }
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "dependencies": {
                    name: result.to_dict()
                    for name, result in results.items()
                }
            }
            
        except Exception as e:
            logger.error("Dependencies health check failed", error=str(e), exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": f"Health check failed: {str(e)}"
                }
            )
    
    return router
