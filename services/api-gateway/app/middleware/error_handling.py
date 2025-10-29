"""Error handling middleware with structured logging"""

import time
from typing import Callable

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from opentelemetry import trace
import structlog

from app.core.observability import REQUEST_COUNT, REQUEST_DURATION


logger = structlog.get_logger()


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling and request logging middleware"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        request_id = getattr(request.state, 'request_id', None)
        
        # Get trace context
        span = trace.get_current_span()
        trace_id = None
        if span:
            trace_context = span.get_span_context()
            if trace_context.trace_id:
                trace_id = hex(trace_context.trace_id)
        
        # Log request start
        logger.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            user_agent=request.headers.get("user-agent"),
            request_id=request_id,
            trace_id=trace_id,
        )
        
        try:
            response = await call_next(request)
            
            # Calculate duration
            process_time = time.time() - start_time
            
            # Record metrics
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code
            ).inc()
            
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(process_time)
            
            # Log successful response
            logger.info(
                "Request completed",
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                duration=process_time,
                request_id=request_id,
                trace_id=trace_id,
            )
            
            # Add timing header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except HTTPException as e:
            # Handle HTTP exceptions
            process_time = time.time() - start_time
            
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=e.status_code
            ).inc()
            
            logger.warning(
                "HTTP exception",
                method=request.method,
                url=str(request.url),
                status_code=e.status_code,
                detail=e.detail,
                duration=process_time,
                request_id=request_id,
                trace_id=trace_id,
            )
            
            # Return structured error response
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": e.detail,
                    "status_code": e.status_code,
                    "request_id": request_id,
                    "trace_id": trace_id,
                    "timestamp": time.time(),
                },
                headers={"X-Process-Time": str(process_time)}
            )
            
        except Exception as e:
            # Handle unexpected exceptions
            process_time = time.time() - start_time
            
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=500
            ).inc()
            
            logger.error(
                "Unhandled exception",
                method=request.method,
                url=str(request.url),
                error=str(e),
                duration=process_time,
                request_id=request_id,
                trace_id=trace_id,
                exc_info=True,
            )
            
            # Return generic error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "status_code": 500,
                    "request_id": request_id,
                    "trace_id": trace_id,
                    "timestamp": time.time(),
                },
                headers={"X-Process-Time": str(process_time)}
            )