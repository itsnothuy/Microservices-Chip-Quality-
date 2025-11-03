# 🤖 Coding Agent Instructions for Auto-Closing Issues

## 🎯 **CRITICAL: Auto-Close Requirements**

To ensure your PR automatically closes the issue when merged to main, you **MUST** follow these requirements:

### ⚠️ **MANDATORY REQUIREMENT #1: Issue Reference**
**INCLUDE THIS EXACT FORMAT in your PR title or description:**

```markdown
Closes #005
```

Replace `#005` with the actual issue number. Use one of these keywords:
- `Closes #XXX` ✅ **RECOMMENDED**
- `Fixes #XXX` ✅ 
- `Resolves #XXX` ✅

### ⚠️ **MANDATORY REQUIREMENT #2: Quality Validation**
Your implementation must achieve **≥80% quality score** to auto-close.

---

## 📋 **Complete Implementation Checklist**

### **Before Starting Implementation:**

#### ✅ **Step 1: Read Issue Specification**
- Read the entire issue markdown file thoroughly
- Understand all acceptance criteria
- Review the implementation structure
- Check dependencies and references

#### ✅ **Step 2: Use PR Template**
- Use the issue implementation PR template in `.github/PULL_REQUEST_TEMPLATE/issue-implementation.md`
- Fill in the issue reference: `Closes #XXX`

#### ✅ **Step 3: Follow Project Conventions**
Follow the patterns in `.github/copilot-instructions.md`:

```python
# Type hints are MANDATORY
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

# Use Pydantic models for validation
class InspectionCreate(BaseModel):
    lot_id: str = Field(..., min_length=1, max_length=100)
    chip_id: str = Field(..., min_length=1, max_length=100)
    
# Follow dependency injection pattern
async def create_inspection(
    request: InspectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> Inspection:
    pass

# Include comprehensive error handling
try:
    result = await service.create_inspection(request)
    return result
except ValidationError as e:
    raise HTTPException(status_code=422, detail=str(e))
```

### **During Implementation:**

#### ✅ **File Structure Requirements**
Create **ALL** files specified in the issue implementation structure:

```python
# Example for Issue #005 (Event Streaming):
services/shared/events/
├── __init__.py                    # ⚠️ REQUIRED
├── schemas/
│   ├── __init__.py               # ⚠️ REQUIRED
│   ├── manufacturing.avsc        # ⚠️ REQUIRED
│   └── inspection.avsc           # ⚠️ REQUIRED
├── producers/
│   ├── __init__.py               # ⚠️ REQUIRED
│   ├── base_producer.py          # ⚠️ REQUIRED
│   └── inspection_producer.py    # ⚠️ REQUIRED
```

#### ✅ **Code Quality Requirements**
```python
# 1. ALWAYS include comprehensive type hints
def process_events(events: List[Dict[str, Any]]) -> Optional[ProcessingResult]:
    pass

# 2. ALWAYS include docstrings
def create_producer(topic: str) -> KafkaProducer:
    """
    Create a Kafka producer for the specified topic.
    
    Args:
        topic: Kafka topic name
        
    Returns:
        Configured Kafka producer instance
    """
    pass

# 3. ALWAYS include error handling
try:
    result = await kafka_producer.send(topic, message)
    return result
except KafkaError as e:
    logger.error(f"Failed to send message: {e}")
    raise ProcessingError(f"Message delivery failed: {e}")

# 4. ALWAYS use structured logging
import structlog
logger = structlog.get_logger()

logger.info(
    "event.published",
    topic=topic,
    event_type=event.type,
    correlation_id=event.correlation_id
)
```

#### ✅ **Testing Requirements**
Create comprehensive tests with **≥95% coverage**:

```python
# Unit tests - REQUIRED
tests/unit/test_event_streaming.py

# Integration tests - REQUIRED  
tests/integration/test_kafka_integration.py

# Performance tests - REQUIRED
tests/performance/test_streaming_performance.py
```

#### ✅ **API Implementation**
Follow OpenAPI specification exactly:

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List

router = APIRouter(prefix="/api/v1/events", tags=["events"])

@router.post("/publish", response_model=EventResponse)
async def publish_event(
    event: EventCreate,
    current_user: User = Depends(get_current_user)
) -> EventResponse:
    """Publish event to Kafka topic."""
    pass

@router.get("/topics", response_model=List[TopicInfo])
async def list_topics() -> List[TopicInfo]:
    """List available Kafka topics."""
    pass
```

### **Validation Prevention:**

#### ❌ **AVOID These Common Failures**

```python
# ❌ DON'T: Missing type hints
def process_data(data):
    return data

# ✅ DO: Include type hints
def process_data(data: Dict[str, Any]) -> ProcessedData:
    return ProcessedData(**data)

# ❌ DON'T: Missing error handling  
result = await risky_operation()

# ✅ DO: Comprehensive error handling
try:
    result = await risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise ServiceError(f"Processing failed: {e}")

# ❌ DON'T: Missing __init__.py files
# ✅ DO: Include __init__.py in every package

# ❌ DON'T: Incorrect import paths
from models import User  # Wrong

# ✅ DO: Use absolute imports
from services.shared.models import User  # Correct
```

---

## 🎯 **Issue-Specific Implementation Guides**

### **For Issue #005: Event Streaming with Kafka**

#### **Core Requirements:**
1. **Kafka Integration**: Complete producer/consumer implementation
2. **Avro Schemas**: Schema definitions for all event types
3. **Event Publishing**: Reliable event publishing for platform activities
4. **Stream Processing**: Real-time analytics and processing
5. **Error Handling**: Dead letter queues and retry mechanisms

#### **Key Files to Implement:**
```python
# CRITICAL: These files MUST exist for validation to pass
services/shared/events/schemas/inspection.avsc
services/shared/events/producers/base_producer.py
services/shared/events/producers/inspection_producer.py
services/shared/events/consumers/analytics_consumer.py
services/shared/events/processors/stream_processor.py
services/event-processor/app/main.py
services/event-processor/app/routers/events.py
```

#### **Dependencies to Install:**
```toml
kafka-python = "^2.0.2"
confluent-kafka = "^2.3.0" 
avro = "^1.11.3"
fastavro = "^1.9.0"
```

### **For Issue #006: Observability & Monitoring**

#### **Core Requirements:**
1. **OpenTelemetry**: Distributed tracing implementation
2. **Prometheus Metrics**: Business and technical metrics
3. **Structured Logging**: Centralized logging with correlation IDs
4. **Health Checks**: Service and dependency monitoring
5. **Grafana Dashboards**: Real-time operational dashboards

#### **Key Files to Implement:**
```python
services/shared/observability/tracing/tracer.py
services/shared/observability/metrics/business_metrics.py
services/shared/observability/health/checks.py
monitoring/grafana/dashboards/quality.json
monitoring/prometheus/alerts/quality.yml
```

### **For Issue #007: Artifact Management**

#### **Core Requirements:**
1. **MinIO Integration**: Object storage for file management
2. **File Processing**: Image processing and metadata extraction
3. **Search & Discovery**: Full-text search capabilities
4. **Version Control**: File versioning and history
5. **Security**: Access control and virus scanning

### **For Issue #008: Quality Reporting & Analytics**

#### **Core Requirements:**
1. **Report Generation**: PDF/Excel report creation
2. **Statistical Analytics**: SPC charts and quality metrics
3. **Dashboard APIs**: Real-time dashboard data
4. **FDA Compliance**: 21 CFR Part 11 compliant reports
5. **Scheduled Reports**: Automated report generation

---

## 🚀 **PR Creation Checklist**

### **Before Creating PR:**

- [ ] All files from issue structure implemented
- [ ] Type hints added to all functions
- [ ] Error handling implemented
- [ ] Tests written with ≥95% coverage  
- [ ] Docstrings added to all public functions
- [ ] Import paths use absolute imports
- [ ] No syntax errors or Unicode characters in tests

### **When Creating PR:**

- [ ] Use issue implementation PR template
- [ ] Include `Closes #XXX` in title or description
- [ ] Fill out all template sections
- [ ] List all implemented acceptance criteria
- [ ] Document any design decisions

### **After Creating PR:**

- [ ] Verify GitHub Actions workflow runs
- [ ] Check validation passes with ≥80% score
- [ ] Respond to any validation failures
- [ ] Wait for auto-close after merge

---

## 🔍 **Troubleshooting Validation Failures**

### **Common Issues & Solutions:**

#### **Import Errors:**
```bash
# ❌ Error: ModuleNotFoundError: No module named 'database'
# ✅ Fix: Use correct import path
from services.shared.database.base import BaseModel
```

#### **Missing Files:**
```bash
# ❌ Error: Missing required files: ['__init__.py', 'main.py']
# ✅ Fix: Create all files from issue structure
```

#### **Test Failures:**
```bash
# ❌ Error: ImportError: No module named 'pytest_xdist'  
# ✅ Fix: Already resolved in environment
```

#### **API Contract Errors:**
```bash
# ❌ Error: No FastAPI router found
# ✅ Fix: Ensure routers are properly defined:

from fastapi import APIRouter
router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "healthy"}
```

---

## 📞 **Success Verification**

### **How to Verify Auto-Close Will Work:**

1. **Check Issue Reference:**
   ```bash
   # In PR title or description, verify you have:
   "Closes #005" or "Fixes #005" or "Resolves #005"
   ```

2. **Run Validation Locally:**
   ```bash
   source venv/bin/activate
   python tools/quality/validate-implementation.py \
     --issue issues/005-event-streaming-kafka.md \
     --output validation-005.json
   ```

3. **Verify Quality Score:**
   ```json
   {
     "quality_score": 85.0,  // Must be ≥80%
     "is_complete": true
   }
   ```

### **Expected Auto-Close Flow:**

1. **PR Created** → Contains "Closes #005"
2. **PR Merged** → Triggers auto-close workflow  
3. **Validation Runs** → Checks quality score ≥80%
4. **Issue Closes** → Automatically closes if validation passes

---

## ⚠️ **Final Reminders**

- **Issue Reference**: Must include `Closes #XXX`
- **Quality Score**: Must achieve ≥80%
- **File Structure**: Must match issue specification exactly
- **Type Hints**: Required on all functions
- **Error Handling**: Must be comprehensive
- **Tests**: Must achieve ≥95% coverage

**Follow these instructions exactly and your issue will auto-close successfully!** 🎉