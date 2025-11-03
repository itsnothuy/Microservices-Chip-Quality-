"""
Unit tests for observability health checks module.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock

from services.shared.observability.health.checks import (
    HealthStatus,
    HealthCheckResult,
    ServiceHealthCheck,
    HealthChecker,
)


class TestHealthCheckResult:
    """Tests for HealthCheckResult."""
    
    def test_health_check_result_creation(self):
        """Test creating a health check result."""
        result = HealthCheckResult(
            status=HealthStatus.HEALTHY,
            component="test-component",
            message="Component is healthy",
            details={"version": "1.0.0"}
        )
        
        assert result.status == HealthStatus.HEALTHY
        assert result.component == "test-component"
        assert result.message == "Component is healthy"
        assert result.details["version"] == "1.0.0"
    
    def test_health_check_result_to_dict(self):
        """Test converting health check result to dictionary."""
        result = HealthCheckResult(
            status=HealthStatus.HEALTHY,
            component="test-component",
            message="Component is healthy",
            latency_ms=10.5
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["status"] == "healthy"
        assert result_dict["component"] == "test-component"
        assert result_dict["message"] == "Component is healthy"
        assert result_dict["latency_ms"] == 10.5


class TestServiceHealthCheck:
    """Tests for ServiceHealthCheck."""
    
    @pytest.mark.asyncio
    async def test_service_health_check_success(self):
        """Test successful health check execution."""
        async def mock_check():
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                component="test-service",
                message="Service is healthy"
            )
        
        check = ServiceHealthCheck(
            name="test-service",
            check_fn=mock_check,
            timeout_seconds=5.0,
            critical=True
        )
        
        result = await check.execute()
        
        assert result.status == HealthStatus.HEALTHY
        assert result.component == "test-service"
        assert result.latency_ms is not None
    
    @pytest.mark.asyncio
    async def test_service_health_check_timeout(self):
        """Test health check timeout handling."""
        async def slow_check():
            import asyncio
            await asyncio.sleep(10)
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                component="test-service",
                message="Service is healthy"
            )
        
        check = ServiceHealthCheck(
            name="test-service",
            check_fn=slow_check,
            timeout_seconds=0.1,
            critical=True
        )
        
        result = await check.execute()
        
        assert result.status == HealthStatus.UNHEALTHY
        assert "timed out" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_service_health_check_exception(self):
        """Test health check exception handling."""
        async def failing_check():
            raise Exception("Connection failed")
        
        check = ServiceHealthCheck(
            name="test-service",
            check_fn=failing_check,
            timeout_seconds=5.0,
            critical=True
        )
        
        result = await check.execute()
        
        assert result.status == HealthStatus.UNHEALTHY
        assert "Connection failed" in result.message


class TestHealthChecker:
    """Tests for HealthChecker."""
    
    def test_health_checker_initialization(self):
        """Test health checker initialization."""
        checker = HealthChecker()
        
        assert checker._checks == {}
        assert checker._last_results == {}
    
    def test_register_health_check(self):
        """Test registering a health check."""
        checker = HealthChecker()
        
        async def mock_check():
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                component="test",
                message="OK"
            )
        
        check = ServiceHealthCheck(
            name="test-service",
            check_fn=mock_check,
            timeout_seconds=5.0,
            critical=True
        )
        
        checker.register_check(check)
        
        assert "test-service" in checker._checks
    
    def test_unregister_health_check(self):
        """Test unregistering a health check."""
        checker = HealthChecker()
        
        async def mock_check():
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                component="test",
                message="OK"
            )
        
        check = ServiceHealthCheck(
            name="test-service",
            check_fn=mock_check,
            timeout_seconds=5.0,
            critical=True
        )
        
        checker.register_check(check)
        checker.unregister_check("test-service")
        
        assert "test-service" not in checker._checks
    
    @pytest.mark.asyncio
    async def test_check_all_parallel(self):
        """Test checking all health checks in parallel."""
        checker = HealthChecker()
        
        async def mock_check_1():
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                component="service-1",
                message="OK"
            )
        
        async def mock_check_2():
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                component="service-2",
                message="OK"
            )
        
        checker.register_check(ServiceHealthCheck(
            name="service-1",
            check_fn=mock_check_1,
            timeout_seconds=5.0,
            critical=True
        ))
        
        checker.register_check(ServiceHealthCheck(
            name="service-2",
            check_fn=mock_check_2,
            timeout_seconds=5.0,
            critical=False
        ))
        
        results = await checker.check_all(parallel=True)
        
        assert len(results) == 2
        assert "service-1" in results
        assert "service-2" in results
        assert results["service-1"].status == HealthStatus.HEALTHY
        assert results["service-2"].status == HealthStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_check_component(self):
        """Test checking a specific component."""
        checker = HealthChecker()
        
        async def mock_check():
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                component="service-1",
                message="OK"
            )
        
        checker.register_check(ServiceHealthCheck(
            name="service-1",
            check_fn=mock_check,
            timeout_seconds=5.0,
            critical=True
        ))
        
        result = await checker.check_component("service-1")
        
        assert result is not None
        assert result.status == HealthStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_get_overall_status_healthy(self):
        """Test getting overall status when all checks are healthy."""
        checker = HealthChecker()
        
        async def mock_check():
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                component="service",
                message="OK"
            )
        
        checker.register_check(ServiceHealthCheck(
            name="service-1",
            check_fn=mock_check,
            timeout_seconds=5.0,
            critical=True
        ))
        
        await checker.check_all()
        status = checker.get_overall_status()
        
        assert status == HealthStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_get_overall_status_unhealthy(self):
        """Test getting overall status when critical check fails."""
        checker = HealthChecker()
        
        async def healthy_check():
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                component="service-1",
                message="OK"
            )
        
        async def unhealthy_check():
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                component="service-2",
                message="FAILED"
            )
        
        checker.register_check(ServiceHealthCheck(
            name="service-1",
            check_fn=healthy_check,
            timeout_seconds=5.0,
            critical=False
        ))
        
        checker.register_check(ServiceHealthCheck(
            name="service-2",
            check_fn=unhealthy_check,
            timeout_seconds=5.0,
            critical=True
        ))
        
        await checker.check_all()
        status = checker.get_overall_status()
        
        assert status == HealthStatus.UNHEALTHY
    
    @pytest.mark.asyncio
    async def test_get_health_report(self):
        """Test getting comprehensive health report."""
        checker = HealthChecker()
        
        async def mock_check():
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                component="service",
                message="OK"
            )
        
        checker.register_check(ServiceHealthCheck(
            name="service-1",
            check_fn=mock_check,
            timeout_seconds=5.0,
            critical=True
        ))
        
        await checker.check_all()
        report = checker.get_health_report()
        
        assert "status" in report
        assert "timestamp" in report
        assert "components" in report
        assert "summary" in report
        assert report["summary"]["total_checks"] == 1
        assert report["summary"]["healthy"] == 1
