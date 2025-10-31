# Inference Service

ML Inference Pipeline with NVIDIA Triton for real-time defect detection in semiconductor manufacturing.

## Features

- **NVIDIA Triton Integration**: High-performance ML inference server
- **Real-time & Batch Inference**: Support for single and batch image processing
- **Model Management**: Dynamic model loading, versioning, and deployment
- **Performance Monitoring**: Comprehensive metrics and health checks
- **Image Preprocessing**: Automated image normalization and preparation
- **Result Postprocessing**: Confidence filtering and quality assessment
- **A/B Testing**: Model comparison framework
- **Observability**: OpenTelemetry tracing, Prometheus metrics, structured logging

## Architecture

```
inference-svc/
├── app/
│   ├── core/           # Core configuration and dependencies
│   ├── models/         # Data models
│   ├── schemas/        # Pydantic schemas for API
│   ├── services/       # Business logic services
│   ├── routers/        # API endpoints
│   └── utils/          # Utility functions
├── models/             # ML model storage
├── tests/              # Test suite
└── Dockerfile          # Container configuration
```

## API Endpoints

### Inference Endpoints
- `POST /api/v1/inference/predict` - Single image inference
- `POST /api/v1/inference/batch` - Batch inference
- `GET /api/v1/inference/{id}` - Get inference status
- `POST /api/v1/inference/{id}/cancel` - Cancel inference
- `GET /api/v1/inference/metrics/summary` - Performance metrics

### Model Management
- `GET /api/v1/models` - List available models
- `GET /api/v1/models/{name}` - Get model information
- `GET /api/v1/models/{name}/versions` - List model versions
- `GET /api/v1/models/{name}/status` - Model health status
- `POST /api/v1/models/deploy` - Deploy model version
- `POST /api/v1/models/{name}/load` - Load model to Triton
- `POST /api/v1/models/{name}/unload` - Unload model

### Monitoring
- `GET /api/v1/monitoring/health` - Service health check
- `GET /api/v1/monitoring/models/{name}/health` - Model health
- `GET /api/v1/monitoring/models/{name}/metrics` - Model metrics
- `GET /api/v1/monitoring/models/{name}/anomalies` - Anomaly detection

## Configuration

Environment variables:

```bash
# Service Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/chip_quality

# Redis
REDIS_URL=redis://:password@localhost:6379/2

# NVIDIA Triton
TRITON_SERVER_URL=localhost:8001
TRITON_HTTP_URL=http://localhost:8000
TRITON_TIMEOUT=30
TRITON_MODEL_NAME=defect_detection_v1

# Image Processing
IMAGE_TARGET_WIDTH=1024
IMAGE_TARGET_HEIGHT=1024
IMAGE_MAX_SIZE=10485760

# Model Settings
MODEL_CONFIDENCE_THRESHOLD=0.75

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# OpenTelemetry
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4318
```

## Running Locally

### With Docker Compose

```bash
cd /path/to/Microservices-Chip-Quality-
docker-compose up inference-service
```

### Standalone

```bash
cd services/inference-svc

# Install dependencies
pip install -r requirements.txt

# Run service
uvicorn app.main:app --reload --port 8000
```

## Model Repository Structure

Place models in the `models/` directory following Triton's model repository structure:

```
models/
├── defect_detection_v1/
│   ├── config.pbtxt
│   └── 1/
│       └── model.onnx
├── thermal_analysis_v1/
│   ├── config.pbtxt
│   └── 1/
│       └── model.onnx
└── electrical_defect_v1/
    ├── config.pbtxt
    └── 1/
        └── model.onnx
```

## Performance

Target performance metrics:
- Single image inference latency: < 2 seconds
- Batch throughput: > 100 images/minute
- GPU utilization: > 80% during inference
- Concurrent requests: 50+

## Development

### Adding a New Model

1. Place model in `models/` directory
2. Create model configuration file
3. Load model via API: `POST /api/v1/models/{name}/load`
4. Verify readiness: `GET /api/v1/models/{name}/status`

### Testing

```bash
# Run tests
pytest tests/

# With coverage
pytest tests/ --cov=app --cov-report=html
```

## Troubleshooting

### Triton Connection Issues
- Verify Triton server is running: `curl http://localhost:8000/v2/health/ready`
- Check network connectivity
- Review Triton logs

### Model Loading Failures
- Verify model repository structure
- Check model configuration file
- Ensure model format is supported (ONNX, PyTorch, TensorFlow)
- Review model compatibility with Triton version

### Performance Issues
- Monitor GPU utilization
- Check batch sizes and dynamic batching configuration
- Review preprocessing performance
- Analyze Triton metrics at `:8002/metrics`

## References

- [NVIDIA Triton Documentation](https://docs.nvidia.com/deeplearning/triton-inference-server/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
