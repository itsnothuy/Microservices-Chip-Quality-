"""
API Gateway for Chip Quality Platform

Provides unified entry point for all platform services with:
- Authentication and authorization
- Request routing and aggregation
- Rate limiting and caching
- Observability and monitoring
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import structlog

from app.core.config import get_settings
from app.core.auth import get_current_user
from app.core.logging import setup_logging
from app.core.observability import setup_observability
from app.core.rate_limiting import setup_rate_limiting
from app.routers import auth, inspections, artifacts, inference, reports, health
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.error_handling import ErrorHandlingMiddleware


settings = get_settings()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting API Gateway", version=app.version)
    
    # Setup observability
    setup_observability(settings)
    
    # Setup rate limiting
    await setup_rate_limiting(settings)
    
    logger.info("API Gateway startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down API Gateway")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    # Setup structured logging
    setup_logging(settings.log_level)
    
    app = FastAPI(
        title="Chip Quality Platform API Gateway",
        description=__doc__,
        version="0.1.0",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
        openapi_url="/openapi.json" if settings.environment != "production" else None,
        lifespan=lifespan,
    )
    
    # Security middleware
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=settings.allowed_hosts
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Custom middleware
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Include routers
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(auth.router, prefix="/auth", tags=["authentication"])
    app.include_router(
        inspections.router, 
        prefix="/api/v1/inspections", 
        tags=["inspections"],
        dependencies=[Depends(get_current_user)]
    )
    app.include_router(
        artifacts.router, 
        prefix="/api/v1/artifacts", 
        tags=["artifacts"],
        dependencies=[Depends(get_current_user)]
    )
    app.include_router(
        inference.router, 
        prefix="/api/v1/inference", 
        tags=["inference"],
        dependencies=[Depends(get_current_user)]
    )
    app.include_router(
        reports.router, 
        prefix="/api/v1/reports", 
        tags=["reports"],
        dependencies=[Depends(get_current_user)]
    )
    
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
        trace_id = trace.get_current_span().get_span_context().trace_id
        
        logger.error(
            "Unhandled exception",
            exc_info=exc,
            trace_id=hex(trace_id) if trace_id else None,
            path=request.url.path,
            method=request.method,
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "trace_id": hex(trace_id) if trace_id else None,
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
        port=8000,
        reload=True,
        log_config=None  # Use our structured logging
    )