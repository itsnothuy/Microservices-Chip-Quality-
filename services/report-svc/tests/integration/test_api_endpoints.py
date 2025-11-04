"""
Integration tests for Report Service API.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from datetime import date

from app.main import app


@pytest.mark.asyncio
class TestHealthEndpoints:
    """Test health check endpoints"""
    
    async def test_health_check(self):
        """Test basic health check"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "report-service"
            assert "version" in data
    
    async def test_readiness_check(self):
        """Test readiness check"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health/ready")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ready"
            assert "checks" in data
    
    async def test_liveness_check(self):
        """Test liveness check"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health/live")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "alive"


@pytest.mark.asyncio
class TestRootEndpoint:
    """Test root endpoint"""
    
    async def test_root(self):
        """Test root endpoint"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/")
            
            assert response.status_code == 200
            data = response.json()
            assert data["service"] == "report-service"
            assert "version" in data
            assert data["docs"] == "/docs"


@pytest.mark.asyncio
class TestOpenAPISpec:
    """Test OpenAPI specification"""
    
    async def test_openapi_json(self):
        """Test OpenAPI JSON is accessible"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/openapi.json")
            
            assert response.status_code == 200
            spec = response.json()
            assert spec["info"]["title"] == "Report Service"
            assert "paths" in spec
            # Check report and analytics endpoints exist
            paths = list(spec["paths"].keys())
            assert any("/api/v1/reports" in p for p in paths)
            assert any("/api/v1/analytics" in p for p in paths)
