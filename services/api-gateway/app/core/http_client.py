"""HTTP client utilities for upstream services"""

import asyncio
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

import httpx
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
import structlog

from app.core.config import get_settings
from app.core.observability import UPSTREAM_DURATION, UPSTREAM_ERRORS


settings = get_settings()
logger = structlog.get_logger()


class ServiceClient:
    """HTTP client for upstream services with observability"""
    
    def __init__(self, base_url: str, service_name: str):
        self.base_url = base_url.rstrip('/')
        self.service_name = service_name
        self._client: Optional[httpx.AsyncClient] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(settings.upstream_timeout),
            headers={
                "User-Agent": f"api-gateway/{settings.otel_service_version}",
                "Accept": "application/json",
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._client:
            await self._client.aclose()
            
    async def request(
        self,
        method: str,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """Make HTTP request with observability"""
        
        with UPSTREAM_DURATION.labels(
            service=self.service_name,
            endpoint=endpoint
        ).time():
            try:
                response = await self._client.request(
                    method=method,
                    url=endpoint,
                    headers=headers,
                    **kwargs
                )
                
                logger.info(
                    "Upstream request completed",
                    service=self.service_name,
                    method=method,
                    endpoint=endpoint,
                    status_code=response.status_code,
                    duration=response.elapsed.total_seconds() if response.elapsed else None
                )
                
                return response
                
            except httpx.TimeoutException as e:
                UPSTREAM_ERRORS.labels(
                    service=self.service_name,
                    error_type="timeout"
                ).inc()
                
                logger.error(
                    "Upstream request timeout",
                    service=self.service_name,
                    endpoint=endpoint,
                    error=str(e)
                )
                raise
                
            except httpx.ConnectError as e:
                UPSTREAM_ERRORS.labels(
                    service=self.service_name,
                    error_type="connection"
                ).inc()
                
                logger.error(
                    "Upstream connection error",
                    service=self.service_name,
                    endpoint=endpoint,
                    error=str(e)
                )
                raise
                
            except Exception as e:
                UPSTREAM_ERRORS.labels(
                    service=self.service_name,
                    error_type="unknown"
                ).inc()
                
                logger.error(
                    "Upstream request error",
                    service=self.service_name,
                    endpoint=endpoint,
                    error=str(e)
                )
                raise
    
    async def get(self, endpoint: str, **kwargs) -> httpx.Response:
        """GET request"""
        return await self.request("GET", endpoint, **kwargs)
    
    async def post(self, endpoint: str, **kwargs) -> httpx.Response:
        """POST request"""
        return await self.request("POST", endpoint, **kwargs)
    
    async def put(self, endpoint: str, **kwargs) -> httpx.Response:
        """PUT request"""
        return await self.request("PUT", endpoint, **kwargs)
    
    async def patch(self, endpoint: str, **kwargs) -> httpx.Response:
        """PATCH request"""
        return await self.request("PATCH", endpoint, **kwargs)
    
    async def delete(self, endpoint: str, **kwargs) -> httpx.Response:
        """DELETE request"""
        return await self.request("DELETE", endpoint, **kwargs)


@asynccontextmanager
async def get_service_client(service_name: str, base_url: str):
    """Get service client context manager"""
    async with ServiceClient(base_url, service_name) as client:
        yield client


# Service client factories
async def get_ingestion_client():
    """Get ingestion service client"""
    async with get_service_client("ingestion", settings.ingestion_service_url) as client:
        yield client


async def get_inference_client():
    """Get inference service client"""
    async with get_service_client("inference", settings.inference_service_url) as client:
        yield client


async def get_metadata_client():
    """Get metadata service client"""
    async with get_service_client("metadata", settings.metadata_service_url) as client:
        yield client


async def get_artifact_client():
    """Get artifact service client"""
    async with get_service_client("artifact", settings.artifact_service_url) as client:
        yield client


async def get_report_client():
    """Get report service client"""
    async with get_service_client("report", settings.report_service_url) as client:
        yield client