# Database Schema Documentation

## Overview

The Chip Quality Platform uses a hybrid database approach combining PostgreSQL for transactional data and TimescaleDB for time-series metrics and performance data. This design provides ACID compliance for critical business data while enabling efficient analytics and monitoring.

## Database Architecture

### PostgreSQL Primary Database
- **Version**: PostgreSQL 15+
- **Purpose**: Transactional data, business entities, relationships
- **Connection Pooling**: PgBouncer with transaction-level pooling
- **Backup Strategy**: Point-in-time recovery with WAL archiving
- **High Availability**: Streaming replication with automatic failover

### TimescaleDB Extension
- **Purpose**: Time-series data, metrics, performance analytics
- **Hypertables**: Automatic partitioning by time
- **Compression**: Automated compression for historical data
- **Retention Policies**: Automated data lifecycle management

## Core Schema Design

### 1. Manufacturing Entities

#### Parts Table
```sql
CREATE TABLE parts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    part_number VARCHAR(100) NOT NULL UNIQUE,
    part_name VARCHAR(200) NOT NULL,
    part_type part_type_enum NOT NULL, -- 'pcb', 'semiconductor', 'component', 'assembly'
    specifications JSONB NOT NULL DEFAULT '{}',
    tolerance_requirements JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    version INTEGER NOT NULL DEFAULT 1
);

-- Indexes
CREATE INDEX idx_parts_part_number ON parts(part_number);
CREATE INDEX idx_parts_type ON parts(part_type);
CREATE INDEX idx_parts_specifications_gin ON parts USING GIN(specifications);
CREATE INDEX idx_parts_updated_at ON parts(updated_at DESC);
```

#### Lots Table
```sql
CREATE TABLE lots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lot_number VARCHAR(100) NOT NULL UNIQUE,
    part_id UUID NOT NULL REFERENCES parts(id) ON DELETE RESTRICT,
    production_date DATE NOT NULL,
    batch_size INTEGER NOT NULL CHECK (batch_size > 0),
    production_line VARCHAR(50) NOT NULL,
    supplier_id UUID,
    quality_requirements JSONB NOT NULL DEFAULT '{}',
    metadata JSONB NOT NULL DEFAULT '{}',
    status lot_status_enum NOT NULL DEFAULT 'active', -- 'active', 'completed', 'quarantined', 'released'
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_lots_lot_number ON lots(lot_number);
CREATE INDEX idx_lots_part_id ON lots(part_id);
CREATE INDEX idx_lots_production_date ON lots(production_date DESC);
CREATE INDEX idx_lots_status ON lots(status);
CREATE INDEX idx_lots_production_line ON lots(production_line);
```

### 2. Inspection Management

#### Inspections Table
```sql
CREATE TABLE inspections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lot_id UUID NOT NULL REFERENCES lots(id) ON DELETE RESTRICT,
    chip_id VARCHAR(100) NOT NULL, -- Individual component identifier within lot
    inspection_type inspection_type_enum NOT NULL, -- 'visual', 'electrical', 'thermal', 'dimensional', 'functional'
    status inspection_status_enum NOT NULL DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'failed'
    priority INTEGER NOT NULL DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    station_id VARCHAR(50) NOT NULL,
    operator_id UUID,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Business constraints
    CONSTRAINT unique_inspection_per_chip UNIQUE (lot_id, chip_id, inspection_type),
    CONSTRAINT valid_completion_order CHECK (
        (completed_at IS NULL) OR 
        (started_at IS NOT NULL AND completed_at >= started_at)
    )
);

-- Indexes
CREATE INDEX idx_inspections_lot_id ON inspections(lot_id);
CREATE INDEX idx_inspections_chip_id ON inspections(chip_id);
CREATE INDEX idx_inspections_status_created ON inspections(status, created_at DESC);
CREATE INDEX idx_inspections_type_status ON inspections(inspection_type, status);
CREATE INDEX idx_inspections_station_id ON inspections(station_id);
CREATE INDEX idx_inspections_priority_created ON inspections(priority DESC, created_at ASC);
CREATE INDEX idx_inspections_metadata_gin ON inspections USING GIN(metadata);
```

### 3. Defect Management

#### Defects Table
```sql
CREATE TABLE defects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inspection_id UUID NOT NULL REFERENCES inspections(id) ON DELETE CASCADE,
    defect_type defect_type_enum NOT NULL, -- 'scratch', 'void', 'contamination', 'misalignment', 'short', 'open', 'crack', 'burn', 'foreign_object'
    severity defect_severity_enum NOT NULL, -- 'low', 'medium', 'high', 'critical'
    confidence DECIMAL(5,4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    location JSONB NOT NULL, -- Bounding box: {x, y, width, height}
    description TEXT,
    detection_method detection_method_enum NOT NULL, -- 'ml_automated', 'manual_review', 'hybrid'
    reviewer_id UUID, -- User who reviewed/confirmed the defect
    review_status review_status_enum DEFAULT 'pending', -- 'pending', 'confirmed', 'rejected', 'needs_review'
    corrective_action TEXT,
    artifact_references JSONB DEFAULT '[]', -- Array of artifact IDs showing the defect
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_defects_inspection_id ON defects(inspection_id);
CREATE INDEX idx_defects_type_severity ON defects(defect_type, severity);
CREATE INDEX idx_defects_confidence ON defects(confidence DESC);
CREATE INDEX idx_defects_review_status ON defects(review_status);
CREATE INDEX idx_defects_detection_method ON defects(detection_method);
CREATE INDEX idx_defects_created_at ON defects(created_at DESC);
```

### 4. ML Inference Management

#### Inference Jobs Table
```sql
CREATE TABLE inference_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inspection_id UUID NOT NULL REFERENCES inspections(id) ON DELETE CASCADE,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    status inference_status_enum NOT NULL DEFAULT 'queued', -- 'queued', 'processing', 'completed', 'failed', 'cancelled'
    priority INTEGER NOT NULL DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    batch_size INTEGER NOT NULL DEFAULT 1 CHECK (batch_size > 0),
    confidence_threshold DECIMAL(5,4) NOT NULL DEFAULT 0.7,
    processing_parameters JSONB NOT NULL DEFAULT '{}',
    input_artifacts JSONB NOT NULL DEFAULT '[]', -- Array of artifact IDs to process
    output_artifacts JSONB DEFAULT '[]', -- Array of generated artifact IDs
    triton_request_id VARCHAR(100), -- NVIDIA Triton request identifier
    error_message TEXT,
    performance_metrics JSONB DEFAULT '{}', -- Execution time, GPU utilization, etc.
    queued_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_job_timing CHECK (
        (started_at IS NULL OR started_at >= queued_at) AND
        (completed_at IS NULL OR (started_at IS NOT NULL AND completed_at >= started_at))
    )
);

-- Indexes
CREATE INDEX idx_inference_jobs_inspection_id ON inference_jobs(inspection_id);
CREATE INDEX idx_inference_jobs_status_priority ON inference_jobs(status, priority DESC, queued_at ASC);
CREATE INDEX idx_inference_jobs_model ON inference_jobs(model_name, model_version);
CREATE INDEX idx_inference_jobs_triton_request ON inference_jobs(triton_request_id) WHERE triton_request_id IS NOT NULL;
CREATE INDEX idx_inference_jobs_created_at ON inference_jobs(created_at DESC);
```

### 5. Artifact Storage

#### Artifacts Table
```sql
CREATE TABLE artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inspection_id UUID NOT NULL REFERENCES inspections(id) ON DELETE CASCADE,
    inference_job_id UUID REFERENCES inference_jobs(id) ON DELETE SET NULL,
    artifact_type artifact_type_enum NOT NULL, -- 'image', 'video', 'measurement', 'document', 'log'
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL, -- Object storage path
    content_type VARCHAR(100) NOT NULL,
    file_size_bytes BIGINT NOT NULL CHECK (file_size_bytes >= 0),
    checksum_sha256 CHAR(64) NOT NULL, -- File integrity verification
    storage_location storage_location_enum NOT NULL DEFAULT 'primary', -- 'primary', 'archive', 'cold_storage'
    metadata JSONB NOT NULL DEFAULT '{}',
    tags TEXT[] DEFAULT '{}', -- Searchable tags
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    archived_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT unique_file_path UNIQUE (file_path),
    CONSTRAINT valid_checksum CHECK (checksum_sha256 ~ '^[a-f0-9]{64}$')
);

-- Indexes
CREATE INDEX idx_artifacts_inspection_id ON artifacts(inspection_id);
CREATE INDEX idx_artifacts_inference_job_id ON artifacts(inference_job_id) WHERE inference_job_id IS NOT NULL;
CREATE INDEX idx_artifacts_type ON artifacts(artifact_type);
CREATE INDEX idx_artifacts_file_path ON artifacts(file_path);
CREATE INDEX idx_artifacts_checksum ON artifacts(checksum_sha256);
CREATE INDEX idx_artifacts_tags_gin ON artifacts USING GIN(tags);
CREATE INDEX idx_artifacts_created_at ON artifacts(created_at DESC);
CREATE INDEX idx_artifacts_storage_location ON artifacts(storage_location);
```

### 6. Reporting and Analytics

#### Reports Table
```sql
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_type report_type_enum NOT NULL, -- 'inspection_summary', 'defect_analysis', 'quality_metrics', 'production_overview'
    title VARCHAR(200) NOT NULL,
    description TEXT,
    filters JSONB NOT NULL DEFAULT '{}', -- Report generation parameters
    data_range JSONB NOT NULL, -- Date range and other data scope
    status report_status_enum NOT NULL DEFAULT 'generating', -- 'generating', 'completed', 'failed'
    format report_format_enum NOT NULL, -- 'pdf', 'excel', 'csv', 'json'
    file_path VARCHAR(500), -- Generated report file location
    file_size_bytes BIGINT CHECK (file_size_bytes >= 0),
    generated_by UUID NOT NULL, -- User who requested the report
    access_permissions JSONB NOT NULL DEFAULT '{}', -- Who can access this report
    metadata JSONB NOT NULL DEFAULT '{}',
    expires_at TIMESTAMP WITH TIME ZONE, -- Auto-cleanup date
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT valid_report_completion CHECK (
        (status != 'completed') OR 
        (completed_at IS NOT NULL AND file_path IS NOT NULL)
    )
);

-- Indexes
CREATE INDEX idx_reports_type_status ON reports(report_type, status);
CREATE INDEX idx_reports_generated_by ON reports(generated_by);
CREATE INDEX idx_reports_created_at ON reports(created_at DESC);
CREATE INDEX idx_reports_expires_at ON reports(expires_at) WHERE expires_at IS NOT NULL;
```

### 7. Audit and Compliance

#### Audit Log Table
```sql
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL, -- Table/entity that was modified
    entity_id UUID NOT NULL, -- ID of the modified record
    action audit_action_enum NOT NULL, -- 'create', 'update', 'delete', 'view'
    user_id UUID, -- User who performed the action
    session_id VARCHAR(100), -- Session identifier
    ip_address INET, -- Client IP address
    user_agent TEXT, -- Client user agent
    changes JSONB, -- Before/after values for updates
    metadata JSONB DEFAULT '{}', -- Additional context
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp DESC);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_session_id ON audit_log(session_id) WHERE session_id IS NOT NULL;

-- Partition by month for performance
CREATE TABLE audit_log_y2025m01 PARTITION OF audit_log
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
-- Additional partitions created monthly
```

## TimescaleDB Time-Series Tables

### 1. Performance Metrics Hypertable

```sql
-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Performance metrics for monitoring and analytics
CREATE TABLE metrics (
    time TIMESTAMPTZ NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL, -- 'inspection', 'inference_job', 'system'
    entity_id UUID,
    value DOUBLE PRECISION NOT NULL,
    unit VARCHAR(20), -- 'seconds', 'bytes', 'count', 'percentage'
    tags JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}'
);

-- Convert to hypertable (partitioned by time)
SELECT create_hypertable('metrics', 'time', chunk_time_interval => INTERVAL '1 hour');

-- Indexes
CREATE INDEX idx_metrics_name_time ON metrics (metric_name, time DESC);
CREATE INDEX idx_metrics_entity ON metrics (entity_type, entity_id, time DESC);
CREATE INDEX idx_metrics_tags_gin ON metrics USING GIN(tags);

-- Compression policy (compress data older than 7 days)
ALTER TABLE metrics SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'metric_name, entity_type'
);

SELECT add_compression_policy('metrics', INTERVAL '7 days');

-- Retention policy (drop data older than 1 year)
SELECT add_retention_policy('metrics', INTERVAL '1 year');
```

### 2. System Events Hypertable

```sql
-- System and application events
CREATE TABLE events (
    time TIMESTAMPTZ NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    source VARCHAR(50) NOT NULL, -- 'api_gateway', 'inference_service', 'inspection_service'
    level event_level_enum NOT NULL, -- 'info', 'warning', 'error', 'critical'
    message TEXT NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    correlation_id UUID,
    request_id VARCHAR(100),
    user_id UUID,
    metadata JSONB DEFAULT '{}'
);

-- Convert to hypertable
SELECT create_hypertable('events', 'time', chunk_time_interval => INTERVAL '1 day');

-- Indexes
CREATE INDEX idx_events_type_time ON events (event_type, time DESC);
CREATE INDEX idx_events_level_time ON events (level, time DESC);
CREATE INDEX idx_events_source ON events (source, time DESC);
CREATE INDEX idx_events_correlation ON events (correlation_id) WHERE correlation_id IS NOT NULL;
CREATE INDEX idx_events_entity ON events (entity_type, entity_id, time DESC);

-- Compression and retention
ALTER TABLE events SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'event_type, source, level'
);

SELECT add_compression_policy('events', INTERVAL '3 days');
SELECT add_retention_policy('events', INTERVAL '90 days');
```

## Enumeration Types

```sql
-- Part types
CREATE TYPE part_type_enum AS ENUM (
    'pcb', 'semiconductor', 'component', 'assembly', 'wafer'
);

-- Lot status
CREATE TYPE lot_status_enum AS ENUM (
    'active', 'completed', 'quarantined', 'released', 'rejected'
);

-- Inspection types
CREATE TYPE inspection_type_enum AS ENUM (
    'visual', 'electrical', 'thermal', 'dimensional', 'functional', 'optical'
);

-- Inspection status
CREATE TYPE inspection_status_enum AS ENUM (
    'pending', 'in_progress', 'completed', 'failed', 'cancelled'
);

-- Defect types
CREATE TYPE defect_type_enum AS ENUM (
    'scratch', 'void', 'contamination', 'misalignment', 'short', 'open', 
    'crack', 'burn', 'foreign_object', 'delamination', 'corrosion'
);

-- Defect severity
CREATE TYPE defect_severity_enum AS ENUM (
    'low', 'medium', 'high', 'critical'
);

-- Detection methods
CREATE TYPE detection_method_enum AS ENUM (
    'ml_automated', 'manual_review', 'hybrid', 'rule_based'
);

-- Review status
CREATE TYPE review_status_enum AS ENUM (
    'pending', 'confirmed', 'rejected', 'needs_review', 'false_positive'
);

-- Inference status
CREATE TYPE inference_status_enum AS ENUM (
    'queued', 'processing', 'completed', 'failed', 'cancelled', 'timeout'
);

-- Artifact types
CREATE TYPE artifact_type_enum AS ENUM (
    'image', 'video', 'measurement', 'document', 'log', 'model_output'
);

-- Storage locations
CREATE TYPE storage_location_enum AS ENUM (
    'primary', 'archive', 'cold_storage', 'temporary'
);

-- Report types
CREATE TYPE report_type_enum AS ENUM (
    'inspection_summary', 'defect_analysis', 'quality_metrics', 
    'production_overview', 'compliance_report', 'performance_analysis'
);

-- Report status
CREATE TYPE report_status_enum AS ENUM (
    'generating', 'completed', 'failed', 'cancelled'
);

-- Report formats
CREATE TYPE report_format_enum AS ENUM (
    'pdf', 'excel', 'csv', 'json', 'html'
);

-- Audit actions
CREATE TYPE audit_action_enum AS ENUM (
    'create', 'update', 'delete', 'view', 'download', 'export'
);

-- Event levels
CREATE TYPE event_level_enum AS ENUM (
    'debug', 'info', 'warning', 'error', 'critical'
);
```

## Database Functions and Triggers

### 1. Updated Timestamp Trigger

```sql
-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to relevant tables
CREATE TRIGGER update_parts_updated_at 
    BEFORE UPDATE ON parts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_lots_updated_at 
    BEFORE UPDATE ON lots 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_inspections_updated_at 
    BEFORE UPDATE ON inspections 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_defects_updated_at 
    BEFORE UPDATE ON defects 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_inference_jobs_updated_at 
    BEFORE UPDATE ON inference_jobs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 2. Audit Trigger Function

```sql
-- Function to log changes to audit_log table
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
DECLARE
    changes JSONB;
BEGIN
    -- Determine the action and build changes object
    IF TG_OP = 'DELETE' THEN
        changes = jsonb_build_object('before', to_jsonb(OLD));
        INSERT INTO audit_log (entity_type, entity_id, action, changes)
        VALUES (TG_TABLE_NAME, OLD.id, 'delete', changes);
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        changes = jsonb_build_object('before', to_jsonb(OLD), 'after', to_jsonb(NEW));
        INSERT INTO audit_log (entity_type, entity_id, action, changes)
        VALUES (TG_TABLE_NAME, NEW.id, 'update', changes);
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        changes = jsonb_build_object('after', to_jsonb(NEW));
        INSERT INTO audit_log (entity_type, entity_id, action, changes)
        VALUES (TG_TABLE_NAME, NEW.id, 'create', changes);
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply audit triggers to critical tables
CREATE TRIGGER audit_parts_trigger
    AFTER INSERT OR UPDATE OR DELETE ON parts
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_inspections_trigger
    AFTER INSERT OR UPDATE OR DELETE ON inspections
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_defects_trigger
    AFTER INSERT OR UPDATE OR DELETE ON defects
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
```

### 3. Data Validation Functions

```sql
-- Function to validate defect location coordinates
CREATE OR REPLACE FUNCTION validate_defect_location(location JSONB)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN (
        location ? 'x' AND 
        location ? 'y' AND 
        location ? 'width' AND 
        location ? 'height' AND
        (location->>'x')::NUMERIC >= 0 AND
        (location->>'y')::NUMERIC >= 0 AND
        (location->>'width')::NUMERIC > 0 AND
        (location->>'height')::NUMERIC > 0
    );
END;
$$ LANGUAGE plpgsql;

-- Add constraint using the validation function
ALTER TABLE defects ADD CONSTRAINT valid_location_format 
    CHECK (validate_defect_location(location));
```

## Performance Optimization

### 1. Connection Pooling Configuration

```yaml
# PgBouncer configuration
[databases]
chip_quality = host=postgres-primary port=5432 dbname=chip_quality

[pgbouncer]
pool_mode = transaction
max_client_conn = 200
default_pool_size = 50
max_db_connections = 100
reserve_pool_size = 10
server_reset_query = DISCARD ALL
```

### 2. Query Optimization Guidelines

```sql
-- Example optimized query for inspection listing with filters
EXPLAIN (ANALYZE, BUFFERS) 
SELECT 
    i.id, i.lot_id, i.chip_id, i.inspection_type, i.status,
    i.created_at, l.lot_number, p.part_number
FROM inspections i
JOIN lots l ON i.lot_id = l.id
JOIN parts p ON l.part_id = p.id
WHERE 
    i.status = 'completed' 
    AND i.created_at >= '2025-10-01'::DATE
    AND i.created_at < '2025-11-01'::DATE
ORDER BY i.created_at DESC
LIMIT 50;

-- Recommended index for this query
CREATE INDEX idx_inspections_status_created_compound 
    ON inspections(status, created_at DESC) 
    WHERE status IN ('completed', 'failed');
```

### 3. Partitioning Strategy

```sql
-- Partition audit_log by month for better performance
CREATE TABLE audit_log_template (
    LIKE audit_log INCLUDING ALL
);

-- Create monthly partitions
CREATE TABLE audit_log_y2025m01 PARTITION OF audit_log 
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
CREATE TABLE audit_log_y2025m02 PARTITION OF audit_log 
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
-- Continue for each month...

-- Automatic partition creation function
CREATE OR REPLACE FUNCTION create_monthly_partitions()
RETURNS VOID AS $$
DECLARE
    start_date DATE;
    end_date DATE;
    table_name TEXT;
BEGIN
    start_date := date_trunc('month', CURRENT_DATE + INTERVAL '1 month');
    end_date := start_date + INTERVAL '1 month';
    table_name := 'audit_log_y' || extract(year from start_date) || 'm' || 
                  lpad(extract(month from start_date)::text, 2, '0');
    
    EXECUTE format('CREATE TABLE %I PARTITION OF audit_log FOR VALUES FROM (%L) TO (%L)',
                   table_name, start_date, end_date);
END;
$$ LANGUAGE plpgsql;
```

## Backup and Recovery

### 1. Backup Strategy

```bash
#!/bin/bash
# Automated backup script
DB_NAME="chip_quality"
BACKUP_DIR="/backups/postgresql"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Full database backup
pg_dump -h postgres-primary -U postgres -d $DB_NAME -F custom \
    --compress=9 --verbose \
    > "$BACKUP_DIR/full_backup_${TIMESTAMP}.dump"

# WAL archiving for point-in-time recovery
rsync -av /var/lib/postgresql/data/pg_wal/ "$BACKUP_DIR/wal_archive/"
```

### 2. Recovery Procedures

```sql
-- Point-in-time recovery example
-- 1. Restore from base backup
-- 2. Create recovery.conf
restore_command = 'cp /backups/wal_archive/%f "%p"'
recovery_target_time = '2025-10-30 14:30:00'
recovery_target_action = 'promote'
```

## Migration Management

### 1. Alembic Configuration

```python
# alembic/versions/001_initial_schema.py
"""Initial schema creation

Revision ID: 001
Revises: 
Create Date: 2025-10-30 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Create enum types first
    op.execute("CREATE TYPE part_type_enum AS ENUM ('pcb', 'semiconductor', 'component', 'assembly', 'wafer')")
    
    # Create tables
    op.create_table('parts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('part_number', sa.String(100), nullable=False),
        sa.Column('part_name', sa.String(200), nullable=False),
        sa.Column('part_type', postgresql.ENUM('pcb', 'semiconductor', 'component', 'assembly', 'wafer', name='part_type_enum'), nullable=False),
        sa.Column('specifications', postgresql.JSONB(), nullable=False, default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('part_number')
    )
    
    # Create indexes
    op.create_index('idx_parts_part_number', 'parts', ['part_number'])
    op.create_index('idx_parts_type', 'parts', ['part_type'])

def downgrade():
    op.drop_table('parts')
    op.execute("DROP TYPE part_type_enum")
```

### 2. Data Migration Scripts

```python
# migrations/data/seed_base_data.py
"""Seed database with initial reference data"""

def seed_initial_data():
    # Base part types and inspection standards
    reference_parts = [
        {
            'part_number': 'REF-PCB-STD-001',
            'part_name': 'Standard PCB Reference',
            'part_type': 'pcb',
            'specifications': {
                'dimensions': {'width': 100, 'height': 80, 'thickness': 1.6},
                'layers': 4,
                'material': 'FR-4'
            }
        }
    ]
    
    # Insert reference data
    for part_data in reference_parts:
        # Implementation here
        pass
```

## Security Considerations

### 1. Row Level Security (RLS)

```sql
-- Enable RLS on sensitive tables
ALTER TABLE inspections ENABLE ROW LEVEL SECURITY;
ALTER TABLE defects ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;

-- Create policies based on user roles
CREATE POLICY inspection_access_policy ON inspections
    FOR ALL TO application_user
    USING (
        -- Users can only access inspections from their assigned stations
        EXISTS (
            SELECT 1 FROM user_station_access usa 
            WHERE usa.user_id = current_setting('app.current_user_id')::UUID
            AND usa.station_id = inspections.station_id
        )
    );

CREATE POLICY defect_access_policy ON defects
    FOR ALL TO application_user
    USING (
        EXISTS (
            SELECT 1 FROM inspections i
            JOIN user_station_access usa ON usa.station_id = i.station_id
            WHERE i.id = defects.inspection_id
            AND usa.user_id = current_setting('app.current_user_id')::UUID
        )
    );
```

### 2. Data Encryption

```sql
-- Encrypt sensitive fields
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Function to encrypt PII data
CREATE OR REPLACE FUNCTION encrypt_pii(data TEXT, key TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN encode(encrypt(data::bytea, key::bytea, 'aes'), 'base64');
END;
$$ LANGUAGE plpgsql;

-- Function to decrypt PII data
CREATE OR REPLACE FUNCTION decrypt_pii(encrypted_data TEXT, key TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN convert_from(decrypt(decode(encrypted_data, 'base64'), key::bytea, 'aes'), 'UTF8');
END;
$$ LANGUAGE plpgsql;
```

## Monitoring and Alerting

### 1. Database Health Queries

```sql
-- Query to monitor database performance
CREATE VIEW db_health_summary AS
SELECT 
    'connections' as metric,
    count(*) as value,
    max_conn.setting::int as max_value,
    (count(*) * 100.0 / max_conn.setting::int) as percentage
FROM pg_stat_activity
CROSS JOIN (SELECT setting FROM pg_settings WHERE name = 'max_connections') max_conn
WHERE state = 'active'
UNION ALL
SELECT 
    'cache_hit_ratio' as metric,
    round((sum(blks_hit) * 100.0 / NULLIF(sum(blks_hit + blks_read), 0))::numeric, 2) as value,
    100 as max_value,
    round((sum(blks_hit) * 100.0 / NULLIF(sum(blks_hit + blks_read), 0))::numeric, 2) as percentage
FROM pg_stat_database;

-- Long-running queries monitoring
CREATE VIEW long_running_queries AS
SELECT 
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query,
    state,
    application_name
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes'
AND state = 'active';
```

### 2. Custom Metrics Collection

```sql
-- Function to collect table statistics
CREATE OR REPLACE FUNCTION collect_table_stats()
RETURNS TABLE(
    table_name TEXT,
    row_count BIGINT,
    size_bytes BIGINT,
    index_size_bytes BIGINT,
    last_vacuum TIMESTAMP,
    last_analyze TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        schemaname||'.'||relname as table_name,
        n_tup_ins + n_tup_upd + n_tup_del as row_count,
        pg_total_relation_size(schemaname||'.'||relname) as size_bytes,
        pg_indexes_size(schemaname||'.'||relname) as index_size_bytes,
        last_vacuum,
        last_analyze
    FROM pg_stat_user_tables
    ORDER BY pg_total_relation_size(schemaname||'.'||relname) DESC;
END;
$$ LANGUAGE plpgsql;
```

This comprehensive database schema documentation provides the foundation for implementing a production-ready chip quality platform with proper data modeling, performance optimization, security, and operational considerations.