"""
Database models for reports.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
import enum

from sqlalchemy import (
    Column, String, DateTime, Enum, Integer, BigInteger, JSON, Text, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ReportTypeEnum(str, enum.Enum):
    """Report types"""
    INSPECTION_SUMMARY = "inspection_summary"
    DEFECT_ANALYSIS = "defect_analysis"
    QUALITY_METRICS = "quality_metrics"
    PRODUCTION_OVERVIEW = "production_overview"
    COMPLIANCE_REPORT = "compliance_report"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    SPC_ANALYSIS = "spc_analysis"
    TREND_ANALYSIS = "trend_analysis"
    CUSTOM = "custom"


class ReportStatusEnum(str, enum.Enum):
    """Report generation status"""
    QUEUED = "queued"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReportFormatEnum(str, enum.Enum):
    """Report output formats"""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    HTML = "html"


class Report(Base):
    """Report entity"""
    __tablename__ = "reports"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    report_type = Column(Enum(ReportTypeEnum), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Report parameters
    filters = Column(JSON, nullable=False, default=dict)
    data_range = Column(JSON, nullable=False)
    
    # Status tracking
    status = Column(Enum(ReportStatusEnum), nullable=False, default=ReportStatusEnum.QUEUED, index=True)
    format = Column(Enum(ReportFormatEnum), nullable=False)
    
    # File information
    file_path = Column(String(500), nullable=True)
    file_size_bytes = Column(BigInteger, nullable=True)
    
    # Access control
    generated_by = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    access_permissions = Column(JSON, nullable=False, default=dict)
    
    # Metadata and error tracking
    report_metadata = Column(JSON, nullable=False, default=dict)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True, index=True)
    
    __table_args__ = (
        CheckConstraint(
            "(status != 'completed') OR (completed_at IS NOT NULL AND file_path IS NOT NULL)",
            name="valid_report_completion"
        ),
        CheckConstraint(
            "file_size_bytes IS NULL OR file_size_bytes >= 0",
            name="valid_file_size"
        ),
    )
    
    def __repr__(self) -> str:
        return f"<Report(id={self.id}, type={self.report_type}, status={self.status})>"


class ReportTemplate(Base):
    """Report template"""
    __tablename__ = "report_templates"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False, unique=True, index=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Template configuration
    report_type = Column(Enum(ReportTypeEnum), nullable=False, index=True)
    template_content = Column(Text, nullable=False)
    supported_formats = Column(JSON, nullable=False, default=list)
    
    # Template parameters
    parameters = Column(JSON, nullable=False, default=dict)
    default_filters = Column(JSON, nullable=False, default=dict)
    
    # Versioning
    version = Column(Integer, nullable=False, default=1)
    is_active = Column(String(10), nullable=False, default="true")
    
    # Metadata
    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<ReportTemplate(id={self.id}, name={self.name}, type={self.report_type})>"


class ScheduledReport(Base):
    """Scheduled report configuration"""
    __tablename__ = "scheduled_reports"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Schedule configuration
    report_type = Column(Enum(ReportTypeEnum), nullable=False)
    format = Column(Enum(ReportFormatEnum), nullable=False)
    
    # Schedule pattern (cron-like)
    schedule_pattern = Column(String(100), nullable=False)  # e.g., "0 9 * * MON"
    timezone = Column(String(50), nullable=False, default="UTC")
    
    # Report parameters
    filters = Column(JSON, nullable=False, default=dict)
    parameters = Column(JSON, nullable=False, default=dict)
    
    # Distribution
    recipients = Column(JSON, nullable=False, default=list)  # Email addresses
    
    # Status
    is_active = Column(String(10), nullable=False, default="true", index=True)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True, index=True)
    
    # Metadata
    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<ScheduledReport(id={self.id}, name={self.name}, active={self.is_active})>"
