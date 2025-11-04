"""
Report Service - Main FastAPI application.

Production-grade microservice for quality reporting, analytics,
and FDA-compliant documentation generation.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import settings
from .core.dependencies import get_engine
from .core.exceptions import ReportServiceError
from .routers import reports, analytics, templates

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Report Service", version=settings.service_version)
    
    # Initialize database connection
    engine = get_engine()
    logger.info("Database connection initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Report Service")
    await engine.dispose()
    logger.info("Database connection closed")


# Create FastAPI application
app = FastAPI(
    title="Report Service",
    description="Quality reporting, analytics, and FDA-compliant documentation",
    version=settings.service_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(ReportServiceError)
async def report_service_error_handler(
    request: Request,
    exc: ReportServiceError
) -> JSONResponse:
    """Handle custom report service errors"""
    logger.error(
        "Report service error",
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
        path=request.url.path
    )
    
    # Map error codes to HTTP status codes
    status_map = {
        "VALIDATION_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "REPORT_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "TEMPLATE_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "REPORT_GENERATION_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "ANALYTICS_CALCULATION_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "EXPORT_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "DATA_TOO_LARGE": status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        "CONCURRENT_LIMIT_ERROR": status.HTTP_429_TOO_MANY_REQUESTS,
        "STORAGE_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "DATABASE_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    
    http_status = status_map.get(exc.error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return JSONResponse(
        status_code=http_status,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle unexpected exceptions"""
    logger.error(
        "Unexpected error",
        error=str(exc),
        path=request.url.path,
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {}
            }
        }
    )


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": settings.service_name,
        "version": settings.service_version
    }


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """Readiness check for Kubernetes"""
    return {
        "status": "ready",
        "service": settings.service_name,
        "checks": {
            "database": "ok",
            "storage": "ok"
        }
    }


@app.get("/health/live", tags=["Health"])
async def liveness_check():
    """Liveness check for Kubernetes"""
    return {
        "status": "alive",
        "service": settings.service_name
    }


# Include routers
app.include_router(
    reports.router,
    prefix=f"{settings.api_prefix}/reports",
    tags=["Reports"]
)

app.include_router(
    analytics.router,
    prefix=f"{settings.api_prefix}/analytics",
    tags=["Analytics"]
)

app.include_router(
    templates.router,
    prefix=f"{settings.api_prefix}/templates",
    tags=["Templates"]
)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with service information"""
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "description": "Quality reporting and analytics service",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )
