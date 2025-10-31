# Inspection Service

Production-grade microservice for inspection workflow orchestration, quality assessment, and defect management.

## Features

- **Inspection Orchestration**: End-to-end inspection workflow management
- **Quality Assessment**: Automated quality scoring and classification
- **Defect Detection**: Integration with ML models for defect identification
- **Manual Review**: Human inspector validation and override capabilities
- **Status Tracking**: Real-time inspection status updates
- **Idempotency**: Duplicate inspection prevention
- **Quality Metrics**: Comprehensive quality metrics calculation
- **Threshold Management**: Configurable quality thresholds
- **Trend Analysis**: Historical quality tracking

## Architecture

```
inspection-svc/
├── app/
│   ├── core/           # Configuration, dependencies, exceptions
│   ├── services/       # Business logic services
│   ├── routers/        # API endpoints
│   ├── models/         # Business models
│   ├── schemas/        # Pydantic schemas
│   └── utils/          # Utility functions
├── tests/              # Unit and integration tests
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container image
└── README.md          # This file
```

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/chip_quality"
export TRITON_URL="localhost:8001"

# Run service
uvicorn app.main:app --reload --port 8000
```

### Docker

```bash
# Build image
docker build -t inspection-svc:latest .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://postgres:postgres@host.docker.internal:5432/chip_quality" \
  inspection-svc:latest
```

## API Documentation

Once running, access the interactive API documentation at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Key Endpoints

### Inspections

- `POST /api/v1/inspections` - Create new inspection
- `GET /api/v1/inspections` - List inspections
- `GET /api/v1/inspections/{id}` - Get inspection details
- `POST /api/v1/inspections/{id}/start` - Start inspection
- `POST /api/v1/inspections/{id}/complete` - Complete inspection

### Defects

- `POST /api/v1/defects` - Create defect
- `GET /api/v1/defects` - List defects
- `GET /api/v1/defects/{id}` - Get defect details
- `POST /api/v1/defects/{id}/confirm` - Confirm defect

### Quality

- `GET /api/v1/quality/metrics/{id}` - Get quality metrics
- `GET /api/v1/quality/assessment/{id}` - Get quality assessment
- `GET /api/v1/quality/trends` - Get quality trends

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `TRITON_URL` | NVIDIA Triton server URL | `localhost:8001` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka brokers | `localhost:9092` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Testing

```bash
# Run unit tests
pytest tests/unit -v

# Run integration tests
pytest tests/integration -v

# Run with coverage
pytest --cov=app --cov-report=html
```

## Production Deployment

The service is designed for Kubernetes deployment with:

- Health checks at `/health`, `/health/ready`, `/health/live`
- Prometheus metrics support
- Distributed tracing via OpenTelemetry
- Structured logging with correlation IDs
- Graceful shutdown handling

## Performance

- Inspection processing: < 30 seconds per chip
- Concurrent inspections: 50+ simultaneous
- ML inference latency: < 2 seconds per image
- API response time: < 200ms

## Security

- OAuth2/JWT authentication integration
- Input validation with Pydantic
- SQL injection prevention via SQLAlchemy ORM
- CORS configuration
- Rate limiting support

## License

MIT License - see LICENSE file for details
