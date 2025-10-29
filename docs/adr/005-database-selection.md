# ADR-005: Database Technology Selection

## Status
Accepted

## Context
The chip quality inspection platform requires a robust data persistence layer that can handle:
- **OLTP Workloads**: High-frequency reads/writes for inspection data
- **Time-Series Data**: Metrics, sensor readings, and system telemetry
- **Analytics**: Complex queries for reporting and business intelligence
- **Compliance**: Audit trails and data retention requirements
- **Scalability**: Growth from thousands to millions of inspections

## Decision
We will use a hybrid database approach combining PostgreSQL 15+ with TimescaleDB extension for optimal performance across different data patterns:

### Primary Database: PostgreSQL 15
- **Core Application Data**: Inspections, defects, parts, lots, reports
- **ACID Compliance**: Strong consistency for critical business data
- **Rich Data Types**: JSONB for flexible metadata storage
- **Advanced Features**: Partial indexes, foreign data wrappers, logical replication

### Time-Series Extension: TimescaleDB
- **Metrics Storage**: System metrics, sensor data, performance telemetry
- **Hypertables**: Automatic partitioning by time for optimal performance
- **Continuous Aggregates**: Pre-computed rollups for dashboard queries
- **Data Retention**: Automated cleanup of old time-series data

## Architecture Design

### Database Deployment Strategy

#### Primary-Replica Setup
```yaml
# PostgreSQL cluster configuration
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: postgres-cluster
spec:
  instances: 3
  primaryUpdateStrategy: unsupervised
  
  postgresql:
    parameters:
      max_connections: "200"
      shared_buffers: "256MB"
      effective_cache_size: "1GB"
      work_mem: "4MB"
      maintenance_work_mem: "64MB"
      checkpoint_completion_target: "0.9"
      wal_buffers: "16MB"
      default_statistics_target: "100"
      random_page_cost: "1.1"
      effective_io_concurrency: "200"
    
  bootstrap:
    initdb:
      database: chip_quality
      owner: app_user
      secret:
        name: postgres-credentials
  
  storage:
    size: 100Gi
    storageClass: fast-ssd
    
  monitoring:
    enabled: true
```

#### Connection Pooling
```yaml
# PgBouncer configuration
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pgbouncer
spec:
  template:
    spec:
      containers:
      - name: pgbouncer
        image: pgbouncer/pgbouncer:1.19
        env:
        - name: DATABASES_HOST
          value: postgres-cluster-rw
        - name: DATABASES_PORT
          value: "5432"
        - name: POOL_MODE
          value: transaction
        - name: MAX_CLIENT_CONN
          value: "1000"
        - name: DEFAULT_POOL_SIZE
          value: "25"
```

### Schema Design Principles

#### Core Business Entities
```sql
-- Optimized table design with proper indexing
CREATE TABLE inspections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lot_id UUID NOT NULL REFERENCES lots(id),
    chip_id VARCHAR(100) NOT NULL,
    inspection_type inspection_type_enum NOT NULL,
    status inspection_status_enum DEFAULT 'pending',
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure uniqueness and enable efficient queries
    CONSTRAINT unique_inspection UNIQUE (lot_id, chip_id, inspection_type)
);

-- Optimized indexes for common query patterns
CREATE INDEX CONCURRENTLY idx_inspections_status 
    ON inspections(status) WHERE status != 'completed';
    
CREATE INDEX CONCURRENTLY idx_inspections_created_at_desc 
    ON inspections(created_at DESC);
    
CREATE INDEX CONCURRENTLY idx_inspections_chip_id 
    ON inspections USING hash(chip_id);
    
-- GIN index for JSONB metadata queries
CREATE INDEX CONCURRENTLY idx_inspections_metadata 
    ON inspections USING gin(metadata);
```

#### TimescaleDB Hypertables
```sql
-- Time-series metrics table
CREATE TABLE system_metrics (
    time TIMESTAMPTZ NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    tags JSONB,
    host VARCHAR(100)
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('system_metrics', 'time', chunk_time_interval => INTERVAL '1 day');

-- Create indexes for typical queries
CREATE INDEX CONCURRENTLY idx_system_metrics_service_metric 
    ON system_metrics(service_name, metric_name, time DESC);
    
CREATE INDEX CONCURRENTLY idx_system_metrics_tags 
    ON system_metrics USING gin(tags);

-- Retention policy for automatic cleanup
SELECT add_retention_policy('system_metrics', INTERVAL '90 days');

-- Continuous aggregate for dashboard queries
CREATE MATERIALIZED VIEW metrics_hourly
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', time) AS bucket,
    service_name,
    metric_name,
    avg(metric_value) as avg_value,
    max(metric_value) as max_value,
    min(metric_value) as min_value,
    count(*) as sample_count
FROM system_metrics
GROUP BY bucket, service_name, metric_name;
```

### Data Access Patterns

#### Async SQLAlchemy Configuration
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Database engine configuration
DATABASE_URL = "postgresql+asyncpg://user:pass@pgbouncer:5432/chip_quality"

engine = create_async_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Use PgBouncer for pooling
    echo=False,
    future=True,
    connect_args={
        "command_timeout": 30,
        "server_settings": {
            "application_name": "chip-quality-api",
            "jit": "off",  # Disable JIT for short queries
        },
    }
)

# Session factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Connection management
async def get_db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

#### Repository Pattern Implementation
```python
class InspectionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, inspection_data: InspectionCreate) -> Inspection:
        """Create inspection with optimistic locking"""
        inspection = Inspection(**inspection_data.dict())
        self.session.add(inspection)
        try:
            await self.session.flush()
            return inspection
        except IntegrityError as e:
            if "unique_inspection" in str(e):
                raise DuplicateInspectionError()
            raise
    
    async def find_by_status(
        self, 
        status: InspectionStatus,
        cursor: Optional[str] = None,
        limit: int = 20
    ) -> List[Inspection]:
        """Cursor-based pagination for stable results"""
        query = select(Inspection).where(Inspection.status == status)
        
        if cursor:
            cursor_time = decode_cursor(cursor)
            query = query.where(Inspection.created_at < cursor_time)
        
        query = query.order_by(Inspection.created_at.desc()).limit(limit + 1)
        
        result = await self.session.execute(query)
        inspections = result.scalars().all()
        
        has_more = len(inspections) > limit
        if has_more:
            inspections = inspections[:-1]
        
        return inspections, has_more

    async def get_metrics_summary(
        self, 
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Complex analytics query using TimescaleDB"""
        query = text("""
            SELECT 
                service_name,
                avg(metric_value) as avg_value,
                max(metric_value) as max_value,
                count(*) as sample_count
            FROM metrics_hourly 
            WHERE bucket BETWEEN :start_time AND :end_time
                AND metric_name = 'response_time_ms'
            GROUP BY service_name
            ORDER BY avg_value DESC
        """)
        
        result = await self.session.execute(
            query, 
            {"start_time": start_time, "end_time": end_time}
        )
        return [dict(row) for row in result.fetchall()]
```

### Performance Optimization

#### Query Optimization
```sql
-- Partial indexes for common filters
CREATE INDEX CONCURRENTLY idx_inspections_pending 
    ON inspections(created_at) WHERE status = 'pending';

-- Covering indexes to avoid table lookups
CREATE INDEX CONCURRENTLY idx_inspections_summary 
    ON inspections(lot_id, chip_id) INCLUDE (status, created_at);

-- Materialized views for complex aggregations
CREATE MATERIALIZED VIEW daily_inspection_summary AS
SELECT 
    date_trunc('day', created_at) as inspection_date,
    inspection_type,
    status,
    count(*) as inspection_count,
    avg(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds
FROM inspections
WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY 1, 2, 3;

-- Refresh strategy
CREATE UNIQUE INDEX ON daily_inspection_summary (inspection_date, inspection_type, status);
```

#### Connection and Memory Optimization
```python
# SQLAlchemy configuration for performance
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo_pool=True,
    connect_args={
        "statement_cache_size": 0,  # Disable for high variability queries
        "prepared_statement_cache_size": 0,
    }
)
```

### Backup and Recovery

#### Continuous Backup Strategy
```yaml
# PostgreSQL backup configuration
apiVersion: postgresql.cnpg.io/v1
kind: ScheduledBackup
metadata:
  name: postgres-backup
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  backupOwnerReference: self
  cluster:
    name: postgres-cluster
  
  # Retention policy
  retentionPolicy: "30d"
  
  # S3 configuration
  s3:
    destinationPath: "s3://chip-quality-backups/postgres"
    region: us-east-1
    accessKeyId:
      name: backup-credentials
      key: ACCESS_KEY_ID
    secretAccessKey:
      name: backup-credentials
      key: SECRET_ACCESS_KEY
```

#### Point-in-Time Recovery
```bash
# Recovery procedure
kubectl apply -f - <<EOF
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: postgres-recovery
spec:
  instances: 3
  
  bootstrap:
    recovery:
      backup:
        name: postgres-backup-20250120
      recoveryTarget:
        targetTime: "2025-01-20 10:30:00"
EOF
```

### Monitoring and Alerting

#### Key Metrics
```yaml
# PostgreSQL monitoring queries
groups:
- name: postgresql.rules
  rules:
  - alert: PostgreSQLDown
    expr: pg_up == 0
    for: 1m
    annotations:
      summary: "PostgreSQL is down"

  - alert: PostgreSQLHighConnections
    expr: pg_stat_database_numbackends / pg_settings_max_connections > 0.8
    for: 5m
    annotations:
      summary: "High connection usage: {{ $value }}"

  - alert: PostgreSQLLongRunningTransactions
    expr: pg_stat_activity_max_tx_duration > 300
    for: 2m
    annotations:
      summary: "Long running transaction detected"

  - alert: TimescaleDBHighChunkSize
    expr: timescaledb_hypertable_chunk_size_bytes > 1073741824  # 1GB
    for: 10m
    annotations:
      summary: "Large chunk detected in hypertable"
```

#### Performance Monitoring
```sql
-- Custom monitoring views
CREATE VIEW slow_queries AS
SELECT 
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements
WHERE mean_exec_time > 100  -- Queries slower than 100ms
ORDER BY mean_exec_time DESC;

-- Index usage monitoring
CREATE VIEW unused_indexes AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE idx_tup_read = 0 AND idx_tup_fetch = 0
ORDER BY pg_relation_size(indexrelid) DESC;
```

## Consequences

### Positive
- **Performance**: Optimized for both OLTP and analytics workloads
- **Scalability**: Horizontal read scaling with replicas
- **Time-Series Efficiency**: TimescaleDB provides 10-100x better performance for metrics
- **Data Integrity**: ACID compliance for critical business data
- **Rich Ecosystem**: Extensive tooling and community support
- **Cost Effective**: Open source with commercial support available

### Negative
- **Complexity**: Managing two database paradigms requires expertise
- **Storage Growth**: Time-series data can grow rapidly
- **Backup Size**: Large databases require significant backup storage
- **Cache Warming**: Read replicas need time to warm up after failover

### Mitigations
- **Automated Management**: Use CloudNativePG operator for lifecycle management
- **Monitoring**: Comprehensive metrics and alerting for proactive management
- **Documentation**: Clear procedures for common operational tasks
- **Training**: Team education on PostgreSQL and TimescaleDB optimization

## Alternative Approaches Considered

### MongoDB + InfluxDB
- **Pros**: Document model flexibility, purpose-built time-series database
- **Cons**: Two different query languages, eventual consistency challenges
- **Verdict**: Added complexity outweighs benefits

### MySQL + Prometheus
- **Pros**: Familiar technology stack, battle-tested at scale
- **Cons**: Limited JSON support, Prometheus not designed for long-term storage
- **Verdict**: PostgreSQL offers better feature set for our use case

### SingleStore (MemSQL)
- **Pros**: Unified OLTP/OLAP, excellent performance
- **Cons**: Commercial licensing costs, vendor lock-in
- **Verdict**: Cost and lock-in concerns for startup environment

## Implementation Timeline

### Phase 1: Foundation (Week 1-2)
- Deploy PostgreSQL cluster with CloudNativePG
- Set up TimescaleDB extension
- Implement basic schema and migrations

### Phase 2: Optimization (Week 3-4)
- Configure connection pooling and monitoring
- Implement repository patterns and query optimization
- Set up backup and recovery procedures

### Phase 3: Production Readiness (Week 5-6)
- Load testing and performance tuning
- Security hardening and compliance setup
- Documentation and operational procedures

## References
- [PostgreSQL 15 Documentation](https://www.postgresql.org/docs/15/)
- [TimescaleDB Documentation](https://docs.timescale.com/)
- [CloudNativePG Operator](https://cloudnative-pg.io/)
- [PgBouncer Configuration Guide](https://www.pgbouncer.org/config.html)