"""
Shared Observability Module for Chip Quality Platform

Provides comprehensive observability infrastructure including:
- Distributed tracing with OpenTelemetry
- Metrics collection with Prometheus
- Structured logging with correlation IDs
- Health checking and monitoring
- Alert rule definitions
"""

from services.shared.observability.tracing.tracer import (
    setup_tracing,
    get_tracer,
    trace_function,
)
from services.shared.observability.metrics.collector import (
    setup_metrics,
    get_meter,
)
from services.shared.observability.metrics.business_metrics import (
    QualityMetrics,
    ProductionMetrics,
    MLPerformanceMetrics,
)
from services.shared.observability.logging.setup import (
    setup_structured_logging,
    get_logger,
)
from services.shared.observability.health.checks import (
    HealthChecker,
    ServiceHealthCheck,
)

__all__ = [
    # Tracing
    "setup_tracing",
    "get_tracer",
    "trace_function",
    # Metrics
    "setup_metrics",
    "get_meter",
    "QualityMetrics",
    "ProductionMetrics",
    "MLPerformanceMetrics",
    # Logging
    "setup_structured_logging",
    "get_logger",
    # Health
    "HealthChecker",
    "ServiceHealthCheck",
]

__version__ = "0.1.0"
