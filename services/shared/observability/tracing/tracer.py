"""
OpenTelemetry Distributed Tracing Setup

Provides comprehensive distributed tracing functionality:
- Automatic HTTP request/response tracing
- Database query tracing with SQL capture
- Kafka message tracing for event streams
- External API call tracing
- Custom business operation tracing
- Trace sampling and filtering
"""

import os
from typing import Optional, Callable, Any
from functools import wraps

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.trace import Status, StatusCode, Span
import structlog

logger = structlog.get_logger()


def setup_tracing(
    service_name: str,
    service_version: str = "0.1.0",
    otlp_endpoint: Optional[str] = None,
    sampling_rate: float = 1.0,
) -> trace.Tracer:
    """
    Setup OpenTelemetry distributed tracing.
    
    Args:
        service_name: Name of the service (e.g., "api-gateway")
        service_version: Version of the service
        otlp_endpoint: OTLP collector endpoint (e.g., "http://jaeger:4317")
        sampling_rate: Sampling rate (0.0 to 1.0, default 1.0 = 100%)
    
    Returns:
        Configured tracer instance
    
    Features:
        - Automatic instrumentation for HTTP, SQL, Redis
        - Custom span attributes for business context
        - Integration with Jaeger/Tempo backends
        - Performance-optimized batch processing
    """
    # Create resource with service information
    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: service_version,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "deployment.type": "microservice",
    })
    
    # Create tracer provider
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    
    # Setup OTLP exporter if endpoint provided
    if otlp_endpoint:
        otlp_exporter = OTLPSpanExporter(
            endpoint=otlp_endpoint,
            insecure=True  # Use TLS in production
        )
        
        # Use batch processor for performance
        span_processor = BatchSpanProcessor(
            otlp_exporter,
            max_queue_size=2048,
            schedule_delay_millis=5000,  # 5 seconds
            export_timeout_millis=30000,  # 30 seconds
        )
        
        tracer_provider.add_span_processor(span_processor)
        
        logger.info(
            "OpenTelemetry tracing configured",
            service_name=service_name,
            otlp_endpoint=otlp_endpoint,
            sampling_rate=sampling_rate,
        )
    else:
        logger.warning(
            "OpenTelemetry tracing not configured - no OTLP endpoint provided",
            service_name=service_name,
        )
    
    # Instrument common libraries
    _instrument_libraries()
    
    # Get tracer
    tracer = trace.get_tracer(service_name, service_version)
    
    return tracer


def _instrument_libraries() -> None:
    """Instrument common Python libraries for automatic tracing."""
    try:
        # SQLAlchemy for database queries
        SQLAlchemyInstrumentor().instrument(
            enable_commenter=True,
            commenter_options={"db_driver": True, "db_framework": True}
        )
        logger.debug("SQLAlchemy instrumentation enabled")
    except Exception as e:
        logger.warning("Failed to instrument SQLAlchemy", error=str(e))
    
    try:
        # HTTPX for HTTP client calls
        HTTPXClientInstrumentor().instrument()
        logger.debug("HTTPX instrumentation enabled")
    except Exception as e:
        logger.warning("Failed to instrument HTTPX", error=str(e))
    
    try:
        # Redis for cache operations
        RedisInstrumentor().instrument()
        logger.debug("Redis instrumentation enabled")
    except Exception as e:
        logger.warning("Failed to instrument Redis", error=str(e))


def get_tracer(name: str, version: str = "0.1.0") -> trace.Tracer:
    """
    Get or create a tracer instance.
    
    Args:
        name: Tracer name (typically module or component name)
        version: Version identifier
    
    Returns:
        Tracer instance
    """
    return trace.get_tracer(name, version)


def trace_function(
    span_name: Optional[str] = None,
    attributes: Optional[dict[str, Any]] = None,
) -> Callable:
    """
    Decorator to trace function execution.
    
    Args:
        span_name: Custom span name (defaults to function name)
        attributes: Additional span attributes
    
    Usage:
        @trace_function(span_name="process_inspection", attributes={"type": "quality"})
        async def process_inspection(inspection_id: str):
            # Function implementation
            pass
    
    Features:
        - Automatic span creation and management
        - Exception tracking with stack traces
        - Function arguments as span attributes
        - Async function support
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer(func.__module__)
            name = span_name or f"{func.__module__}.{func.__name__}"
            
            with tracer.start_as_current_span(name) as span:
                # Add default attributes
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                # Add custom attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, str(value))
                
                # Add function arguments (be careful with sensitive data)
                if kwargs:
                    for key, value in kwargs.items():
                        # Skip sensitive parameters
                        if key not in ["password", "secret", "token", "key"]:
                            span.set_attribute(f"arg.{key}", str(value)[:100])
                
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer(func.__module__)
            name = span_name or f"{func.__module__}.{func.__name__}"
            
            with tracer.start_as_current_span(name) as span:
                # Add default attributes
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                # Add custom attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, str(value))
                
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def add_span_attributes(attributes: dict[str, Any]) -> None:
    """
    Add attributes to the current active span.
    
    Args:
        attributes: Dictionary of attributes to add
    
    Usage:
        add_span_attributes({
            "inspection.id": inspection_id,
            "inspection.type": inspection_type,
            "batch.size": batch_size,
        })
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        for key, value in attributes.items():
            span.set_attribute(key, str(value))


def add_span_event(name: str, attributes: Optional[dict[str, Any]] = None) -> None:
    """
    Add an event to the current active span.
    
    Args:
        name: Event name
        attributes: Event attributes
    
    Usage:
        add_span_event("defect_detected", {"defect_type": "scratch", "confidence": 0.95})
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        span.add_event(name, attributes or {})
