# Event Streaming Infrastructure

Comprehensive event streaming system using Apache Kafka for real-time data processing and system integration in the Chip Quality Platform.

## Overview

This module provides:
- **Event Producers**: Reliable event publishing with schema validation
- **Event Consumers**: Scalable event consumption with consumer groups
- **Schema Management**: Avro schema definitions with Schema Registry integration
- **Stream Processing**: Real-time event processing for analytics
- **Reliability Features**: Idempotency, dead letter queues, retry mechanisms

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Event Producer │────▶│  Apache Kafka    │────▶│ Event Consumer  │
│  (Service)      │     │  + Schema Reg    │     │ (Processor)     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │ Dead Letter  │
                        │   Queue      │
                        └──────────────┘
```

## Event Topics

### Inspection Events
**Topic**: `chip-quality.inspection.events`

Events for inspection lifecycle:
- `INSPECTION_CREATED` - New inspection initiated
- `INSPECTION_STARTED` - Inspection processing began
- `INSPECTION_COMPLETED` - Inspection finished successfully
- `INSPECTION_FAILED` - Inspection encountered error
- `DEFECT_DETECTED` - Defects found during inspection
- `QUALITY_ASSESSED` - Quality score calculated

### Manufacturing Events
**Topic**: `chip-quality.manufacturing.events`

Events for manufacturing operations:
- `BATCH_CREATED` - New manufacturing batch
- `LOT_CREATED` - New lot within batch
- `BATCH_COMPLETED` - Batch processing finished
- `PRODUCTION_MILESTONE` - Production milestone reached

### Quality Events
**Topic**: `chip-quality.quality.events`

Events for quality assessment:
- `QUALITY_ASSESSED` - Quality evaluation completed
- `THRESHOLD_VIOLATED` - Quality below threshold
- `ALERT_TRIGGERED` - Quality alert issued
- `COMPLIANCE_CHECK` - Compliance verification

### User Events
**Topic**: `chip-quality.user.events`

Events for user activities:
- `USER_LOGIN` - User authentication
- `USER_LOGOUT` - User session end
- `AUDIT_ACTION` - Auditable user action
- `PERMISSION_GRANTED` - Access granted

### System Events
**Topic**: `chip-quality.system.events`

Events for system operations:
- `SERVICE_STARTED` - Service initialization
- `SERVICE_STOPPED` - Service shutdown
- `HEALTH_CHECK` - Service health status
- `ERROR_OCCURRED` - System error

## Usage Examples

### Publishing Events

```python
from events.producers import InspectionEventProducer

# Initialize producer
async with InspectionEventProducer() as producer:
    # Publish inspection created event
    await producer.publish_inspection_created(
        inspection_id="INS-001",
        batch_id="BATCH-001",
        chip_id="CHIP-001",
        inspection_type="visual",
        metadata={"station": "A1"}
    )
    
    # Publish inspection completed event
    await producer.publish_inspection_completed(
        inspection_id="INS-001",
        batch_id="BATCH-001",
        chip_id="CHIP-001",
        inspection_type="visual",
        quality_score=0.95,
        defects=[
            {
                "defect_type": "scratch",
                "severity": "minor",
                "confidence": 0.85,
                "location": "corner"
            }
        ]
    )
```

### Consuming Events

```python
from events.consumers import AnalyticsConsumer

# Initialize consumer
consumer = AnalyticsConsumer()

# Define event handler
async def process_event(event_data, record):
    print(f"Processing: {event_data['event_type']}")
    print(f"Inspection: {event_data['inspection_id']}")

# Start consuming
await consumer.start()
await consumer.consume(handler=process_event)
```

### Batch Publishing

```python
async with InspectionEventProducer() as producer:
    events = [
        {"inspection_id": "INS-001", ...},
        {"inspection_id": "INS-002", ...},
        {"inspection_id": "INS-003", ...},
    ]
    
    await producer.publish_batch(
        events,
        key_fn=lambda e: e["inspection_id"]
    )
```

## Configuration

### Environment Variables

```bash
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_SECURITY_PROTOCOL=PLAINTEXT

# Schema Registry
SCHEMA_REGISTRY_URL=http://localhost:8081

# Consumer Configuration
KAFKA_GROUP_ID=my-consumer-group
KAFKA_AUTO_OFFSET_RESET=earliest
```

### Programmatic Configuration

```python
from events.utils import KafkaConfig

config = KafkaConfig(
    bootstrap_servers="kafka:29092",
    acks="all",
    compression_type="snappy",
    enable_idempotence=True,
    group_id="analytics-group"
)
```

## Schema Management

### Schema Registration

```python
from events.utils import SchemaRegistry
from pathlib import Path

registry = SchemaRegistry(url="http://localhost:8081")

# Register schema
schema_path = Path("schemas/inspection.avsc")
schema = await registry.load_schema_from_file(schema_path)
schema_id = await registry.register_schema("inspection-value", schema)
```

### Schema Evolution

All schemas support backward-compatible evolution:
- Add optional fields with defaults
- Remove fields (consumers must handle missing fields)
- Change field types (with compatible types)

## Reliability Features

### Idempotency

All producers are configured with `enable_idempotence=True` to prevent duplicate messages.

### Dead Letter Queue

Failed messages are automatically sent to topic-specific DLQ:
- Original message preserved
- Error details included
- Timestamp of failure recorded

### Retry Mechanism

Consumers support automatic retry with exponential backoff:

```python
await consumer.consume_with_retry(
    handler=process_event,
    max_retries=3,
    retry_delay=1.0  # Exponential backoff
)
```

### Exactly-Once Semantics

- Producer idempotency enabled
- Manual offset commits after processing
- Transactional message processing support

## Monitoring

### Producer Metrics

```python
metrics = producer.get_metrics()
# {
#   "messages_sent": 1000,
#   "messages_failed": 5,
#   "total_bytes_sent": 500000,
#   "is_started": True
# }
```

### Consumer Metrics

```python
metrics = consumer.get_metrics()
# {
#   "messages_consumed": 950,
#   "messages_processed": 945,
#   "messages_failed": 5,
#   "total_bytes_consumed": 475000,
#   "is_running": True
# }
```

## Testing

Run unit tests:
```bash
pytest services/shared/events/tests/
```

Run integration tests (requires Kafka):
```bash
docker-compose up -d kafka schema-registry
pytest services/shared/events/tests/ -m integration
```

## Performance

### Producer Performance
- **Throughput**: 10,000+ messages/second
- **Latency**: <10ms P99 for publish
- **Compression**: 60-70% size reduction with Snappy

### Consumer Performance
- **Throughput**: 10,000+ messages/second per consumer
- **Latency**: <100ms P95 end-to-end
- **Scaling**: Horizontal scaling with consumer groups

## Best Practices

1. **Use async context managers** for automatic resource cleanup
2. **Partition by key** for ordered message processing
3. **Monitor consumer lag** to detect processing bottlenecks
4. **Set appropriate timeouts** based on processing complexity
5. **Handle schema evolution** gracefully with default values
6. **Log all events** with correlation IDs for tracing

## Troubleshooting

### Consumer Lag
```python
# Check consumer position
position = await consumer.consumer.position(partition)
end_offset = await consumer.consumer.end_offsets([partition])
lag = end_offset - position
```

### Schema Validation Failures
- Verify schema compatibility with Schema Registry
- Check required fields are present
- Validate data types match schema

### Connection Issues
- Verify Kafka broker accessibility
- Check security credentials
- Validate network connectivity

## Development

### Adding New Event Types

1. Update Avro schema with new event type
2. Add producer method for new event
3. Update consumers to handle new event
4. Register updated schema with Schema Registry
5. Add tests for new event type

### Schema Evolution Guidelines

- Always add default values for new fields
- Never remove required fields
- Test compatibility before deployment
- Version schemas appropriately

## References

- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [Confluent Schema Registry](https://docs.confluent.io/platform/current/schema-registry/)
- [Avro Specification](https://avro.apache.org/docs/current/spec.html)
- [Event Sourcing Pattern](https://martinfowler.com/eaaDev/EventSourcing.html)
