"""
Structured Logging Setup

Provides comprehensive structured logging with:
- JSON formatted logs for machine parsing
- Correlation ID tracking
- Context propagation
- Log level management
- Integration with Loki
"""

import logging
import sys
from typing import Any, Dict, Optional
import structlog
from structlog.types import Processor
from opentelemetry import trace

# Global logger instance
_logger: Optional[structlog.BoundLogger] = None


def setup_structured_logging(
    log_level: str = "INFO",
    service_name: str = "chip-quality-service",
    json_logs: bool = True,
) -> structlog.BoundLogger:
    """
    Setup structured logging with structlog.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        service_name: Name of the service
        json_logs: Whether to use JSON formatting (True for production)
    
    Returns:
        Configured structured logger
    
    Features:
        - Automatic correlation ID injection
        - Trace context propagation
        - Timestamp and log level formatting
        - Exception stack trace capture
        - Contextual information preservation
    """
    global _logger
    
    # Configure Python's logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # Shared processors for all configurations
    shared_processors: list[Processor] = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.contextvars.merge_contextvars,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        _add_trace_context,
        _add_service_context(service_name),
    ]
    
    if json_logs:
        # Production: JSON logs
        processors = shared_processors + [
            structlog.processors.JSONRenderer()
        ]
    else:
        # Development: Colored console logs
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    _logger = structlog.get_logger(service_name)
    
    _logger.info(
        "Structured logging configured",
        log_level=log_level,
        service_name=service_name,
        json_format=json_logs,
    )
    
    return _logger


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """
    Get or create a logger instance.
    
    Args:
        name: Logger name (typically module name)
    
    Returns:
        Structured logger instance
    """
    if _logger is None:
        # Initialize with defaults if not already setup
        setup_structured_logging()
    
    if name:
        return structlog.get_logger(name)
    return structlog.get_logger()


def _add_trace_context(
    logger: logging.Logger,
    method_name: str,
    event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Add OpenTelemetry trace context to log events.
    
    Automatically includes:
    - trace_id: Unique trace identifier
    - span_id: Current span identifier
    - trace_flags: Trace sampling flags
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        ctx = span.get_span_context()
        if ctx.is_valid:
            event_dict["trace_id"] = format(ctx.trace_id, "032x")
            event_dict["span_id"] = format(ctx.span_id, "016x")
            event_dict["trace_flags"] = ctx.trace_flags
    
    return event_dict


def _add_service_context(service_name: str) -> Processor:
    """
    Create processor to add service context to all log events.
    
    Args:
        service_name: Name of the service
    
    Returns:
        Processor function
    """
    def processor(
        logger: logging.Logger,
        method_name: str,
        event_dict: Dict[str, Any]
    ) -> Dict[str, Any]:
        event_dict["service"] = service_name
        return event_dict
    
    return processor


def bind_contextvars(**kwargs: Any) -> None:
    """
    Bind context variables to be included in all subsequent log entries.
    
    Args:
        **kwargs: Key-value pairs to bind to context
    
    Usage:
        bind_contextvars(
            request_id="req-12345",
            user_id="user-67890",
            inspection_id="insp-abc"
        )
        
        # All subsequent logs will include these fields
        logger.info("Processing inspection")
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def unbind_contextvars(*keys: str) -> None:
    """
    Remove context variables.
    
    Args:
        *keys: Keys to remove from context
    
    Usage:
        unbind_contextvars("request_id", "user_id")
    """
    structlog.contextvars.unbind_contextvars(*keys)


def clear_contextvars() -> None:
    """Clear all context variables."""
    structlog.contextvars.clear_contextvars()
