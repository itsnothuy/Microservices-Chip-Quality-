"""
Metrics Collection and Management

Provides centralized metrics collection and Prometheus integration.
"""

from typing import Optional
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from prometheus_client import CollectorRegistry, REGISTRY
import structlog

logger = structlog.get_logger()


def setup_metrics(
    service_name: str,
    service_version: str = "0.1.0",
    registry: Optional[CollectorRegistry] = None,
) -> metrics.Meter:
    """
    Setup OpenTelemetry metrics with Prometheus exporter.
    
    Args:
        service_name: Name of the service
        service_version: Version of the service
        registry: Prometheus registry (defaults to global registry)
    
    Returns:
        Configured meter instance
    """
    # Create resource with service information
    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: service_version,
    })
    
    # Use provided registry or default
    prom_registry = registry or REGISTRY
    
    # Create Prometheus metric reader
    reader = PrometheusMetricReader(registry=prom_registry)
    
    # Create meter provider
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[reader]
    )
    
    metrics.set_meter_provider(meter_provider)
    
    logger.info(
        "Metrics collection configured",
        service_name=service_name,
        version=service_version
    )
    
    return metrics.get_meter(service_name, service_version)


def get_meter(name: str, version: str = "0.1.0") -> metrics.Meter:
    """
    Get or create a meter instance.
    
    Args:
        name: Meter name (typically module or component name)
        version: Version identifier
    
    Returns:
        Meter instance
    """
    return metrics.get_meter(name, version)
