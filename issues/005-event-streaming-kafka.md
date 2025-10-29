# Issue #005: Implement Event Streaming with Apache Kafka

## 🎯 Objective
Implement comprehensive event streaming architecture using Apache Kafka for real-time data processing, system integration, and event-driven workflows in the semiconductor manufacturing platform.

## 📋 Priority
**MEDIUM** - Enables real-time processing and system decoupling

## 🔍 Context
The platform currently has:
- ✅ Apache Kafka cluster configured in docker-compose (`docker-compose.yml`)
- ✅ Schema Registry for event schema management
- ✅ Kafka UI for monitoring and management
- ✅ Event streaming design in architecture (`1. Architecture (final).txt`)
- ❌ **MISSING**: Event producers, consumers, schema definitions, stream processing logic

## 🎯 Acceptance Criteria

### Core Event Streaming Features
- [ ] **Event Publishing**: Reliable event publishing for all platform activities
- [ ] **Event Consumption**: Scalable event consumption with consumer groups
- [ ] **Schema Management**: Avro schema evolution and compatibility
- [ ] **Stream Processing**: Real-time stream processing for analytics
- [ ] **Dead Letter Queues**: Error handling and message retry mechanisms
- [ ] **Event Ordering**: Maintain event ordering for critical business processes
- [ ] **Exactly-Once Delivery**: Ensure data consistency and prevent duplicates

### Business Event Categories
- [ ] **Manufacturing Events**: Batch creation, lot processing, production milestones
- [ ] **Inspection Events**: Inspection lifecycle, quality results, defect detection
- [ ] **Quality Events**: Quality threshold violations, alerts, compliance events
- [ ] **User Events**: Authentication, authorization, audit trail events
- [ ] **System Events**: Service health, performance metrics, error conditions
- [ ] **ML Events**: Model inference, training completion, drift detection

### Integration Features
- [ ] **Service Decoupling**: Asynchronous communication between services
- [ ] **Real-time Analytics**: Stream processing for live dashboards
- [ ] **External Integration**: Event forwarding to external systems (MES, ERP)
- [ ] **Notification System**: Real-time alerts and notifications
- [ ] **Data Pipeline**: ETL processing for data warehouse integration
- [ ] **Audit Compliance**: Immutable event log for regulatory compliance

## 📁 Implementation Structure

```
services/shared/events/
├── __init__.py                       # Event system exports
├── schemas/                          # Avro schema definitions
│   ├── __init__.py
│   ├── manufacturing.avsc            # Manufacturing event schemas
│   ├── inspection.avsc               # Inspection event schemas
│   ├── quality.avsc                  # Quality event schemas
│   ├── user.avsc                     # User activity schemas
│   └── system.avsc                   # System event schemas
├── producers/
│   ├── __init__.py
│   ├── base_producer.py              # Base event producer
│   ├── manufacturing_producer.py     # Manufacturing event publisher
│   ├── inspection_producer.py        # Inspection event publisher
│   ├── quality_producer.py           # Quality event publisher
│   └── user_producer.py              # User activity publisher
├── consumers/
│   ├── __init__.py
│   ├── base_consumer.py              # Base event consumer
│   ├── analytics_consumer.py         # Real-time analytics processing
│   ├── notification_consumer.py      # Alert and notification handling
│   ├── audit_consumer.py             # Audit trail processing
│   └── integration_consumer.py       # External system integration
├── processors/
│   ├── __init__.py
│   ├── stream_processor.py           # Kafka Streams processing
│   ├── quality_aggregator.py         # Quality metrics aggregation
│   ├── alert_processor.py            # Real-time alert processing
│   └── analytics_processor.py        # Stream analytics processing
└── utils/
    ├── __init__.py
    ├── kafka_client.py               # Kafka client configuration
    ├── schema_registry.py            # Schema registry integration
    └── serialization.py              # Avro serialization utilities

services/event-processor/
├── app/
│   ├── __init__.py
│   ├── main.py                       # Event processing service
│   ├── processors/                   # Stream processing logic
│   └── routers/                      # Event monitoring APIs
└── Dockerfile                       # Service containerization
```

## 🔧 Technical Specifications

### 1. Event Schema Definitions

**File**: `services/shared/events/schemas/inspection.avsc`

```json
{
  "type": "record",
  "name": "InspectionEvent",
  "namespace": "com.chipquality.events.inspection",
  "doc": "Event for inspection lifecycle changes",
  "fields": [
    {
      "name": "event_id",
      "type": "string",
      "doc": "Unique event identifier"
    },
    {
      "name": "event_type",
      "type": {
        "type": "enum",
        "name": "InspectionEventType",
        "symbols": [
          "INSPECTION_CREATED",
          "INSPECTION_STARTED", 
          "INSPECTION_COMPLETED",
          "INSPECTION_FAILED",
          "DEFECT_DETECTED",
          "QUALITY_ASSESSED"
        ]
      }
    },
    {
      "name": "timestamp",
      "type": "long",
      "logicalType": "timestamp-millis"
    },
    {
      "name": "inspection_id",
      "type": "string"
    },
    {
      "name": "batch_id", 
      "type": "string"
    },
    {
      "name": "chip_id",
      "type": "string"
    },
    {
      "name": "inspection_type",
      "type": "string"
    },
    {
      "name": "status",
      "type": "string"
    },
    {
      "name": "quality_score",
      "type": ["null", "double"],
      "default": null
    },
    {
      "name": "defects",
      "type": {
        "type": "array",
        "items": {
          "type": "record",
          "name": "Defect",
          "fields": [
            {"name": "defect_type", "type": "string"},
            {"name": "severity", "type": "string"},
            {"name": "confidence", "type": "double"},
            {"name": "location", "type": "string"}
          ]
        }
      },
      "default": []
    },
    {
      "name": "metadata",
      "type": {
        "type": "map",
        "values": "string"
      },
      "default": {}
    }
  ]
}
```

### 2. Base Event Producer

**File**: `services/shared/events/producers/base_producer.py`

```python
"""
Base event producer with reliability and performance features:

Producer Features:
- Asynchronous message publishing with callbacks
- Automatic retry with exponential backoff
- Dead letter queue for failed messages
- Schema registry integration for validation
- Partitioning strategy for scalability
- Compression and serialization optimization

Reliability Features:
- Acknowledgment handling (acks=all)
- Idempotent producer configuration
- Transaction support for exactly-once semantics
- Connection pooling and health monitoring
- Graceful shutdown and resource cleanup
- Comprehensive error handling and logging

Performance Features:
- Batch processing for high throughput
- Configurable buffering and flush policies
- Connection reuse and optimization
- Metrics collection for monitoring
- Memory management and resource optimization
"""
```

### 3. Inspection Event Producer

**File**: `services/shared/events/producers/inspection_producer.py`

```python
"""
Inspection-specific event publishing:

Event Publishing:
- Inspection lifecycle events (created, started, completed)
- Quality assessment results and scoring
- Defect detection and classification events
- ML inference completion and results
- Manual review and approval events
- Error and failure condition events

Integration Features:
- Integration with inspection service business logic
- Automatic event generation from database changes
- Correlation ID tracking for event tracing
- Event enrichment with contextual metadata
- Filtering and routing based on event criteria

Business Logic:
- Event publishing at key inspection milestones
- Quality threshold violation detection
- Real-time dashboard update triggers
- Notification routing for stakeholders
- Audit trail maintenance for compliance
- Integration with external quality systems
"""
```

### 4. Real-time Analytics Consumer

**File**: `services/shared/events/consumers/analytics_consumer.py`

```python
"""
Real-time analytics and metrics processing:

Stream Processing Features:
- Real-time quality metrics calculation
- Production line performance monitoring
- Defect rate trending and analysis
- Inspection throughput tracking
- Quality threshold monitoring
- Predictive analytics for quality issues

Analytics Processing:
- Windowed aggregations for time-based metrics
- Quality control charts and SPC calculations
- Anomaly detection for quality patterns
- Trend analysis and forecasting
- Correlation analysis between process parameters
- Performance KPI calculation and tracking

Integration Features:
- Real-time dashboard updates
- Metrics storage in time-series database
- Alert generation for threshold violations
- Integration with business intelligence systems
- Data export for offline analysis
"""
```

### 5. Stream Processing Engine

**File**: `services/shared/events/processors/stream_processor.py`

```python
"""
Kafka Streams processing for complex event workflows:

Stream Processing Features:
- Complex event pattern detection
- Multi-stream joins and correlations
- Stateful processing with local state stores
- Windowed operations for time-based analysis
- Event sourcing and CQRS patterns
- Real-time aggregations and computations

Quality Processing:
- Quality trend analysis across batches
- Defect pattern recognition and clustering
- Process capability monitoring (Cp, Cpk)
- Automatic quality gate evaluation
- Predictive quality modeling
- Root cause analysis automation

Performance Features:
- Parallel processing with multiple instances
- State store optimization for fast lookups
- Memory management for large datasets
- Checkpoint and recovery mechanisms
- Backpressure handling and flow control
"""
```

### 6. Event Monitoring API

**File**: `services/event-processor/app/routers/events.py`

```python
"""
Event streaming monitoring and management API:

Event Monitoring:
GET    /events/topics               - List Kafka topics and status
GET    /events/topics/{name}        - Get topic details and metrics
GET    /events/consumers            - List consumer groups and lag
GET    /events/schemas              - List registered schemas
GET    /events/health               - Event system health check

Event Analytics:
GET    /events/metrics              - Event processing metrics
GET    /events/throughput           - Message throughput statistics
GET    /events/latency              - End-to-end latency metrics
GET    /events/errors               - Error rates and dead letter queues

Event Management:
POST   /events/replay               - Replay events from specific offset
POST   /events/reset                - Reset consumer group offset
PUT    /events/schemas/{id}         - Update schema compatibility
DELETE /events/topics/{name}        - Delete topic (admin only)
"""
```

## 🧪 Testing Requirements

### Unit Tests
**File**: `tests/unit/test_event_streaming.py`

```python
"""
Comprehensive event streaming testing:

Event Producer Testing:
- Event serialization and schema validation
- Error handling for publishing failures
- Retry mechanisms and dead letter queues
- Performance testing with high message volumes
- Configuration validation and connection handling

Event Consumer Testing:
- Message deserialization and processing
- Consumer group coordination and rebalancing
- Offset management and exactly-once processing
- Error handling and recovery mechanisms
- Performance testing with high throughput

Schema Testing:
- Schema evolution and compatibility validation
- Avro serialization and deserialization
- Schema registry integration testing
- Backward and forward compatibility verification

Coverage Requirements:
- 95%+ code coverage for all event processing logic
- Edge case testing (network failures, service unavailability)
- Performance testing (throughput, latency, resource usage)
- Concurrent processing and thread safety validation
"""
```

### Integration Tests
**File**: `tests/integration/test_kafka_integration.py`

```python
"""
Full Kafka cluster integration testing:

End-to-End Testing:
- Complete message flow from producer to consumer
- Schema registry integration and evolution
- Consumer group coordination and rebalancing
- Topic creation and configuration management
- Dead letter queue handling and recovery

Performance Validation:
- Message throughput testing (>10,000 messages/second)
- End-to-end latency measurement (<100ms P95)
- Consumer lag monitoring and alerting
- Resource utilization under load
- Scaling behavior with multiple consumers

Failure Testing:
- Kafka broker failure and recovery
- Network partition handling
- Consumer failure and rebalancing
- Message ordering and delivery guarantees
- Data consistency and exactly-once processing
"""
```

### Stream Processing Tests
**File**: `tests/integration/test_stream_processing.py`

```python
"""
Stream processing logic validation:

Stream Processing Testing:
- Complex event pattern detection accuracy
- Windowed aggregation correctness
- State store persistence and recovery
- Multi-stream joins and correlations
- Performance under high event volumes

Business Logic Testing:
- Quality metrics calculation accuracy
- Alert generation for threshold violations
- Real-time analytics correctness
- Integration with downstream systems
- Event replay and reprocessing capabilities
"""
```

## 📚 Architecture References

### Primary References
- **Architecture Document**: `1. Architecture (final).txt` (Event streaming design)
- **Kafka Configuration**: `docker-compose.yml` (Kafka cluster setup)
- **Event Design Patterns**: Event sourcing and CQRS documentation

### Implementation Guidelines
- **Schema Registry**: Confluent Schema Registry best practices
- **Kafka Streams**: Stream processing patterns and optimization
- **Event Modeling**: Domain-driven design for event schemas

### Integration Points
- **Service Integration**: How services publish and consume events
- **Database Integration**: Event sourcing and CQRS patterns
- **Monitoring Integration**: Metrics and alerting for event streams

## 🔗 Dependencies

### Blocking Dependencies
- **Issue #001**: Database models for event persistence
- **Apache Kafka**: Kafka cluster must be operational

### Service Dependencies
- **Kafka Cluster**: Apache Kafka with Zookeeper
- **Schema Registry**: Confluent Schema Registry for schema management
- **PostgreSQL**: Database for event metadata and state storage
- **Redis**: Caching for consumer state and metrics

### Python Dependencies
```toml
# Add to pyproject.toml
[tool.poetry.dependencies]
kafka-python = "^2.0.2"
confluent-kafka = "^2.3.0"
avro = "^1.11.3"
fastavro = "^1.9.0"
confluent-kafka-avro = "^0.11.0"
python-schema-registry-client = "^2.5.2"
```

## 🎯 Implementation Strategy

### Phase 1: Event Infrastructure (Priority 1)
1. **Schema Definitions**: Create Avro schemas for all event types
2. **Base Producers/Consumers**: Implement base classes with reliability features
3. **Kafka Client**: Configure Kafka client with optimization
4. **Schema Registry Integration**: Setup schema management

### Phase 2: Business Events (Priority 2)
1. **Manufacturing Events**: Implement batch and lot processing events
2. **Inspection Events**: Create inspection lifecycle event publishing
3. **Quality Events**: Add quality assessment and alert events
4. **Event Consumers**: Build consumers for real-time processing

### Phase 3: Stream Processing (Priority 3)
1. **Analytics Processing**: Implement real-time analytics streams
2. **Alert Processing**: Create alert generation and routing
3. **Quality Aggregation**: Build quality metrics aggregation
4. **Event Monitoring**: Add monitoring and management APIs

### Phase 4: Advanced Features (Priority 4)
1. **Complex Patterns**: Implement complex event processing
2. **External Integration**: Add integration with external systems
3. **Performance Optimization**: Optimize for high throughput
4. **Operational Features**: Add replay, reset, and management capabilities

## ✅ Definition of Done

### Functional Completeness
- [ ] Complete event streaming infrastructure with producers and consumers
- [ ] Avro schema management with evolution support
- [ ] Real-time stream processing for analytics and alerts
- [ ] Integration with all platform services for event publishing
- [ ] Event monitoring and management capabilities

### Performance Validation
- [ ] Message throughput > 10,000 messages per second
- [ ] End-to-end event latency < 100ms P95
- [ ] Consumer lag monitoring and alerting
- [ ] Support for 1M+ events per day processing
- [ ] Resource optimization for memory and CPU usage

### Reliability Validation
- [ ] Exactly-once delivery guarantees for critical events
- [ ] Dead letter queue handling for failed messages
- [ ] Consumer group rebalancing and failure recovery
- [ ] Event ordering maintenance for business-critical flows
- [ ] Comprehensive error handling and retry mechanisms

### Production Readiness
- [ ] 95%+ test coverage with integration and performance tests
- [ ] Comprehensive monitoring and alerting for event streams
- [ ] Health checks and service status endpoints
- [ ] Configuration management for different environments
- [ ] Documentation with event modeling and integration guides

## 🚨 Critical Implementation Notes

### Performance Requirements
- **Throughput**: Minimum 10,000 events per second sustained
- **Latency**: P95 end-to-end latency < 100ms for critical events
- **Scalability**: Support for horizontal scaling with consumer groups
- **Resource Efficiency**: Optimize memory usage for large event volumes

### Reliability Requirements
- **Delivery Guarantees**: Exactly-once delivery for business-critical events
- **Fault Tolerance**: Handle broker failures and network partitions
- **Data Consistency**: Maintain event ordering for related events
- **Recovery**: Fast recovery from failures with minimal data loss

### Schema Management
- **Evolution**: Support backward and forward compatible schema evolution
- **Validation**: Strict schema validation for all published events
- **Documentation**: Comprehensive schema documentation and examples
- **Governance**: Schema review and approval process for changes

### Integration Requirements
- **Service Decoupling**: Enable loose coupling between platform services
- **Real-time Processing**: Support for real-time analytics and dashboards
- **External Integration**: Event forwarding to external systems (MES, ERP)
- **Audit Compliance**: Immutable event log for regulatory requirements

This event streaming implementation will provide a robust, scalable foundation for real-time data processing and system integration while maintaining strict performance and reliability requirements for semiconductor manufacturing operations.