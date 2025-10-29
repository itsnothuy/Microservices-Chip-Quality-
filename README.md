# Chip Quality Platform

A production-grade microservices-based chip quality inspection system using NVIDIA Triton Inference Server, FastAPI, Kafka, and Kubernetes.

## 🏗️ Architecture Overview

This system implements a **Vision AI pipeline** aligned with NVIDIA Metropolis conventions for manufacturing quality control:

- **API Gateway** (FastAPI) - OAuth2/JWT auth, rate limiting, request routing
- **Ingestion Service** - Handles inspection creation with idempotency
- **Artifact Service** - MinIO S3-compatible storage with presigned URLs
- **Inference Service** - NVIDIA Triton client for ML inference
- **Metadata Service** - PostgreSQL/TimescaleDB with cursor pagination
- **Report Service** - PDF/JSON report generation
- **Event Bus** - Kafka for async processing
- **Observability** - OpenTelemetry, Prometheus, Grafana, Loki

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- NVIDIA Docker Runtime (for GPU inference)
- Kubernetes cluster (for production)

### Local Development
```bash
# Clone and setup
git clone <repo-url>
cd chip-quality-platform

# Start infrastructure
docker-compose up -d postgres kafka minio

# Install dependencies
pip install -r requirements-dev.txt

# Run services
make dev-gateway
make dev-inference

# Access services
open http://localhost:8080/docs  # API Gateway
open http://localhost:9001       # MinIO Console
```

### Demo Flow
```bash
# 1. Get auth token
TOKEN=$(curl -s -X POST "localhost:8080/v1/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo&password=demo" | jq -r .access_token)

# 2. Create inspection
INSPECTION=$(curl -s -X POST "localhost:8080/v1/inspections" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Idempotency-Key: demo-$(date +%s)" \
  -H "Content-Type: application/json" \
  -d '{"lot":"DEMO-LOT","part":"PCB-001","station":"AOI-1"}' | jq -r .inspection_id)

# 3. Upload artifact
UPLOAD_URL=$(curl -s -X POST "localhost:8080/v1/inspections/$INSPECTION/artifacts?type=image/jpeg" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Idempotency-Key: demo-upload-$(date +%s)" | jq -r .upload_url)

curl -X PUT "$UPLOAD_URL" --upload-file demo-data/pcb.jpg

# 4. Trigger inference
curl -X POST "localhost:8080/v1/inspections/$INSPECTION/infer" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Idempotency-Key: demo-infer-$(date +%s)"

# 5. Check reports
curl -s "localhost:8080/v1/reports?limit=5" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

## 📚 Documentation

- [Architecture Guide](docs/architecture.md) - System design and patterns
- [API Reference](docs/api/openapi.yaml) - OpenAPI 3.1 specification
- [Event Schemas](docs/events/asyncapi.yaml) - AsyncAPI 3.0 contracts
- [Deployment Guide](docs/deployment.md) - Kubernetes and Helm setup
- [Security Model](docs/security/threat-model.md) - Auth, compliance, and auditing
- [Observability](docs/sre/slis-slos.md) - Monitoring and alerting
- [Development](docs/development.md) - Local setup and testing

## 🔧 Key Features

### Production-Ready Patterns
- **Idempotency**: Stripe-style idempotency keys on all mutations
- **Pagination**: Cursor-based (keyset) pagination for stable results
- **Auth**: OAuth2 + JWT with scopes and rate limiting
- **Observability**: Full OpenTelemetry tracing with correlation IDs
- **Resilience**: Circuit breakers, retries, and graceful degradation

### NVIDIA Integration
- **Triton Inference Server**: gRPC client with dynamic batching
- **Model Hot-Reload**: Zero-downtime model updates
- **GPU Scheduling**: Kubernetes node affinity and HPA
- **Metropolis Alignment**: Vision AI microservices patterns

### Compliance & Security
- **Audit Logging**: Complete action trail with user context
- **Data Integrity**: Checksums, versioning, and retention policies
- **Encryption**: TLS, presigned URLs, and secrets management
- **RBAC**: Role-based access with JWT scopes

## 📁 Project Structure

```
chip-quality-platform/
├── services/           # Microservices (FastAPI apps)
│   ├── api-gateway/
│   ├── ingestion-svc/
│   ├── inference-svc/
│   ├── metadata-svc/
│   ├── artifact-svc/
│   └── report-svc/
├── deploy/             # Kubernetes & Helm
│   ├── helm/charts/
│   ├── k8s/
│   └── argocd/
├── docs/               # Architecture & API docs
├── ops/                # Observability configs
├── scripts/            # Load testing & utilities
├── triton/             # Model repository
└── compose/            # Docker Compose for dev
```

## 🧪 Testing

```bash
# Unit tests
make test

# Integration tests
make test-integration

# Load testing
make load-test

# Security scanning
make security-scan
```

## 🚢 Deployment

### Kubernetes (Production)
```bash
# Install with Helm
helm upgrade --install chip-quality ./deploy/helm/charts/platform \
  --namespace production --create-namespace \
  --values deploy/helm/values/prod.yaml

# Or use Argo CD (GitOps)
kubectl apply -f deploy/argocd/app-of-apps.yaml
```

### Scaling
- **HPA**: Auto-scaling based on CPU/GPU utilization
- **VPA**: Vertical pod autoscaling for resource optimization
- **Cluster Autoscaler**: Node-level scaling for GPU workloads

## 📊 Monitoring

- **Metrics**: Prometheus + custom business metrics
- **Logs**: Structured JSON logs via Loki
- **Traces**: OpenTelemetry end-to-end tracing
- **Dashboards**: Grafana with pre-built panels
- **Alerts**: PagerDuty/Slack integration

## 🤝 Contributing

1. Read [CONTRIBUTING.md](CONTRIBUTING.md)
2. Check [ADRs](adr/) for architectural decisions
3. Follow [Conventional Commits](https://www.conventionalcommits.org/)
4. Sign commits (DCO required)

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## 🆘 Support

- 📖 Documentation: [docs/](docs/)
- 🐛 Issues: [GitHub Issues](https://github.com/your-org/chip-quality-platform/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/your-org/chip-quality-platform/discussions)
- 🔒 Security: See [SECURITY.md](SECURITY.md)

---

Built with ❤️ for manufacturing quality excellence