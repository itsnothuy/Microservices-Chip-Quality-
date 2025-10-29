"""
Ingestion Service for Chip Quality Platform

Handles inspection requests, batch processing, and event publishing:
- Inspection lifecycle management
- Batch processing coordination
- Event-driven architecture integration
- Database operations with audit trails
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import structlog

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.observability import setup_observability
from app.core.database import init_database, close_database
from app.core.events import init_event_publisher, close_event_publisher
from app.routers import inspections, batches, health
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.error_handling import ErrorHandlingMiddleware
from app.middleware.auth import AuthMiddleware


settings = get_settings()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Ingestion Service", version=app.version)
    
    # Setup observability
    setup_observability(settings)
    
    # Initialize database
    await init_database(settings)
    
    # Initialize event publisher
    await init_event_publisher(settings)
    
    logger.info("Ingestion Service startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Ingestion Service")
    
    # Close event publisher
    await close_event_publisher()
    
    # Close database
    await close_database()


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    # Setup structured logging
    setup_logging(settings.log_level)
    
    app = FastAPI(
        title="Chip Quality Platform - Ingestion Service",
        description=__doc__,
        version="0.1.0",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
        openapi_url="/openapi.json" if settings.environment != "production" else None,
        lifespan=lifespan,
    )
    
    # Security middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Custom middleware
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(AuthMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Include routers
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(inspections.router, prefix="/api/v1/inspections", tags=["inspections"])
    app.include_router(batches.router, prefix="/api/v1/batches", tags=["batches"])
    
    # Metrics endpoint
    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        """Prometheus metrics endpoint"""
        return Response(
            generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler with structured logging"""
        logger.error(
            "Unhandled exception",
            exc_info=exc,
            path=request.url.path,
            method=request.method,
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    
    # Instrument with OpenTelemetry
    FastAPIInstrumentor.instrument_app(app)
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_config=None  # Use our structured logging
    )