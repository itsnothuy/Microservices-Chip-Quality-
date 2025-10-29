"""Observability setup with OpenTelemetry and Prometheus"""

import os
from typing import Optional

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import structlog

from app.core.config import Settings


logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections'
)

UPSTREAM_DURATION = Histogram(
    'upstream_request_duration_seconds',
    'Upstream service request duration',
    ['service', 'endpoint']
)

UPSTREAM_ERRORS = Counter(
    'upstream_errors_total',
    'Upstream service errors',
    ['service', 'error_type']
)


def setup_observability(settings: Settings) -> None:
    """Setup OpenTelemetry tracing and metrics"""
    
    # Setup tracing
    trace.set_tracer_provider(TracerProvider())
    tracer = trace.get_tracer(
        settings.otel_service_name,
        settings.otel_service_version
    )
    
    # Setup OTLP exporter if endpoint is configured
    if settings.otel_exporter_otlp_endpoint:
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.otel_exporter_otlp_endpoint,
            insecure=True  # Use secure=True in production with proper certs
        )
        span_processor = BatchSpanProcessor(otlp_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
        
        logger.info(
            "OpenTelemetry OTLP exporter configured",
            endpoint=settings.otel_exporter_otlp_endpoint
        )
    
    # Setup metrics
    if settings.otel_exporter_otlp_endpoint:
        metric_exporter = OTLPMetricExporter(
            endpoint=settings.otel_exporter_otlp_endpoint,
            insecure=True
        )
        metric_reader = PeriodicExportingMetricReader(
            exporter=metric_exporter,
            export_interval_millis=30000  # 30 seconds
        )
        metrics.set_meter_provider(MeterProvider(metric_readers=[metric_reader]))
    
    # Instrument SQLAlchemy
    SQLAlchemyInstrumentor().instrument()
    
    # Instrument HTTPX
    HTTPXClientInstrumentor().instrument()
    
    logger.info("Observability setup complete")


def get_tracer(name: str) -> trace.Tracer:
    """Get OpenTelemetry tracer"""
    return trace.get_tracer(name)


def get_meter(name: str) -> metrics.Meter:
    """Get OpenTelemetry meter"""
    return metrics.get_meter(name)