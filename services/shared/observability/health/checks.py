"""
Comprehensive Health Check System

Provides health monitoring for:
- Service health (database, cache, message queue)
- Business health (quality thresholds, compliance)
- Dependency health (external services, ML models)
- System resource health (CPU, memory, disk)
"""

from typing import Dict, Any, Optional, Callable, Awaitable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import structlog

logger = structlog.get_logger()


class HealthStatus(str, Enum):
    """Health check status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    status: HealthStatus
    component: str
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = field(default_factory=dict)
    latency_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "status": self.status.value,
            "component": self.component,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "latency_ms": self.latency_ms,
        }


class ServiceHealthCheck:
    """Base class for service health checks."""
    
    def __init__(
        self,
        name: str,
        check_fn: Callable[[], Awaitable[HealthCheckResult]],
        timeout_seconds: float = 5.0,
        critical: bool = True,
    ):
        """
        Initialize service health check.
        
        Args:
            name: Name of the service/component
            check_fn: Async function that performs the health check
            timeout_seconds: Timeout for health check
            critical: Whether this check is critical for overall health
        """
        self.name = name
        self.check_fn = check_fn
        self.timeout_seconds = timeout_seconds
        self.critical = critical
    
    async def execute(self) -> HealthCheckResult:
        """
        Execute the health check with timeout.
        
        Returns:
            Health check result
        """
        start_time = datetime.utcnow()
        
        try:
            result = await asyncio.wait_for(
                self.check_fn(),
                timeout=self.timeout_seconds
            )
            
            # Calculate latency
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.latency_ms = latency
            
            return result
            
        except asyncio.TimeoutError:
            latency = self.timeout_seconds * 1000
            logger.warning(
                "Health check timeout",
                component=self.name,
                timeout_seconds=self.timeout_seconds
            )
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                component=self.name,
                message=f"Health check timed out after {self.timeout_seconds}s",
                latency_ms=latency,
            )
            
        except Exception as e:
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(
                "Health check failed",
                component=self.name,
                error=str(e),
                exc_info=True
            )
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                component=self.name,
                message=f"Health check failed: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
                latency_ms=latency,
            )


class HealthChecker:
    """
    Comprehensive health checker for all system components.
    
    Manages and executes health checks for:
    - Infrastructure services (database, cache, queue)
    - External dependencies (APIs, ML models)
    - Business health (quality metrics, compliance)
    - System resources (CPU, memory, disk)
    """
    
    def __init__(self):
        """Initialize health checker."""
        self._checks: Dict[str, ServiceHealthCheck] = {}
        self._last_check_time: Optional[datetime] = None
        self._last_results: Dict[str, HealthCheckResult] = {}
        logger.info("Health checker initialized")
    
    def register_check(self, check: ServiceHealthCheck) -> None:
        """
        Register a health check.
        
        Args:
            check: Service health check to register
        """
        self._checks[check.name] = check
        logger.debug("Health check registered", component=check.name)
    
    def unregister_check(self, name: str) -> None:
        """
        Unregister a health check.
        
        Args:
            name: Name of the check to unregister
        """
        if name in self._checks:
            del self._checks[name]
            logger.debug("Health check unregistered", component=name)
    
    async def check_all(self, parallel: bool = True) -> Dict[str, HealthCheckResult]:
        """
        Execute all registered health checks.
        
        Args:
            parallel: Whether to run checks in parallel (default: True)
        
        Returns:
            Dictionary of health check results by component name
        """
        if not self._checks:
            logger.warning("No health checks registered")
            return {}
        
        self._last_check_time = datetime.utcnow()
        
        if parallel:
            # Execute all checks in parallel
            results = await asyncio.gather(
                *[check.execute() for check in self._checks.values()],
                return_exceptions=True
            )
            
            # Map results to component names
            self._last_results = {
                check.name: result if isinstance(result, HealthCheckResult) else HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    component=check.name,
                    message=f"Check failed with exception: {str(result)}",
                )
                for check, result in zip(self._checks.values(), results)
            }
        else:
            # Execute checks sequentially
            self._last_results = {}
            for name, check in self._checks.items():
                result = await check.execute()
                self._last_results[name] = result
        
        return self._last_results
    
    async def check_component(self, name: str) -> Optional[HealthCheckResult]:
        """
        Execute health check for a specific component.
        
        Args:
            name: Name of the component to check
        
        Returns:
            Health check result or None if component not found
        """
        check = self._checks.get(name)
        if not check:
            logger.warning("Health check not found", component=name)
            return None
        
        result = await check.execute()
        self._last_results[name] = result
        return result
    
    def get_overall_status(self) -> HealthStatus:
        """
        Get overall system health status.
        
        Returns:
            Overall health status based on all checks
        
        Logic:
            - HEALTHY: All checks are healthy
            - DEGRADED: Some non-critical checks are unhealthy
            - UNHEALTHY: Any critical check is unhealthy
            - UNKNOWN: No checks have been executed
        """
        if not self._last_results:
            return HealthStatus.UNKNOWN
        
        critical_checks = {
            name: result
            for name, result in self._last_results.items()
            if self._checks[name].critical
        }
        
        # Check critical components first
        for result in critical_checks.values():
            if result.status == HealthStatus.UNHEALTHY:
                return HealthStatus.UNHEALTHY
        
        # Check all components
        all_healthy = all(
            result.status == HealthStatus.HEALTHY
            for result in self._last_results.values()
        )
        
        if all_healthy:
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.DEGRADED
    
    def get_health_report(self) -> Dict[str, Any]:
        """
        Get comprehensive health report.
        
        Returns:
            Dictionary containing overall status and component details
        """
        overall_status = self.get_overall_status()
        
        return {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "last_check": self._last_check_time.isoformat() if self._last_check_time else None,
            "components": {
                name: result.to_dict()
                for name, result in self._last_results.items()
            },
            "summary": {
                "total_checks": len(self._last_results),
                "healthy": sum(
                    1 for r in self._last_results.values()
                    if r.status == HealthStatus.HEALTHY
                ),
                "degraded": sum(
                    1 for r in self._last_results.values()
                    if r.status == HealthStatus.DEGRADED
                ),
                "unhealthy": sum(
                    1 for r in self._last_results.values()
                    if r.status == HealthStatus.UNHEALTHY
                ),
            }
        }


# Global health checker instance
health_checker = HealthChecker()
