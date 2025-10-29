# ADR-004: Event-Driven Architecture with Apache Kafka

## Status
Accepted

## Context
The chip quality inspection platform requires loose coupling between microservices, reliable message delivery, and the ability to scale components independently. Traditional synchronous REST communication creates tight coupling and makes it difficult to handle peak loads during inspection batches.

## Decision
We will implement an event-driven architecture using Apache Kafka as the primary message broker with the following patterns:

### Event Design Patterns
- **Event Sourcing**: Store all state changes as immutable events
- **CQRS**: Separate command and query responsibilities
- **Saga Pattern**: Manage distributed transactions across services
- **Event Carried State Transfer**: Include sufficient data in events to reduce service coupling

### Topic Strategy

#### Core Topics
```yaml
# Topic naming convention: <domain>.<entity>.<action>
inspection.lifecycle:
  partitions: 12
  replication_factor: 3
  retention_ms: 2592000000  # 30 days
  cleanup_policy: delete

inference.workflow:
  partitions: 8
  replication_factor: 3
  retention_ms: 604800000   # 7 days
  cleanup_policy: delete

artifact.management:
  partitions: 6
  replication_factor: 3
  retention_ms: 7776000000  # 90 days
  cleanup_policy: delete

audit.events:
  partitions: 4
  replication_factor: 3
  retention_ms: 31536000000 # 1 year
  cleanup_policy: compact
```

### Event Schema Design

#### Standard Event Envelope
```json
{
  "event_type": "string",
  "event_id": "uuid",
  "timestamp": "2025-01-20T10:30:00.000Z",
  "trace_id": "distributed_trace_id",
  "source_service": "string",
  "schema_version": "1.0.0",
  "payload": {
    // Event-specific data
  }
}
```

#### Schema Evolution Strategy
- **Backward Compatibility**: New fields optional, existing fields immutable
- **Schema Registry**: Confluent Schema Registry with Avro schemas
- **Versioning**: Semantic versioning with major.minor.patch format
- **Migration Path**: Dual-write pattern during schema transitions

### Producer Patterns

#### Transactional Outbox Pattern
```python
@transactional
async def create_inspection(inspection_data: InspectionCreate) -> Inspection:
    # 1. Write to database
    inspection = await db.inspections.create(inspection_data)
    
    # 2. Write event to outbox table
    event = InspectionCreatedEvent(
        inspection_id=inspection.id,
        lot_id=inspection.lot_id,
        chip_id=inspection.chip_id,
        created_at=inspection.created_at
    )
    await db.outbox.create(event)
    
    # 3. Background worker publishes from outbox
    return inspection
```

#### Idempotent Producers
```python
async def publish_event(topic: str, event: BaseEvent):
    producer_config = {
        'enable.idempotence': True,
        'acks': 'all',
        'retries': 2147483647,
        'max.in.flight.requests.per.connection': 5,
        'delivery.timeout.ms': 120000
    }
    await kafka_producer.send(
        topic=topic,
        key=event.event_id,
        value=event.json(),
        headers={'idempotency-key': event.event_id}
    )
```

### Consumer Patterns

#### At-Least-Once Processing
```python
@kafka_consumer(
    topic='inspection.lifecycle',
    group_id='inference-service',
    auto_offset_reset='earliest',
    enable_auto_commit=False
)
async def handle_inspection_event(message: KafkaMessage):
    try:
        # 1. Process message
        event = InspectionEvent.parse_raw(message.value)
        await process_inspection_created(event)
        
        # 2. Commit offset only after successful processing
        await message.commit()
        
    except Exception as e:
        logger.error(f"Failed to process message: {e}")
        # Dead letter queue handling
        await send_to_dlq(message, str(e))
        await message.commit()  # Commit to prevent reprocessing
```

#### Consumer Group Strategy
- **Parallel Processing**: Multiple consumers per service for scalability
- **Partition Affinity**: Sticky assignment for cache locality
- **Rebalancing**: Graceful shutdown with in-flight message completion
- **Monitoring**: Consumer lag alerts and partition assignment tracking

### Dead Letter Queue (DLQ) Handling

#### DLQ Topics
```yaml
inspection.lifecycle.dlq:
  partitions: 4
  replication_factor: 3
  retention_ms: 7776000000  # 90 days for debugging

inference.workflow.dlq:
  partitions: 4
  replication_factor: 3
  retention_ms: 2592000000  # 30 days
```

#### DLQ Processing Strategy
```python
async def dlq_processor():
    """Background service to analyze and reprocess DLQ messages"""
    while True:
        messages = await dlq_consumer.poll(timeout_ms=1000)
        for message in messages:
            error_info = extract_error_info(message.headers)
            
            if should_retry(error_info):
                await republish_to_main_topic(message)
            else:
                await alert_operations_team(message, error_info)
```

## Consequences

### Positive
- **Loose Coupling**: Services communicate through events, not direct API calls
- **Scalability**: Independent scaling of producers and consumers
- **Resilience**: Message persistence and replay capabilities
- **Audit Trail**: Complete event history for compliance and debugging
- **Flexibility**: Easy to add new consumers without changing producers
- **Performance**: Asynchronous processing improves response times

### Negative
- **Complexity**: Additional infrastructure and operational overhead
- **Eventual Consistency**: Need to handle out-of-order and delayed events
- **Debugging Difficulty**: Distributed tracing required for request flows
- **Storage Overhead**: Event logs consume significant disk space
- **Schema Management**: Need governance for schema evolution

### Mitigations
- **Monitoring**: Comprehensive metrics for lag, throughput, and errors
- **Documentation**: Clear event schemas and consumer contracts
- **Testing**: Event-driven integration tests and chaos engineering
- **Tooling**: Kafka management tools and schema registry UI
- **Training**: Team education on event-driven patterns

## Implementation Plan

### Phase 1: Foundation (Week 1-2)
- Deploy Kafka cluster with proper configuration
- Implement basic producer/consumer patterns
- Set up Schema Registry and monitoring

### Phase 2: Core Events (Week 3-4)
- Implement inspection lifecycle events
- Add inference workflow events
- Build outbox pattern for transactional consistency

### Phase 3: Advanced Patterns (Week 5-6)
- Implement DLQ handling and retry logic
- Add distributed tracing correlation
- Performance optimization and load testing

### Phase 4: Production Hardening (Week 7-8)
- Disaster recovery procedures
- Security hardening (SSL, SASL)
- Operational runbooks and alerting

## Monitoring and Observability

### Key Metrics
```yaml
Producer Metrics:
  - kafka_producer_request_latency_avg
  - kafka_producer_batch_size_avg
  - kafka_producer_buffer_pool_wait_time

Consumer Metrics:
  - kafka_consumer_lag_sum
  - kafka_consumer_records_consumed_rate
  - kafka_consumer_fetch_latency_avg

Topic Metrics:
  - kafka_topic_partitions
  - kafka_topic_under_replicated_partitions
  - kafka_topic_bytes_in_per_sec
```

### Alerting Rules
```yaml
# Consumer lag alert
groups:
- name: kafka.rules
  rules:
  - alert: HighConsumerLag
    expr: kafka_consumer_lag_sum > 1000
    for: 5m
    annotations:
      summary: "High consumer lag detected"
      description: "Consumer group {{ $labels.group }} has lag of {{ $value }}"

  - alert: ProducerErrors
    expr: rate(kafka_producer_record_error_rate[5m]) > 0.01
    for: 2m
    annotations:
      summary: "High producer error rate"
```

## Security Considerations

### Authentication & Authorization
- **SASL/SCRAM**: Username/password authentication
- **ACLs**: Topic-level permissions for services
- **TLS Encryption**: In-transit encryption for all connections
- **Schema Registry Security**: Role-based access to schemas

### Network Security
```yaml
# Kafka network policies
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: kafka-access
spec:
  podSelector:
    matchLabels:
      app: kafka
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: chip-quality
    ports:
    - protocol: TCP
      port: 9092
```

## Testing Strategy

### Unit Tests
- Event serialization/deserialization
- Producer idempotency
- Consumer error handling

### Integration Tests
```python
@pytest.mark.integration
async def test_inspection_event_flow():
    # Publish inspection created event
    event = InspectionCreatedEvent(...)
    await kafka_producer.send('inspection.lifecycle', event)
    
    # Verify inference service processes event
    await wait_for_consumer_processing()
    
    # Check database state
    inference = await db.inferences.get_by_inspection_id(event.inspection_id)
    assert inference.status == 'queued'
```

### Performance Tests
- Producer throughput under load
- Consumer lag during traffic spikes
- Schema evolution impact

## Disaster Recovery

### Backup Strategy
- **Cross-Region Replication**: MirrorMaker 2.0 for disaster recovery
- **Retention Policies**: Configurable retention based on topic criticality
- **Snapshot Backups**: Periodic Kafka state snapshots

### Recovery Procedures
1. **Topic Recovery**: Restore from replicated cluster
2. **Consumer Position**: Reset to last known good checkpoint
3. **Data Validation**: Verify event integrity after recovery

## References
- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [Confluent Platform Documentation](https://docs.confluent.io/)
- [Event-Driven Architecture Patterns](https://microservices.io/patterns/data/event-driven-architecture.html)
- [Kafka Streams Documentation](https://kafka.apache.org/documentation/streams/)