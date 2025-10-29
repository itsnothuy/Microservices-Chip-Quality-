"""Initial schema migration

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-10-29

Implements complete database schema from docs/database/schema.md including:
- Enum types
- Core tables (parts, lots, inspections, defects, etc.)
- Indexes and constraints
- Triggers for updated_at timestamps
- TimescaleDB extensions and hypertables
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema"""
    
    # =========================================================================
    # 1. CREATE ENUM TYPES
    # =========================================================================
    
    # Part type enumeration
    op.execute("""
        CREATE TYPE part_type_enum AS ENUM (
            'pcb', 'semiconductor', 'component', 'assembly', 'wafer'
        )
    """)
    
    # Lot status enumeration
    op.execute("""
        CREATE TYPE lot_status_enum AS ENUM (
            'active', 'completed', 'quarantined', 'released', 'rejected'
        )
    """)
    
    # Inspection type enumeration
    op.execute("""
        CREATE TYPE inspection_type_enum AS ENUM (
            'visual', 'electrical', 'thermal', 'dimensional', 'functional', 'optical'
        )
    """)
    
    # Inspection status enumeration
    op.execute("""
        CREATE TYPE inspection_status_enum AS ENUM (
            'pending', 'in_progress', 'completed', 'failed', 'cancelled'
        )
    """)
    
    # Defect type enumeration
    op.execute("""
        CREATE TYPE defect_type_enum AS ENUM (
            'scratch', 'void', 'contamination', 'misalignment', 'short', 'open', 
            'crack', 'burn', 'foreign_object', 'delamination', 'corrosion'
        )
    """)
    
    # Defect severity enumeration
    op.execute("""
        CREATE TYPE defect_severity_enum AS ENUM (
            'low', 'medium', 'high', 'critical'
        )
    """)
    
    # Detection method enumeration
    op.execute("""
        CREATE TYPE detection_method_enum AS ENUM (
            'ml_automated', 'manual_review', 'hybrid', 'rule_based'
        )
    """)
    
    # Review status enumeration
    op.execute("""
        CREATE TYPE review_status_enum AS ENUM (
            'pending', 'confirmed', 'rejected', 'needs_review', 'false_positive'
        )
    """)
    
    # Inference status enumeration
    op.execute("""
        CREATE TYPE inference_status_enum AS ENUM (
            'queued', 'processing', 'completed', 'failed', 'cancelled', 'timeout'
        )
    """)
    
    # Artifact type enumeration
    op.execute("""
        CREATE TYPE artifact_type_enum AS ENUM (
            'image', 'video', 'measurement', 'document', 'log', 'model_output'
        )
    """)
    
    # Storage location enumeration
    op.execute("""
        CREATE TYPE storage_location_enum AS ENUM (
            'primary', 'archive', 'cold_storage', 'temporary'
        )
    """)
    
    # Report type enumeration
    op.execute("""
        CREATE TYPE report_type_enum AS ENUM (
            'inspection_summary', 'defect_analysis', 'quality_metrics', 
            'production_overview', 'compliance_report', 'performance_analysis'
        )
    """)
    
    # Report status enumeration
    op.execute("""
        CREATE TYPE report_status_enum AS ENUM (
            'generating', 'completed', 'failed', 'cancelled'
        )
    """)
    
    # Report format enumeration
    op.execute("""
        CREATE TYPE report_format_enum AS ENUM (
            'pdf', 'excel', 'csv', 'json', 'html'
        )
    """)
    
    # Audit action enumeration
    op.execute("""
        CREATE TYPE audit_action_enum AS ENUM (
            'create', 'update', 'delete', 'view', 'download', 'export'
        )
    """)
    
    # Event level enumeration
    op.execute("""
        CREATE TYPE event_level_enum AS ENUM (
            'debug', 'info', 'warning', 'error', 'critical'
        )
    """)
    
    # =========================================================================
    # 2. CREATE CORE TABLES
    # =========================================================================
    
    # Parts table
    op.create_table(
        'parts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('part_number', sa.String(100), nullable=False, unique=True),
        sa.Column('part_name', sa.String(200), nullable=False),
        sa.Column('part_type', postgresql.ENUM('pcb', 'semiconductor', 'component', 'assembly', 'wafer', name='part_type_enum'), nullable=False),
        sa.Column('specifications', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('tolerance_requirements', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
    )
    
    # Lots table
    op.create_table(
        'lots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('lot_number', sa.String(100), nullable=False, unique=True),
        sa.Column('part_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('parts.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('production_date', sa.Date, nullable=False),
        sa.Column('batch_size', sa.Integer, nullable=False),
        sa.Column('production_line', sa.String(50), nullable=False),
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('quality_requirements', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('metadata', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('status', postgresql.ENUM('active', 'completed', 'quarantined', 'released', 'rejected', name='lot_status_enum'), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint('batch_size > 0', name='check_batch_size_positive'),
    )
    
    # Inspections table
    op.create_table(
        'inspections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('lot_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lots.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('chip_id', sa.String(100), nullable=False),
        sa.Column('inspection_type', postgresql.ENUM('visual', 'electrical', 'thermal', 'dimensional', 'functional', 'optical', name='inspection_type_enum'), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'in_progress', 'completed', 'failed', 'cancelled', name='inspection_status_enum'), nullable=False, server_default='pending'),
        sa.Column('priority', sa.Integer, nullable=False, server_default='5'),
        sa.Column('station_id', sa.String(50), nullable=False),
        sa.Column('operator_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint('priority >= 1 AND priority <= 10', name='check_priority_range'),
        sa.CheckConstraint(
            '(completed_at IS NULL) OR (started_at IS NOT NULL AND completed_at >= started_at)',
            name='check_valid_completion_order'
        ),
        sa.UniqueConstraint('lot_id', 'chip_id', 'inspection_type', name='unique_inspection_per_chip'),
    )
    
    # Defects table
    op.create_table(
        'defects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('inspection_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('inspections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('defect_type', postgresql.ENUM('scratch', 'void', 'contamination', 'misalignment', 'short', 'open', 'crack', 'burn', 'foreign_object', 'delamination', 'corrosion', name='defect_type_enum'), nullable=False),
        sa.Column('severity', postgresql.ENUM('low', 'medium', 'high', 'critical', name='defect_severity_enum'), nullable=False),
        sa.Column('confidence', sa.Numeric(5, 4), nullable=False),
        sa.Column('location', postgresql.JSONB, nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('detection_method', postgresql.ENUM('ml_automated', 'manual_review', 'hybrid', 'rule_based', name='detection_method_enum'), nullable=False),
        sa.Column('reviewer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('review_status', postgresql.ENUM('pending', 'confirmed', 'rejected', 'needs_review', 'false_positive', name='review_status_enum'), nullable=True, server_default='pending'),
        sa.Column('corrective_action', sa.Text, nullable=True),
        sa.Column('artifact_references', postgresql.JSONB, nullable=True, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint('confidence >= 0 AND confidence <= 1', name='check_confidence_range'),
    )
    
    # Inference Jobs table
    op.create_table(
        'inference_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('inspection_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('inspections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('model_version', sa.String(20), nullable=False),
        sa.Column('status', postgresql.ENUM('queued', 'processing', 'completed', 'failed', 'cancelled', 'timeout', name='inference_status_enum'), nullable=False, server_default='queued'),
        sa.Column('priority', sa.Integer, nullable=False, server_default='5'),
        sa.Column('batch_size', sa.Integer, nullable=False, server_default='1'),
        sa.Column('confidence_threshold', sa.Numeric(5, 4), nullable=False, server_default='0.7'),
        sa.Column('processing_parameters', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('input_artifacts', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('output_artifacts', postgresql.JSONB, nullable=True, server_default='[]'),
        sa.Column('triton_request_id', sa.String(100), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('performance_metrics', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('queued_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint('priority >= 1 AND priority <= 10', name='check_inference_priority_range'),
        sa.CheckConstraint('batch_size > 0', name='check_inference_batch_size_positive'),
        sa.CheckConstraint(
            '(started_at IS NULL OR started_at >= queued_at) AND '
            '(completed_at IS NULL OR (started_at IS NOT NULL AND completed_at >= started_at))',
            name='check_valid_job_timing'
        ),
    )
    
    # Artifacts table
    op.create_table(
        'artifacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('inspection_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('inspections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('inference_job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('inference_jobs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('artifact_type', postgresql.ENUM('image', 'video', 'measurement', 'document', 'log', 'model_output', name='artifact_type_enum'), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False, unique=True),
        sa.Column('content_type', sa.String(100), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger, nullable=False),
        sa.Column('checksum_sha256', sa.CHAR(64), nullable=False),
        sa.Column('storage_location', postgresql.ENUM('primary', 'archive', 'cold_storage', 'temporary', name='storage_location_enum'), nullable=False, server_default='primary'),
        sa.Column('metadata', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('tags', postgresql.ARRAY(sa.Text), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('file_size_bytes >= 0', name='check_file_size_non_negative'),
        sa.CheckConstraint("checksum_sha256 ~ '^[a-f0-9]{64}$'", name='check_valid_checksum'),
    )
    
    # Reports table
    op.create_table(
        'reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('report_type', postgresql.ENUM('inspection_summary', 'defect_analysis', 'quality_metrics', 'production_overview', 'compliance_report', 'performance_analysis', name='report_type_enum'), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('filters', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('data_range', postgresql.JSONB, nullable=False),
        sa.Column('status', postgresql.ENUM('generating', 'completed', 'failed', 'cancelled', name='report_status_enum'), nullable=False, server_default='generating'),
        sa.Column('format', postgresql.ENUM('pdf', 'excel', 'csv', 'json', 'html', name='report_format_enum'), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('file_size_bytes', sa.BigInteger, nullable=True),
        sa.Column('generated_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('access_permissions', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('metadata', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('file_size_bytes IS NULL OR file_size_bytes >= 0', name='check_report_file_size_non_negative'),
        sa.CheckConstraint(
            "(status != 'completed') OR (completed_at IS NOT NULL AND file_path IS NOT NULL)",
            name='check_valid_report_completion'
        ),
    )
    
    # Audit Log table
    op.create_table(
        'audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', postgresql.ENUM('create', 'update', 'delete', 'view', 'download', 'export', name='audit_action_enum'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('ip_address', postgresql.INET, nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('changes', postgresql.JSONB, nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # =========================================================================
    # 3. CREATE INDEXES
    # =========================================================================
    
    # Parts indexes
    op.create_index('idx_parts_part_number', 'parts', ['part_number'])
    op.create_index('idx_parts_type', 'parts', ['part_type'])
    op.create_index('idx_parts_specifications_gin', 'parts', ['specifications'], postgresql_using='gin')
    op.create_index('idx_parts_updated_at', 'parts', [sa.text('updated_at DESC')])
    
    # Lots indexes
    op.create_index('idx_lots_lot_number', 'lots', ['lot_number'])
    op.create_index('idx_lots_part_id', 'lots', ['part_id'])
    op.create_index('idx_lots_production_date', 'lots', [sa.text('production_date DESC')])
    op.create_index('idx_lots_status', 'lots', ['status'])
    op.create_index('idx_lots_production_line', 'lots', ['production_line'])
    
    # Inspections indexes
    op.create_index('idx_inspections_lot_id', 'inspections', ['lot_id'])
    op.create_index('idx_inspections_chip_id', 'inspections', ['chip_id'])
    op.create_index('idx_inspections_status_created', 'inspections', ['status', sa.text('created_at DESC')])
    op.create_index('idx_inspections_type_status', 'inspections', ['inspection_type', 'status'])
    op.create_index('idx_inspections_station_id', 'inspections', ['station_id'])
    op.create_index('idx_inspections_priority_created', 'inspections', [sa.text('priority DESC'), sa.text('created_at ASC')])
    op.create_index('idx_inspections_metadata_gin', 'inspections', ['metadata'], postgresql_using='gin')
    
    # Defects indexes
    op.create_index('idx_defects_inspection_id', 'defects', ['inspection_id'])
    op.create_index('idx_defects_type_severity', 'defects', ['defect_type', 'severity'])
    op.create_index('idx_defects_confidence', 'defects', [sa.text('confidence DESC')])
    op.create_index('idx_defects_review_status', 'defects', ['review_status'])
    op.create_index('idx_defects_detection_method', 'defects', ['detection_method'])
    op.create_index('idx_defects_created_at', 'defects', [sa.text('created_at DESC')])
    
    # Inference Jobs indexes
    op.create_index('idx_inference_jobs_inspection_id', 'inference_jobs', ['inspection_id'])
    op.create_index('idx_inference_jobs_status_priority', 'inference_jobs', ['status', sa.text('priority DESC'), sa.text('queued_at ASC')])
    op.create_index('idx_inference_jobs_model', 'inference_jobs', ['model_name', 'model_version'])
    op.create_index('idx_inference_jobs_triton_request', 'inference_jobs', ['triton_request_id'], postgresql_where=sa.text('triton_request_id IS NOT NULL'))
    op.create_index('idx_inference_jobs_created_at', 'inference_jobs', [sa.text('created_at DESC')])
    
    # Artifacts indexes
    op.create_index('idx_artifacts_inspection_id', 'artifacts', ['inspection_id'])
    op.create_index('idx_artifacts_inference_job_id', 'artifacts', ['inference_job_id'], postgresql_where=sa.text('inference_job_id IS NOT NULL'))
    op.create_index('idx_artifacts_type', 'artifacts', ['artifact_type'])
    op.create_index('idx_artifacts_file_path', 'artifacts', ['file_path'])
    op.create_index('idx_artifacts_checksum', 'artifacts', ['checksum_sha256'])
    op.create_index('idx_artifacts_tags_gin', 'artifacts', ['tags'], postgresql_using='gin')
    op.create_index('idx_artifacts_created_at', 'artifacts', [sa.text('created_at DESC')])
    op.create_index('idx_artifacts_storage_location', 'artifacts', ['storage_location'])
    
    # Reports indexes
    op.create_index('idx_reports_type_status', 'reports', ['report_type', 'status'])
    op.create_index('idx_reports_generated_by', 'reports', ['generated_by'])
    op.create_index('idx_reports_created_at', 'reports', [sa.text('created_at DESC')])
    op.create_index('idx_reports_expires_at', 'reports', ['expires_at'], postgresql_where=sa.text('expires_at IS NOT NULL'))
    
    # Audit Log indexes
    op.create_index('idx_audit_log_entity', 'audit_log', ['entity_type', 'entity_id'])
    op.create_index('idx_audit_log_user_id', 'audit_log', ['user_id'], postgresql_where=sa.text('user_id IS NOT NULL'))
    op.create_index('idx_audit_log_timestamp', 'audit_log', [sa.text('timestamp DESC')])
    op.create_index('idx_audit_log_action', 'audit_log', ['action'])
    op.create_index('idx_audit_log_session_id', 'audit_log', ['session_id'], postgresql_where=sa.text('session_id IS NOT NULL'))
    
    # =========================================================================
    # 4. CREATE TRIGGERS FOR UPDATED_AT
    # =========================================================================
    
    # Function to update the updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Apply trigger to relevant tables
    for table_name in ['parts', 'lots', 'inspections', 'defects', 'inference_jobs']:
        op.execute(f"""
            CREATE TRIGGER update_{table_name}_updated_at
                BEFORE UPDATE ON {table_name}
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    """Drop all database objects"""
    
    # Drop triggers first
    for table_name in ['parts', 'lots', 'inspections', 'defects', 'inference_jobs']:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table_name}_updated_at ON {table_name}")
    
    # Drop function
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
    
    # Drop indexes (most will be dropped with tables, but explicit for clarity)
    # Note: Indexes are automatically dropped when tables are dropped
    
    # Drop tables in reverse order (respecting foreign key dependencies)
    op.drop_table('audit_log')
    op.drop_table('reports')
    op.drop_table('artifacts')
    op.drop_table('inference_jobs')
    op.drop_table('defects')
    op.drop_table('inspections')
    op.drop_table('lots')
    op.drop_table('parts')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS event_level_enum")
    op.execute("DROP TYPE IF EXISTS audit_action_enum")
    op.execute("DROP TYPE IF EXISTS report_format_enum")
    op.execute("DROP TYPE IF EXISTS report_status_enum")
    op.execute("DROP TYPE IF EXISTS report_type_enum")
    op.execute("DROP TYPE IF EXISTS storage_location_enum")
    op.execute("DROP TYPE IF EXISTS artifact_type_enum")
    op.execute("DROP TYPE IF EXISTS inference_status_enum")
    op.execute("DROP TYPE IF EXISTS review_status_enum")
    op.execute("DROP TYPE IF EXISTS detection_method_enum")
    op.execute("DROP TYPE IF EXISTS defect_severity_enum")
    op.execute("DROP TYPE IF EXISTS defect_type_enum")
    op.execute("DROP TYPE IF EXISTS inspection_status_enum")
    op.execute("DROP TYPE IF EXISTS inspection_type_enum")
    op.execute("DROP TYPE IF EXISTS lot_status_enum")
    op.execute("DROP TYPE IF EXISTS part_type_enum")
