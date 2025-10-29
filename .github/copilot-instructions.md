# GitHub Copilot Instructions for Chip Quality Platform

## 🎯 Project Overview

This is a **production-grade semiconductor manufacturing quality control platform** that uses AI/ML for automated defect detection and quality assurance. The system handles high-throughput inspection workflows with real-time inference, comprehensive reporting, and enterprise-grade observability.

### 🏗️ Core Business Domain
- **Manufacturing Quality Control**: PCB, semiconductor, and component inspection
- **AI-Powered Defect Detection**: Real-time ML inference using NVIDIA Triton
- **Production Workflows**: Lot tracking, station management, quality reporting
- **Enterprise Integration**: ERP systems, manufacturing execution systems (MES)

---

## 🚀 Technology Stack & Architecture

### **Primary Technologies**
```yaml
Backend Framework: FastAPI (Python 3.11+)
Database: PostgreSQL 15+ with TimescaleDB for time-series data
Message Broker: Apache Kafka with Schema Registry
ML Inference: NVIDIA Triton Inference Server
Container Orchestration: Kubernetes
Observability: OpenTelemetry + Grafana Stack (Prometheus, Tempo, Loki)
Security: OAuth2/JWT with fine-grained RBAC
API Design: OpenAPI 3.1 with comprehensive documentation
```

### **Architectural Patterns**
- **Event-Driven Architecture**: Kafka-based messaging with transactional outbox pattern
- **Microservices**: Domain-driven service boundaries with API Gateway
- **CQRS**: Command Query Responsibility Segregation for read/write optimization
- **Circuit Breaker**: Resilience patterns for external dependencies
- **Asynchronous Processing**: Long-running ML inference with job tracking

### **Critical Design Principles**
1. **Idempotency**: All mutations support Stripe-style idempotency keys
2. **Cursor-based Pagination**: Stable pagination for large datasets
3. **Fine-grained Security**: OAuth2 scopes for precise authorization
4. **Comprehensive Observability**: Distributed tracing, metrics, structured logging
5. **Production Resilience**: Rate limiting, circuit breakers, graceful degradation

---

## 📁 Project Structure

```
chip-quality-platform/
├── services/                    # Microservices implementation
│   ├── api-gateway/            # Kong/FastAPI API Gateway
│   ├── inspection-service/     # Core inspection management
│   ├── inference-service/      # ML inference coordination
│   ├── artifact-service/       # File storage and retrieval
│   └── report-service/         # Analytics and reporting
├── docs/                       # Comprehensive documentation
│   ├── architecture.md         # System architecture (1000+ lines)
│   ├── api/openapi.yaml       # Complete API specification
│   └── adr/                   # Architectural Decision Records
├── k8s/                       # Kubernetes manifests
├── monitoring/                # Observability configuration
├── tools/                     # Development and testing tools
└── .github/                   # GitHub workflows and instructions
```

---

## 🛠️ Development Guidelines

### **Code Quality Standards**

#### **Python Standards**
```python
# Use type hints consistently
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

# Follow dataclass/Pydantic model patterns
class InspectionCreate(BaseModel):
    lot_id: str = Field(..., min_length=1, max_length=100, pattern="^[A-Z0-9-]+$")
    chip_id: str = Field(..., min_length=1, max_length=100)
    inspection_type: InspectionType
    priority: int = Field(default=5, ge=1, le=10)
    metadata: Optional[Dict[str, Any]] = None

# Use dependency injection for services
class InspectionService:
    def __init__(
        self,
        db: DatabaseService,
        event_publisher: EventPublisher,
        artifact_service: ArtifactService
    ):
        self.db = db
        self.event_publisher = event_publisher
        self.artifact_service = artifact_service
```

#### **FastAPI Patterns**
```python
# Route organization and error handling
@router.post("/inspections", response_model=Inspection)
async def create_inspection(
    request: InspectionCreate,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    inspection_service: InspectionService = Depends()
) -> Inspection:
    """
    Create new inspection with idempotency support.
    
    - **lot_id**: Manufacturing lot identifier
    - **chip_id**: Individual chip/component identifier
    - **inspection_type**: Type of quality inspection
    """
    try:
        return await inspection_service.create_inspection(
            request, idempotency_key, current_user.id
        )
    except DuplicateInspectionError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
```

#### **Database Patterns**
```python
# Use SQLAlchemy 2.0+ async patterns
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.orm import selectinload

class InspectionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_inspection(self, inspection: InspectionCreate) -> Inspection:
        db_inspection = Inspection(
            id=uuid.uuid4(),
            lot_id=inspection.lot_id,
            chip_id=inspection.chip_id,
            status=InspectionStatus.PENDING,
            created_at=datetime.utcnow()
        )
        self.session.add(db_inspection)
        await self.session.commit()
        await self.session.refresh(db_inspection)
        return db_inspection
    
    async def get_by_id(self, inspection_id: uuid.UUID) -> Optional[Inspection]:
        result = await self.session.execute(
            select(Inspection)
            .options(selectinload(Inspection.defects))
            .where(Inspection.id == inspection_id)
        )
        return result.scalar_one_or_none()
```

### **Event-Driven Patterns**
```python
# Kafka event publishing
from dataclasses import dataclass
from enum import Enum

class EventType(str, Enum):
    INSPECTION_CREATED = "inspection.created"
    INFERENCE_COMPLETED = "inference.completed"
    DEFECT_DETECTED = "defect.detected"

@dataclass
class InspectionCreatedEvent:
    inspection_id: str
    lot_id: str
    chip_id: str
    inspection_type: str
    created_at: datetime
    metadata: Dict[str, Any]

# Event publisher service
class EventPublisher:
    async def publish(self, event_type: EventType, event_data: BaseModel):
        await self.kafka_producer.send(
            topic=f"chip-quality.{event_type.value}",
            key=event_data.inspection_id,
            value=event_data.model_dump_json()
        )
```

### **Error Handling Standards**
```python
# Custom exception hierarchy
class ChipQualityError(Exception):
    """Base exception for all chip quality platform errors."""
    
class ValidationError(ChipQualityError):
    """Data validation errors."""
    
class DuplicateInspectionError(ChipQualityError):
    """Inspection already exists for lot/chip/type combination."""
    
class InferenceTimeoutError(ChipQualityError):
    """ML inference operation timed out."""

# Structured error responses
@dataclass
class ErrorResponse:
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
```

---

## 🔒 Security Implementation

### **OAuth2/JWT Patterns**
```python
# Scope-based authorization
REQUIRED_SCOPES = {
    "create_inspection": ["inspections:write"],
    "trigger_inference": ["inference:execute"],
    "view_reports": ["reports:read"],
    "admin_functions": ["admin:manage"]
}

def require_scopes(required_scopes: List[str]):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not all(scope in current_user.scopes for scope in required_scopes):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

@require_scopes(["inspections:write"])
async def create_inspection(...):
    pass
```

### **Rate Limiting Implementation**
```python
# Token bucket rate limiting
from fastapi import Request
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, requests_per_minute: int = 100):
        self.requests_per_minute = requests_per_minute
        self.buckets: Dict[str, TokenBucket] = {}
    
    async def check_rate_limit(self, request: Request) -> bool:
        client_ip = request.client.host
        bucket = self.buckets.get(client_ip)
        if not bucket:
            bucket = TokenBucket(self.requests_per_minute)
            self.buckets[client_ip] = bucket
        return bucket.consume()
```

---

## 🧪 Testing Standards

### **Test Organization**
```python
# Test structure
tests/
├── unit/                   # Unit tests for individual components
├── integration/           # Integration tests for service interactions
├── e2e/                   # End-to-end API tests
└── load/                  # Performance and load tests

# Pytest patterns
import pytest
from httpx import AsyncClient
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_create_inspection_success():
    # Arrange
    mock_service = AsyncMock()
    mock_service.create_inspection.return_value = Inspection(
        id=uuid.uuid4(),
        lot_id="LOT-2025-001",
        status=InspectionStatus.PENDING
    )
    
    # Act
    async with AsyncClient(app=app) as client:
        response = await client.post(
            "/v1/inspections",
            json={
                "lot_id": "LOT-2025-001",
                "chip_id": "PCB-A1234",
                "inspection_type": "visual"
            },
            headers={"Authorization": "Bearer valid-token"}
        )
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["lot_id"] == "LOT-2025-001"
    assert data["status"] == "pending"
```

---

## 📊 Observability Implementation

### **OpenTelemetry Integration**
```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Tracing setup
tracer = trace.get_tracer(__name__)

class InspectionService:
    @tracer.start_as_current_span("inspection.create")
    async def create_inspection(self, request: InspectionCreate) -> Inspection:
        span = trace.get_current_span()
        span.set_attributes({
            "inspection.lot_id": request.lot_id,
            "inspection.type": request.inspection_type,
            "inspection.priority": request.priority
        })
        
        # Implementation
        inspection = await self.repository.create(request)
        
        span.set_attribute("inspection.id", str(inspection.id))
        return inspection
```

### **Structured Logging**
```python
import structlog

# Logging configuration
logger = structlog.get_logger()

class InspectionService:
    async def create_inspection(self, request: InspectionCreate) -> Inspection:
        logger.info(
            "inspection.create.started",
            lot_id=request.lot_id,
            chip_id=request.chip_id,
            inspection_type=request.inspection_type
        )
        
        try:
            inspection = await self.repository.create(request)
            logger.info(
                "inspection.create.completed",
                inspection_id=str(inspection.id),
                lot_id=request.lot_id
            )
            return inspection
        except Exception as e:
            logger.error(
                "inspection.create.failed",
                lot_id=request.lot_id,
                error=str(e),
                exc_info=True
            )
            raise
```

---

## 🚀 NVIDIA Triton Integration

### **Inference Client Patterns**
```python
import tritonclient.grpc as grpcclient
from tritonclient.utils import triton_to_np_dtype

class TritonInferenceClient:
    def __init__(self, triton_url: str = "triton-inference-server:8001"):
        self.client = grpcclient.InferenceServerClient(triton_url)
        self.model_metadata = self._load_model_metadata()
    
    async def detect_defects(
        self, 
        image_data: bytes, 
        model_name: str = "pcb_defect_detector_v2"
    ) -> List[DefectDetection]:
        # Prepare input tensors
        input_tensor = grpcclient.InferInput("INPUT", image_data.shape, "UINT8")
        input_tensor.set_data_from_numpy(image_data)
        
        # Configure output
        output_tensor = grpcclient.InferRequestedOutput("OUTPUT")
        
        # Run inference
        response = await self.client.infer(
            model_name=model_name,
            inputs=[input_tensor],
            outputs=[output_tensor]
        )
        
        # Process results
        return self._parse_inference_results(response)
```

---

## 📋 Database Conventions

### **Schema Patterns**
```sql
-- Follow naming conventions
CREATE TABLE inspections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lot_id VARCHAR(100) NOT NULL,
    chip_id VARCHAR(100) NOT NULL,
    inspection_type inspection_type_enum NOT NULL,
    status inspection_status_enum NOT NULL DEFAULT 'pending',
    priority INTEGER NOT NULL DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_inspection_per_chip UNIQUE (lot_id, chip_id, inspection_type)
);

-- Indexes for performance
CREATE INDEX idx_inspections_lot_id ON inspections(lot_id);
CREATE INDEX idx_inspections_status_created ON inspections(status, created_at DESC);
CREATE INDEX idx_inspections_metadata_gin ON inspections USING GIN(metadata);
```

### **Migration Patterns**
```python
# Alembic migration structure
"""Add inspection priority field

Revision ID: 003
Revises: 002
Create Date: 2025-10-30 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('inspections', 
        sa.Column('priority', sa.Integer(), nullable=False, server_default='5')
    )
    op.create_check_constraint(
        'priority_range', 
        'inspections', 
        'priority >= 1 AND priority <= 10'
    )

def downgrade():
    op.drop_constraint('priority_range', 'inspections')
    op.drop_column('inspections', 'priority')
```

---

## 🌐 API Design Principles

### **RESTful Conventions**
- Use standard HTTP methods and status codes
- Implement comprehensive error responses with structured format
- Support idempotency for all mutations using `Idempotency-Key` header
- Use cursor-based pagination for list endpoints
- Include correlation IDs for request tracing

### **Response Patterns**
```python
# Consistent response structure
{
    "data": [...],           # Actual response data
    "has_more": true,        # Pagination indicator
    "next_cursor": "...",    # Next page cursor
    "request_id": "req_...", # Request correlation ID
    "timestamp": "2025-10-30T10:30:00Z"
}

# Error response structure
{
    "error": {
        "code": "validation_error",
        "message": "Request validation failed",
        "details": {
            "field": "chip_id",
            "constraint": "must be alphanumeric, 3-50 characters"
        },
        "request_id": "req_1234567890abcdef",
        "timestamp": "2025-10-30T10:30:00.000Z"
    }
}
```

---

## 🔧 Development Workflow

### **Git Conventions**
```bash
# Branch naming
feature/ISSUE-123-add-defect-classification
bugfix/ISSUE-456-fix-inference-timeout
hotfix/ISSUE-789-security-patch

# Commit messages
feat(inspection): add priority field to inspection model
fix(inference): handle NVIDIA Triton connection timeout
docs(api): update OpenAPI specification for new endpoints
test(integration): add tests for artifact upload flow
```

### **Issue Implementation Process**
1. **Analysis Phase**: Read issue requirements and acceptance criteria
2. **Design Phase**: Review relevant ADRs and architecture documentation
3. **Implementation Phase**: Follow established patterns and conventions
4. **Testing Phase**: Write comprehensive unit and integration tests
5. **Documentation Phase**: Update API docs and code comments
6. **Review Phase**: Self-review against quality standards

---

## ⚡ Performance Guidelines

### **Database Optimization**
- Use appropriate indexes for query patterns
- Implement connection pooling with proper sizing
- Use TimescaleDB hypertables for time-series data
- Optimize N+1 queries with proper eager loading

### **Caching Strategies**
```python
# Redis caching for frequent lookups
from redis.asyncio import Redis

class CacheService:
    def __init__(self, redis: Redis):
        self.redis = redis
    
    async def get_inspection(self, inspection_id: str) -> Optional[Inspection]:
        cached = await self.redis.get(f"inspection:{inspection_id}")
        if cached:
            return Inspection.model_validate_json(cached)
        return None
    
    async def set_inspection(self, inspection: Inspection, ttl: int = 300):
        await self.redis.setex(
            f"inspection:{inspection.id}",
            ttl,
            inspection.model_dump_json()
        )
```

---

## 🎯 Implementation Priorities

When implementing features, prioritize in this order:
1. **Core Business Logic**: Inspection management, defect detection
2. **API Endpoints**: Following OpenAPI specification exactly
3. **Event Publishing**: Kafka integration for system integration
4. **Observability**: Logging, metrics, tracing
5. **Error Handling**: Comprehensive error responses
6. **Testing**: Unit, integration, and API tests
7. **Documentation**: Code comments and API documentation updates

---

## 🚨 Critical Requirements

### **Always Include**
- Comprehensive error handling with structured responses
- OpenTelemetry tracing spans for all operations
- Structured logging with correlation IDs
- Input validation using Pydantic models
- OAuth2 scope verification for protected endpoints
- Idempotency support for mutation operations
- Comprehensive type hints

### **Never Do**
- Hardcode configuration values
- Skip input validation
- Ignore error handling
- Return raw database exceptions
- Skip logging for important operations
- Implement blocking operations in async functions
- Create endpoints without proper authentication

---

## 📚 Key Documentation References

1. **Architecture**: `/docs/architecture.md` - Complete system architecture
2. **API Specification**: `/docs/api/openapi.yaml` - Authoritative API contract
3. **ADRs**: `/docs/adr/` - All architectural decisions
4. **Database Schema**: `/docs/database/` - Complete database design
5. **Security Model**: `/docs/security/` - Authentication and authorization
6. **Deployment**: `/k8s/` - Kubernetes deployment configurations

---

## 🎯 Success Criteria

Your implementation is successful when:
- ✅ All tests pass (unit, integration, e2e)
- ✅ API endpoints match OpenAPI specification exactly
- ✅ Proper error handling with structured responses
- ✅ Comprehensive observability integration
- ✅ Security requirements are met
- ✅ Code follows established patterns and conventions
- ✅ Performance meets requirements
- ✅ Documentation is updated and accurate

Remember: **Quality over speed**. Follow the patterns, test thoroughly, and ensure production readiness.