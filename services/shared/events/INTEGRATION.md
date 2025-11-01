# Event Streaming Integration Guide

This guide shows how to integrate the event streaming system with existing services in the Chip Quality Platform.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Service Integration](#service-integration)
3. [Publishing Events](#publishing-events)
4. [Consuming Events](#consuming-events)
5. [Testing](#testing)
6. [Deployment](#deployment)
7. [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites

```bash
# Start Kafka infrastructure
docker-compose up -d kafka schema-registry zookeeper
```

### Installation

The event streaming package is part of the shared module:

```python
# Add to your service's requirements or imports
from events.producers import InspectionEventProducer
from events.consumers import AnalyticsConsumer
from events.utils import KafkaConfig
```

### Configuration

Set environment variables:

```bash
export KAFKA_BOOTSTRAP_SERVERS=kafka:29092
export SCHEMA_REGISTRY_URL=http://schema-registry:8081
```

## Service Integration

### Inspection Service Integration

Add event publishing to the inspection service workflow:

```python
# services/inspection-svc/app/services/inspection_service.py

from events.producers import InspectionEventProducer
from events.utils import KafkaConfig

class InspectionService:
    def __init__(self):
        self.kafka_config = KafkaConfig.from_env()
        self.event_producer = None
    
    async def initialize(self):
        """Initialize event producer on service startup."""
        self.event_producer = InspectionEventProducer(self.kafka_config)
        await self.event_producer.start()
    
    async def shutdown(self):
        """Cleanup on service shutdown."""
        if self.event_producer:
            await self.event_producer.stop()
    
    async def create_inspection(self, inspection_data):
        """Create inspection and publish event."""
        # Create inspection in database
        inspection = await self.db.create_inspection(inspection_data)
        
        # Publish inspection created event
        await self.event_producer.publish_inspection_created(
            inspection_id=inspection.inspection_id,
            batch_id=str(inspection.lot_id),
            chip_id=inspection.chip_id,
            inspection_type=inspection.inspection_type.value,
            metadata={
                "station": inspection.station_id,
                "created_by": str(inspection.inspector_id)
            }
        )
        
        return inspection
    
    async def complete_inspection(self, inspection_id, results):
        """Complete inspection and publish event."""
        # Update inspection in database
        inspection = await self.db.update_inspection(
            inspection_id,
            status="completed",
            results=results
        )
        
        # Extract defects
        defects = []
        for defect in results.get("defects", []):
            defects.append({
                "defect_type": defect["type"],
                "severity": defect["severity"],
                "confidence": defect["confidence"],
                "location": defect["location"]
            })
        
        # Publish inspection completed event
        await self.event_producer.publish_inspection_completed(
            inspection_id=inspection.inspection_id,
            batch_id=str(inspection.lot_id),
            chip_id=inspection.chip_id,
            inspection_type=inspection.inspection_type.value,
            quality_score=results.get("quality_score"),
            defects=defects,
            metadata={
                "processing_time_ms": str(results.get("processing_time"))
            }
        )
        
        return inspection
```

### FastAPI Lifespan Integration

```python
# services/inspection-svc/app/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.services.inspection_service import InspectionService

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    inspection_service = InspectionService()
    await inspection_service.initialize()
    app.state.inspection_service = inspection_service
    
    yield
    
    # Shutdown
    await inspection_service.shutdown()

app = FastAPI(lifespan=lifespan)
```

### Dependency Injection

```python
# services/inspection-svc/app/core/dependencies.py

from fastapi import Depends, Request
from app.services.inspection_service import InspectionService

async def get_inspection_service(request: Request) -> InspectionService:
    """Get inspection service from app state."""
    return request.app.state.inspection_service
```

### Route Integration

```python
# services/inspection-svc/app/routers/inspections.py

from fastapi import APIRouter, Depends
from app.core.dependencies import get_inspection_service
from app.services.inspection_service import InspectionService

router = APIRouter(prefix="/inspections", tags=["inspections"])

@router.post("/")
async def create_inspection(
    data: InspectionCreate,
    service: InspectionService = Depends(get_inspection_service)
):
    """Create new inspection with event publishing."""
    inspection = await service.create_inspection(data)
    return inspection

@router.post("/{inspection_id}/complete")
async def complete_inspection(
    inspection_id: str,
    results: InspectionResults,
    service: InspectionService = Depends(get_inspection_service)
):
    """Complete inspection with event publishing."""
    inspection = await service.complete_inspection(inspection_id, results)
    return inspection
```

## Publishing Events

### Example: Publish Quality Events

```python
from events.producers import QualityEventProducer

class QualityService:
    def __init__(self):
        self.event_producer = QualityEventProducer()
    
    async def initialize(self):
        await self.event_producer.start()
    
    async def assess_quality(self, inspection_id, batch_id, quality_score):
        """Assess quality and publish events."""
        threshold = 0.85
        pass_fail = quality_score >= threshold
        
        # Publish quality assessed event
        await self.event_producer.publish_quality_assessed(
            inspection_id=inspection_id,
            batch_id=batch_id,
            quality_score=quality_score,
            pass_fail=pass_fail,
            threshold=threshold
        )
        
        # If failed, publish threshold violation
        if not pass_fail:
            alert_level = "WARNING" if quality_score > 0.7 else "CRITICAL"
            await self.event_producer.publish_threshold_violated(
                inspection_id=inspection_id,
                batch_id=batch_id,
                quality_score=quality_score,
                threshold=threshold,
                alert_level=alert_level
            )
```

### Example: Batch Publishing

```python
async def publish_multiple_inspections(inspections):
    """Batch publish inspection events."""
    async with InspectionEventProducer() as producer:
        events = []
        for inspection in inspections:
            event = {
                "event_type": "INSPECTION_CREATED",
                "inspection_id": inspection.id,
                "batch_id": inspection.batch_id,
                "chip_id": inspection.chip_id,
                "inspection_type": inspection.type,
                "status": "pending",
                "quality_score": None,
                "defects": [],
                "metadata": {}
            }
            events.append(event)
        
        await producer.publish_batch(
            events,
            key_fn=lambda e: e["inspection_id"]
        )
```

## Consuming Events

### Background Consumer Service

Create a dedicated consumer service:

```python
# services/event-processor/app/main.py

import asyncio
from events.consumers import AnalyticsConsumer, NotificationConsumer
from events.utils import KafkaConfig

class EventProcessorService:
    def __init__(self):
        self.config = KafkaConfig.from_env()
        self.analytics_consumer = AnalyticsConsumer(self.config)
        self.notification_consumer = NotificationConsumer(self.config)
        self.is_running = False
    
    async def start(self):
        """Start all consumers."""
        self.is_running = True
        
        # Start consumers
        await self.analytics_consumer.start()
        await self.notification_consumer.start()
        
        # Run consumers concurrently
        await asyncio.gather(
            self._run_analytics(),
            self._run_notifications()
        )
    
    async def _run_analytics(self):
        """Run analytics consumer."""
        while self.is_running:
            try:
                await self.analytics_consumer.consume_with_retry(
                    handler=self.analytics_consumer.process_event,
                    max_retries=3
                )
            except Exception as e:
                print(f"Analytics consumer error: {e}")
                await asyncio.sleep(5)
    
    async def _run_notifications(self):
        """Run notification consumer."""
        while self.is_running:
            try:
                await self.notification_consumer.consume_with_retry(
                    handler=self.notification_consumer.process_event,
                    max_retries=3
                )
            except Exception as e:
                print(f"Notification consumer error: {e}")
                await asyncio.sleep(5)
    
    async def stop(self):
        """Stop all consumers."""
        self.is_running = False
        await self.analytics_consumer.stop()
        await self.notification_consumer.stop()

if __name__ == "__main__":
    service = EventProcessorService()
    try:
        asyncio.run(service.start())
    except KeyboardInterrupt:
        asyncio.run(service.stop())
```

### Custom Event Handler

```python
from events.consumers import BaseEventConsumer
from pathlib import Path
import json

class CustomConsumer(BaseEventConsumer):
    def __init__(self):
        schema_path = Path(__file__).parent / "schemas" / "inspection.avsc"
        with open(schema_path) as f:
            schema = json.load(f)
        
        super().__init__(
            topics=["chip-quality.inspection.events"],
            group_id="custom-processor",
            schema=schema
        )
    
    async def process_event(self, event_data, record):
        """Custom event processing logic."""
        event_type = event_data["event_type"]
        
        if event_type == "INSPECTION_COMPLETED":
            # Custom business logic
            await self._process_completed(event_data)
        
        # Commit after successful processing
        await self.consumer.commit()
    
    async def _process_completed(self, event_data):
        """Process completed inspection."""
        print(f"Processing: {event_data['inspection_id']}")
        # Add your custom logic here
```

## Testing

### Unit Tests

```python
# tests/unit/test_event_integration.py

import pytest
from events.producers import InspectionEventProducer
from events.utils import KafkaConfig

@pytest.mark.asyncio
async def test_publish_inspection_event():
    """Test publishing inspection event."""
    config = KafkaConfig(bootstrap_servers="localhost:9092")
    producer = InspectionEventProducer(config)
    
    # Note: This requires Kafka to be running
    try:
        await producer.start()
        
        await producer.publish_inspection_created(
            inspection_id="TEST-001",
            batch_id="BATCH-TEST",
            chip_id="CHIP-TEST",
            inspection_type="visual"
        )
        
        metrics = producer.get_metrics()
        assert metrics["messages_sent"] > 0
    finally:
        await producer.stop()
```

### Integration Tests

```python
# tests/integration/test_event_flow.py

import pytest
import asyncio
from events.producers import InspectionEventProducer
from events.consumers import AnalyticsConsumer

@pytest.mark.integration
@pytest.mark.asyncio
async def test_end_to_end_event_flow():
    """Test complete event flow from producer to consumer."""
    producer = InspectionEventProducer()
    consumer = AnalyticsConsumer()
    
    events_received = []
    
    async def capture_event(event_data, record):
        events_received.append(event_data)
    
    try:
        # Start producer and consumer
        await producer.start()
        await consumer.start()
        
        # Publish event
        await producer.publish_inspection_created(
            inspection_id="INT-TEST-001",
            batch_id="BATCH-INT",
            chip_id="CHIP-INT",
            inspection_type="visual"
        )
        
        # Consume with timeout
        try:
            await asyncio.wait_for(
                consumer.consume(handler=capture_event, max_messages=1),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            pass
        
        # Verify event was received
        assert len(events_received) > 0
        assert events_received[0]["inspection_id"] == "INT-TEST-001"
    finally:
        await producer.stop()
        await consumer.stop()
```

## Deployment

### Docker Compose Integration

The event streaming system is already configured in `docker-compose.yml`:

```yaml
services:
  kafka:
    image: confluentinc/cp-kafka:latest
    environment:
      KAFKA_BOOTSTRAP_SERVERS: kafka:29092
  
  schema-registry:
    image: confluentinc/cp-schema-registry:latest
    environment:
      SCHEMA_REGISTRY_KAFKASTORE_BOOTSTRAP_SERVERS: kafka:29092
```

### Service Configuration

Add to service environment variables:

```yaml
inspection-service:
  environment:
    - KAFKA_BOOTSTRAP_SERVERS=kafka:29092
    - SCHEMA_REGISTRY_URL=http://schema-registry:8081
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: event-processor
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: event-processor
        image: chip-quality/event-processor:latest
        env:
        - name: KAFKA_BOOTSTRAP_SERVERS
          value: "kafka-service:9092"
        - name: SCHEMA_REGISTRY_URL
          value: "http://schema-registry:8081"
```

## Troubleshooting

### Producer Issues

**Problem**: Events not being published

```python
# Check producer metrics
metrics = producer.get_metrics()
print(f"Failed messages: {metrics['messages_failed']}")

# Check Kafka connectivity
from events.utils import KafkaClientManager
manager = KafkaClientManager()
is_healthy = await manager.health_check()
```

### Consumer Issues

**Problem**: Consumer lag increasing

```python
# Monitor consumer lag
metrics = consumer.get_metrics()
print(f"Consumed: {metrics['messages_consumed']}")
print(f"Processed: {metrics['messages_processed']}")
print(f"Failed: {metrics['messages_failed']}")
```

### Schema Issues

**Problem**: Schema validation failures

```python
# Test schema validation
from events.utils.serialization import AvroSerializer
serializer = AvroSerializer(schema)

is_valid = serializer.validate(event_data)
if not is_valid:
    print("Validation failed - check required fields")
```

### Connection Issues

```bash
# Test Kafka connectivity
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Check Schema Registry
curl http://localhost:8081/subjects
```

## Best Practices

1. **Always use async context managers** for producers
2. **Commit offsets manually** for exactly-once semantics
3. **Handle errors gracefully** with retry logic
4. **Monitor consumer lag** to detect processing issues
5. **Use partition keys** for ordered processing
6. **Log correlation IDs** for distributed tracing
7. **Test with real Kafka** in integration tests
8. **Version schemas carefully** to maintain compatibility

## Next Steps

1. Integrate event publishing in inspection service
2. Deploy event processor service
3. Monitor event throughput and lag
4. Set up alerting for failed messages
5. Implement custom consumers as needed
