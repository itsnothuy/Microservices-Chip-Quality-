# Observability & Monitoring Infrastructure

Comprehensive observability infrastructure for the Chip Quality Platform using OpenTelemetry, Prometheus, and Grafana.

## Features

### 🔍 Distributed Tracing
- OpenTelemetry integration with OTLP export
- Automatic instrumentation for HTTP, database, cache operations
- Custom span creation and attribute management
- Trace context propagation across services
- Integration with Jaeger/Tempo backends

### 📊 Metrics Collection
- **Business Metrics**: Quality scores, defect rates, production metrics, ML performance
- **System Metrics**: API performance, database queries, cache operations, queue processing
- Prometheus exposition format
- Custom metric definitions with labels
- Performance-optimized collection (<5% overhead)

### 📝 Structured Logging
- JSON-formatted logs for machine parsing
- Correlation ID tracking across services
- Automatic trace context injection
- Context variable binding
- Integration with Loki for aggregation

### 🏥 Health Checking
- Service dependency health checks (Database, Redis, Kafka, MinIO, Triton)
- Business health indicators
- Kubernetes-compatible endpoints (/live, /ready)
- Comprehensive health reports
- Configurable timeouts and criticality

### 🚨 Alerting
- **39 pre-configured alert rules** covering:
  - Quality alerts (defect rates, quality scores, compliance)
  - Performance alerts (latency, throughput, cache efficiency)
  - System alerts (errors, resources, availability)
  - Business alerts (yield, OEE, model drift, costs)
- Configurable thresholds and severity levels
- Runbook URLs and dashboard links

## Usage

### Setting Up Tracing

```python
from services.shared.observability.tracing import setup_tracing, trace_function

# Setup tracing for your service
tracer = setup_tracing(
    service_name="my-service",
    service_version="1.0.0",
    otlp_endpoint="http://jaeger:4317"
)

# Use decorator for automatic tracing
@trace_function(span_name="process_inspection")
async def process_inspection(inspection_id: str):
    # Your code here
    pass
```

### Recording Business Metrics

```python
from services.shared.observability.metrics import QualityMetrics

quality_metrics = QualityMetrics()

# Record defect detection
quality_metrics.record_defect(
    product_type="PCB-A",
    defect_type="scratch",
    severity="high"
)

# Record inspection result
quality_metrics.record_inspection_result(
    product_type="PCB-A",
    inspection_type="visual",
    passed=True,
    quality_score=0.95,
    duration_seconds=45.5
)
```

### Setting Up Health Checks

```python
from services.shared.observability.health import (
    health_checker,
    create_database_check,
    create_redis_check,
)

# Register health checks
health_checker.register_check(
    create_database_check(db_url="postgresql://...")
)
health_checker.register_check(
    create_redis_check(redis_url="redis://...")
)

# Check all health checks
results = await health_checker.check_all()
overall_status = health_checker.get_overall_status()
```

### Adding Health Endpoints to FastAPI

```python
from fastapi import FastAPI
from services.shared.observability.health import create_health_router

app = FastAPI()

# Add health check endpoints
health_router = create_health_router(
    service_name="my-service",
    service_version="1.0.0"
)
app.include_router(health_router, prefix="/health", tags=["health"])
```

### Structured Logging

```python
from services.shared.observability.logging import (
    setup_structured_logging,
    get_logger,
    bind_contextvars,
)

# Setup structured logging
setup_structured_logging(
    log_level="INFO",
    service_name="my-service",
    json_logs=True
)

logger = get_logger(__name__)

# Bind context for all subsequent logs
bind_contextvars(
    request_id="req-12345",
    user_id="user-67890"
)

# Log with structured data
logger.info("Processing inspection", inspection_id="insp-abc", status="started")
```

## Architecture

### Component Structure

```
services/shared/observability/
├── tracing/           # OpenTelemetry distributed tracing
│   ├── tracer.py      # Tracer setup and decorators
│   └── __init__.py
├── metrics/           # Prometheus metrics
│   ├── business_metrics.py    # Quality, production, ML metrics
│   ├── system_metrics.py      # API, database, cache metrics
│   ├── collector.py           # Metrics collection setup
│   └── __init__.py
├── logging/           # Structured logging
│   ├── setup.py       # Logging configuration
│   ├── correlation.py # Correlation ID management
│   └── __init__.py
├── health/            # Health checking
│   ├── checks.py      # Health check framework
│   ├── dependencies.py # Service health checks
│   ├── endpoints.py   # FastAPI health endpoints
│   └── __init__.py
└── __init__.py
```

### Monitoring Stack

```
monitoring/
├── prometheus/
│   ├── prometheus.yml     # Prometheus configuration
│   └── alerts/            # Alert rule definitions
│       ├── quality.yml    # Quality-related alerts
│       ├── performance.yml # Performance alerts
│       ├── system.yml     # System resource alerts
│       └── business.yml   # Business metric alerts
└── grafana/
    ├── dashboards/        # Grafana dashboard JSON
    └── provisioning/      # Grafana provisioning config
```

## Integration

### With FastAPI

The observability components integrate seamlessly with FastAPI:

```python
from fastapi import FastAPI
from services.shared.observability import (
    setup_tracing,
    setup_metrics,
    setup_structured_logging,
    health_checker,
    create_health_router,
)

app = FastAPI()

# Setup observability on startup
@app.on_event("startup")
async def startup_observability():
    setup_tracing("my-service", otlp_endpoint="http://jaeger:4317")
    setup_metrics("my-service")
    setup_structured_logging(log_level="INFO", service_name="my-service")
    
    # Register health checks
    health_checker.register_check(...)

# Add health endpoints
app.include_router(create_health_router(), prefix="/health")
```

### With Kubernetes

Health check endpoints are compatible with Kubernetes probes:

```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: my-service
    livenessProbe:
      httpGet:
        path: /health/live
        port: 8000
      initialDelaySeconds: 10
      periodSeconds: 10
    readinessProbe:
      httpGet:
        path: /health/ready
        port: 8000
      initialDelaySeconds: 5
      periodSeconds: 5
```

## Testing

Run the observability unit tests:

```bash
pytest tests/unit/observability/ -v
```

## Performance

The observability infrastructure is designed for minimal performance impact:

- **Tracing overhead**: <5ms per request
- **Metrics collection**: <1ms per metric update
- **Overall overhead**: <5% of total response time
- **Memory footprint**: ~50MB per service

## Best Practices

1. **Always use correlation IDs** for request tracking across services
2. **Record business metrics** at critical decision points
3. **Set appropriate health check timeouts** (5-10 seconds)
4. **Use structured logging** with meaningful context
5. **Mark critical dependencies** in health checks
6. **Monitor alert fatigue** - tune thresholds appropriately

## Contributing

When adding new observability features:

1. Add comprehensive tests in `tests/unit/observability/`
2. Update this README with usage examples
3. Ensure performance impact remains <5%
4. Document alert thresholds and runbook procedures

## References

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Grafana Dashboard Design](https://grafana.com/docs/grafana/latest/best-practices/)
- [Health Check Patterns](https://microservices.io/patterns/observability/health-check-api.html)
