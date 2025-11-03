"""
Artifact Service - Main FastAPI application.

Production-grade microservice for artifact and file management with MinIO integration.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import settings
from .core.dependencies import get_engine
from .core.exceptions import ArtifactServiceError
from .routers import artifacts

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Artifact Service", version=settings.service_version)
    
    # Initialize database connection
    engine = get_engine()
    logger.info("Database connection initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Artifact Service")
    await engine.dispose()
    logger.info("Database connection closed")


# Create FastAPI application
app = FastAPI(
    title="Artifact Service",
    description="File and artifact management service with MinIO object storage",
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
@app.exception_handler(ArtifactServiceError)
async def artifact_service_error_handler(
    request: Request,
    exc: ArtifactServiceError
) -> JSONResponse:
    """Handle custom artifact service errors"""
    logger.error(
        "Artifact service error",
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
        path=request.url.path
    )
    
    # Map error codes to HTTP status codes
    status_map = {
        "ARTIFACT_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "FILE_UPLOAD_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "FILE_VALIDATION_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "STORAGE_ERROR": status.HTTP_503_SERVICE_UNAVAILABLE,
        "FILE_TOO_LARGE": status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        "INVALID_FILE_TYPE": status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        "CHECKSUM_MISMATCH": status.HTTP_422_UNPROCESSABLE_ENTITY,
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
    # In production, check database connectivity, MinIO, etc.
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
    artifacts.router,
    prefix=f"{settings.api_prefix}/artifacts",
    tags=["Artifacts"]
)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with service information"""
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "description": "Artifact management service for quality control platform",
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
