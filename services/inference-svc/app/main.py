"""
Inference Service - FastAPI Application.

ML inference service providing NVIDIA Triton integration
for real-time defect detection.
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.core.config import settings
from app.core.dependencies import cleanup_services, get_triton_client
from app.routers import inference, models, monitoring


# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown logic.
    """
    # Startup
    logger.info(
        "Starting Inference Service",
        environment=settings.environment,
        triton_url=settings.triton_server_url
    )
    
    # Initialize Triton connection
    try:
        triton_client = await get_triton_client()
        await triton_client.connect()
        logger.info("Triton client connected successfully")
    except Exception as e:
        logger.error("Failed to connect to Triton server", error=str(e))
    
    yield
    
    # Shutdown
    logger.info("Shutting down Inference Service")
    await cleanup_services()


# Create FastAPI application
app = FastAPI(
    title="Inference Service",
    description="ML Inference Pipeline with NVIDIA Triton for defect detection",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    inference.router,
    prefix=f"{settings.api_v1_prefix}/inference",
    tags=["inference"]
)

app.include_router(
    models.router,
    prefix=f"{settings.api_v1_prefix}/models",
    tags=["models"]
)

app.include_router(
    monitoring.router,
    prefix=f"{settings.api_v1_prefix}/monitoring",
    tags=["monitoring"]
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        triton_client = await get_triton_client()
        triton_healthy = await triton_client.health_check()
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        triton_healthy = False
    
    return {
        "status": "healthy" if triton_healthy else "degraded",
        "service": "inference-service",
        "version": "0.1.0",
        "triton_connected": triton_healthy
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    try:
        triton_client = await get_triton_client()
        is_ready = triton_client.is_connected
    except Exception:
        is_ready = False
    
    if is_ready:
        return {"status": "ready"}
    else:
        return {"status": "not_ready"}, 503


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "inference-service",
        "version": "0.1.0",
        "description": "ML Inference Pipeline with NVIDIA Triton",
        "docs_url": "/docs",
        "health_url": "/health",
        "ready_url": "/ready"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
