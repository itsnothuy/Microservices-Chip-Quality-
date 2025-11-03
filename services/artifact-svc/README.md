# Artifact Service

Production-grade artifact and file management service for the Chip Quality Platform.

## Features

- **File Upload/Download**: Secure file upload and download with validation
- **MinIO Integration**: Object storage with MinIO for scalable file storage
- **Metadata Management**: Comprehensive file metadata tracking and indexing
- **File Validation**: Content type validation, size limits, and checksum verification
- **RESTful API**: Complete CRUD operations for artifact management

## Architecture

The service follows a layered architecture:
- **Routers**: FastAPI endpoints for HTTP API
- **Services**: Business logic and orchestration
- **Models**: SQLAlchemy database models
- **Schemas**: Pydantic models for validation
- **Utils**: Utility functions for file handling

## Configuration

Environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `S3_ENDPOINT_URL`: MinIO endpoint
- `S3_ACCESS_KEY_ID`: MinIO access key
- `S3_SECRET_ACCESS_KEY`: MinIO secret key
- `S3_BUCKET_NAME`: Storage bucket name

## API Endpoints

### Artifacts
- `POST /api/v1/artifacts/upload` - Upload artifact file
- `GET /api/v1/artifacts` - List artifacts with filtering
- `GET /api/v1/artifacts/{id}` - Get artifact metadata
- `GET /api/v1/artifacts/{id}/download` - Download artifact file
- `PUT /api/v1/artifacts/{id}` - Update artifact metadata
- `DELETE /api/v1/artifacts/{id}` - Delete artifact

### Health
- `GET /health` - Basic health check
- `GET /health/ready` - Readiness check
- `GET /health/live` - Liveness check

## Development

### Setup
```bash
cd services/artifact-svc
pip install -r requirements.txt
```

### Run locally
```bash
uvicorn app.main:app --reload
```

### Run with Docker
```bash
docker build -t artifact-service .
docker run -p 8000:8000 artifact-service
```

## Testing

Run tests:
```bash
pytest tests/
```

## Production Deployment

Deploy using Kubernetes:
```bash
kubectl apply -f ../../k8s/artifact-service/
```
