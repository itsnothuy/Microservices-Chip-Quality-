# API Gateway Service

Production-ready FastAPI service that provides unified entry point for the Chip Quality Platform.

## Features

- **Authentication & Authorization**: JWT-based auth with role-based permissions
- **Request Routing**: Intelligent routing to upstream microservices
- **Rate Limiting**: Redis-backed rate limiting with user/IP identification
- **Observability**: OpenTelemetry tracing, Prometheus metrics, structured logging
- **Security**: CORS, trusted hosts, input validation, secure headers

## Architecture

The API Gateway acts as the single entry point for all client requests:

```
Client -> API Gateway -> [Ingestion, Inference, Metadata, Artifact, Report] Services
```

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -e .

# Set environment variables
export SECRET_KEY="your-secret-key"
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/db"
export REDIS_URL="redis://localhost:6379"

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```bash
# Build image
docker build -t api-gateway .

# Run container
docker run -p 8000:8000 \
  -e SECRET_KEY="your-secret-key" \
  -e DATABASE_URL="postgresql+asyncpg://user:pass@db/chip_quality" \
  -e REDIS_URL="redis://redis:6379" \
  api-gateway
```

## API Documentation

Access interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Authentication

### Login

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

### Use Token

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/inspections"
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT secret key | **Required** |
| `DATABASE_URL` | Database connection | **Required** |
| `REDIS_URL` | Redis connection | `redis://localhost:6379` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `ENVIRONMENT` | Environment name | `development` |
| `RATE_LIMIT_PER_MINUTE` | Rate limit | `100` |
| `CORS_ORIGINS` | CORS origins | `["*"]` |

### Service URLs

| Service | Environment Variable | Default |
|---------|---------------------|---------|
| Ingestion | `INGESTION_SERVICE_URL` | `http://ingestion-svc:8001` |
| Inference | `INFERENCE_SERVICE_URL` | `http://inference-svc:8002` |
| Metadata | `METADATA_SERVICE_URL` | `http://metadata-svc:8003` |
| Artifact | `ARTIFACT_SERVICE_URL` | `http://artifact-svc:8004` |
| Report | `REPORT_SERVICE_URL` | `http://report-svc:8005` |

## Health Checks

- **Liveness**: `GET /health/live` - Basic health check
- **Readiness**: `GET /health/ready` - Includes upstream service checks
- **Metrics**: `GET /metrics` - Prometheus metrics

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

## Monitoring

### Metrics

The service exposes Prometheus metrics:
- HTTP request counts and durations
- Upstream service metrics
- Authentication metrics
- Rate limiting metrics

### Tracing

OpenTelemetry traces are exported to configured OTLP endpoint:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="http://jaeger:14268/api/traces"
```

### Logging

Structured JSON logs with trace correlation:

```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "info",
  "message": "Request completed",
  "method": "GET",
  "url": "/api/v1/inspections",
  "status_code": 200,
  "duration": 0.123,
  "trace_id": "0x1234567890abcdef",
  "user_id": "user_001"
}
```

## Security

### Authentication

- JWT tokens with configurable expiration
- Refresh token rotation
- Role-based access control (RBAC)
- Scope-based permissions

### Rate Limiting

- Per-user and per-IP rate limiting
- Redis-backed storage
- Configurable limits and burst handling

### Input Validation

- Pydantic models for request validation
- SQL injection prevention
- XSS protection
- File upload validation

## Development

### Adding New Routes

1. Create router in `app/routers/`
2. Add route permissions in `app/core/auth.py`
3. Update service client in `app/core/http_client.py`
4. Include router in `app/main.py`

### Testing Upstream Services

Use the built-in health check system:

```python
# Check all services
response = requests.get("http://localhost:8000/health/ready")
print(response.json())
```

## Deployment

See the main platform documentation for Kubernetes deployment instructions.