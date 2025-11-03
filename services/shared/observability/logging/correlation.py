"""
Correlation ID Management

Provides request correlation tracking across services.
"""

import uuid
from typing import Optional
from contextvars import ContextVar

# Context variable for correlation ID
_correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
_request_id: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


def generate_correlation_id() -> str:
    """
    Generate a new correlation ID.
    
    Returns:
        UUID-based correlation ID
    """
    return f"corr-{uuid.uuid4().hex[:16]}"


def generate_request_id() -> str:
    """
    Generate a new request ID.
    
    Returns:
        UUID-based request ID
    """
    return f"req-{uuid.uuid4().hex[:16]}"


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """
    Set correlation ID for current context.
    
    Args:
        correlation_id: Optional correlation ID (generates new if not provided)
    
    Returns:
        The correlation ID that was set
    """
    if correlation_id is None:
        correlation_id = generate_correlation_id()
    
    _correlation_id.set(correlation_id)
    return correlation_id


def get_correlation_id() -> Optional[str]:
    """
    Get correlation ID from current context.
    
    Returns:
        Correlation ID or None if not set
    """
    return _correlation_id.get()


def set_request_id(request_id: Optional[str] = None) -> str:
    """
    Set request ID for current context.
    
    Args:
        request_id: Optional request ID (generates new if not provided)
    
    Returns:
        The request ID that was set
    """
    if request_id is None:
        request_id = generate_request_id()
    
    _request_id.set(request_id)
    return request_id


def get_request_id() -> Optional[str]:
    """
    Get request ID from current context.
    
    Returns:
        Request ID or None if not set
    """
    return _request_id.get()


def clear_context() -> None:
    """Clear correlation and request IDs from context."""
    _correlation_id.set(None)
    _request_id.set(None)
