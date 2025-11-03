"""Logging module exports"""

from services.shared.observability.logging.setup import (
    setup_structured_logging,
    get_logger,
    bind_contextvars,
    unbind_contextvars,
    clear_contextvars,
)
from services.shared.observability.logging.correlation import (
    generate_correlation_id,
    generate_request_id,
    set_correlation_id,
    get_correlation_id,
    set_request_id,
    get_request_id,
    clear_context,
)

__all__ = [
    # Setup
    "setup_structured_logging",
    "get_logger",
    "bind_contextvars",
    "unbind_contextvars",
    "clear_contextvars",
    # Correlation
    "generate_correlation_id",
    "generate_request_id",
    "set_correlation_id",
    "get_correlation_id",
    "set_request_id",
    "get_request_id",
    "clear_context",
]
