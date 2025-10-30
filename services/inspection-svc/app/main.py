"""
Inspection Service - Main FastAPI application.

Production-grade microservice for inspection workflow orchestration,
quality assessment, and defect management.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import structlog

from .core.config import settings
from .core.exceptions import InspectionServiceError
from .routers import inspections, defects, quality
from .core.dependencies import get_engine


logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Inspection Service", version=settings.service_version)
    
    # Initialize database connection
    engine = get_engine()
    logger.info("Database connection initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Inspection Service")
    await engine.dispose()
    logger.info("Database connection closed")


# Create FastAPI application
app = FastAPI(
    title="Inspection Service",
    description="Core business logic for quality inspection orchestration",
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
@app.exception_handler(InspectionServiceError)
async def inspection_service_error_handler(
    request: Request,
    exc: InspectionServiceError
) -> JSONResponse:
    """Handle custom inspection service errors"""
    logger.error(
        "Inspection service error",
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
        path=request.url.path
    )
    
    # Map error codes to HTTP status codes
    status_map = {
        "VALIDATION_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "INSPECTION_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "DEFECT_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "DUPLICATE_INSPECTION": status.HTTP_409_CONFLICT,
        "INVALID_STATUS_TRANSITION": status.HTTP_400_BAD_REQUEST,
        "ML_INFERENCE_ERROR": status.HTTP_503_SERVICE_UNAVAILABLE,
        "QUALITY_THRESHOLD_VIOLATION": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "RESOURCE_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "CONCURRENCY_ERROR": status.HTTP_409_CONFLICT,
        "CONFIGURATION_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "EXTERNAL_SERVICE_ERROR": status.HTTP_503_SERVICE_UNAVAILABLE,
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
    # In production, check database connectivity, ML service, etc.
    return {
        "status": "ready",
        "service": settings.service_name,
        "checks": {
            "database": "ok",
            "ml_service": "ok"
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
    inspections.router,
    prefix=f"{settings.api_prefix}/inspections",
    tags=["Inspections"]
)

app.include_router(
    defects.router,
    prefix=f"{settings.api_prefix}/defects",
    tags=["Defects"]
)

app.include_router(
    quality.router,
    prefix=f"{settings.api_prefix}/quality",
    tags=["Quality"]
)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with service information"""
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "description": "Inspection service for quality control orchestration",
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
