"""Tracing module exports"""

from services.shared.observability.tracing.tracer import (
    setup_tracing,
    get_tracer,
    trace_function,
    add_span_attributes,
    add_span_event,
)

__all__ = [
    "setup_tracing",
    "get_tracer",
    "trace_function",
    "add_span_attributes",
    "add_span_event",
]
