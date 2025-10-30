"""Reporting models for quality reports and analytics."""

from decimal import Decimal
from typing import Dict, Any, Optional, List
from datetime import datetime, date

from sqlalchemy import (
    Column, String, Text, Integer, DateTime, Date,
    ForeignKey, Index, Boolean, Float
)
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY
from sqlalchemy.orm import relationship, validates

from database.base import BaseModel, TimestampMixin
from database.enums import ReportTypeEnum, ReportStatusEnum, ReportFormatEnum


class Report(BaseModel, TimestampMixin):
    """Quality reports and analytics generation tracking."""
    
    __tablename__ = "reports"
    
    # Core identification
    report_id = Column(
        String(50),
        nullable=False,
        unique=True,
        comment="Unique report identifier"
    )
    report_name = Column(
        String(200),
        nullable=False,
        comment="Human-readable report name"
    )
    report_type = Column(
        ReportTypeEnum,
        nullable=False,
        comment="Type of report (quality, production, etc.)"
    )
    
    # Report content and configuration
    template_id = Column(
        String(50),
        nullable=True,
        comment="Report template identifier"
    )
    template_version = Column(
        String(20),
        nullable=True,
        comment="Template version used"
    )
    parameters = Column(
        JSONB,
        nullable=True,
        comment="Report generation parameters"
    )
    filters = Column(
        JSONB,
        nullable=True,
        comment="Data filters applied to the report"
    )
    
    # Time period covered by the report
    period_start = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Start of the reporting period"
    )
    period_end = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="End of the reporting period"
    )
    report_date = Column(
        Date,
        nullable=False,
        default=date.today,
        comment="Date when report was generated"
    )
    
    # Generation information
    status = Column(
        ReportStatusEnum,
        nullable=False,
        default=ReportStatusEnum.PENDING,
        comment="Current report generation status"
    )
    requested_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="When report was requested"
    )
    started_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When report generation started"
    )
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When report generation completed"
    )
    
    # Output formats and files
    output_formats = Column(
        ARRAY(ReportFormatEnum),
        nullable=True,
        comment="Generated output formats"
    )
    output_files = Column(
        JSONB,
        nullable=True,
        comment="Generated output file references"
    )
    file_size = Column(
        Integer,
        nullable=True,
        comment="Total size of generated files in bytes"
    )
    
    # Data and metrics
    data_sources = Column(
        JSONB,
        nullable=True,
        comment="Data sources used for the report"
    )
    record_count = Column(
        Integer,
        nullable=True,
        comment="Number of records processed"
    )
    summary_metrics = Column(
        JSONB,
        nullable=True,
        comment="Key summary metrics and statistics"
    )
    
    # Quality and validation
    data_quality_score = Column(
        Float,
        nullable=True,
        comment="Data quality score (0.0 to 1.0)"
    )
    completeness_score = Column(
        Float,
        nullable=True,
        comment="Data completeness score (0.0 to 1.0)"
    )
    validation_results = Column(
        JSONB,
        nullable=True,
        comment="Data validation results"
    )
    
    # Performance metrics
    generation_time_ms = Column(
        Integer,
        nullable=True,
        comment="Report generation time in milliseconds"
    )
    query_time_ms = Column(
        Integer,
        nullable=True,
        comment="Data query time in milliseconds"
    )
    rendering_time_ms = Column(
        Integer,
        nullable=True,
        comment="Report rendering time in milliseconds"
    )
    
    # Access and security
    is_public = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether report is publicly accessible"
    )
    access_permissions = Column(
        JSONB,
        nullable=True,
        comment="Access permissions and restrictions"
    )
    security_classification = Column(
        String(50),
        nullable=True,
        comment="Security classification level"
    )
    
    # Lifecycle management
    expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When report expires and can be deleted"
    )
    is_archived = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether report is archived"
    )
    archived_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When report was archived"
    )
    retention_policy = Column(
        String(50),
        nullable=True,
        comment="Retention policy identifier"
    )
    
    # User and session information
    requested_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User who requested the report"
    )
    generated_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User/system that generated the report"
    )
    session_id = Column(
        String(100),
        nullable=True,
        comment="Session identifier"
    )
    
    # Distribution and notifications
    distribution_list = Column(
        JSONB,
        nullable=True,
        comment="Distribution list for automated sharing"
    )
    notification_sent = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether completion notification was sent"
    )
    notification_sent_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When notification was sent"
    )
    
    # Error handling
    error_message = Column(
        Text,
        nullable=True,
        comment="Error message if generation failed"
    )
    error_code = Column(
        String(50),
        nullable=True,
        comment="Error code for categorization"
    )
    retry_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of retry attempts"
    )
    
    # External integration
    external_id = Column(
        String(100),
        nullable=True,
        comment="External system identifier"
    )
    webhook_url = Column(
        String(500),
        nullable=True,
        comment="Webhook URL for completion notification"
    )
    correlation_id = Column(
        String(100),
        nullable=True,
        comment="Correlation ID for tracking"
    )
    
    # Custom fields
    custom_fields = Column(
        JSONB,
        nullable=True,
        comment="Custom report fields and metadata"
    )
    tags = Column(
        ARRAY(String(50)),
        nullable=True,
        comment="Tags for categorization and search"
    )
    notes = Column(
        Text,
        nullable=True,
        comment="Additional notes and comments"
    )
    
    # Version control
    version = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Report version number"
    )
    parent_report_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="SET NULL"),
        nullable=True,
        comment="Parent report (for revisions)"
    )
    
    # Relationships
    parent_report = relationship(
        "Report",
        remote_side=[BaseModel.id],
        foreign_keys=[parent_report_id]
    )
    child_reports = relationship(
        "Report",
        remote_side=[parent_report_id],
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_reports_id", "report_id"),
        Index("idx_reports_type", "report_type"),
        Index("idx_reports_status", "status"),
        Index("idx_reports_date", "report_date"),
        Index("idx_reports_period", "period_start", "period_end"),
        Index("idx_reports_requested_by", "requested_by"),
        Index("idx_reports_template", "template_id"),
        Index("idx_reports_public", "is_public"),
        Index("idx_reports_archived", "is_archived"),
        Index("idx_reports_expires", "expires_at"),
        Index("idx_reports_correlation", "correlation_id"),
        Index("idx_reports_tags", "tags", postgresql_using="gin"),
        Index("idx_reports_parameters", "parameters", postgresql_using="gin"),
        Index("idx_reports_summary", "summary_metrics", postgresql_using="gin"),
    )
    
    @validates('report_id')
    def validate_report_id(self, key, value):
        """Validate report ID format."""
        if not value or len(value.strip()) < 5:
            raise ValueError("Report ID must be at least 5 characters")
        return value.strip()
    
    @validates('report_name')
    def validate_report_name(self, key, value):
        """Validate report name."""
        if not value or len(value.strip()) < 3:
            raise ValueError("Report name must be at least 3 characters")
        return value.strip()
    
    @validates('data_quality_score')
    def validate_data_quality_score(self, key, value):
        """Validate data quality score is between 0 and 1."""
        if value is not None and not (0 <= value <= 1):
            raise ValueError("Data quality score must be between 0 and 1")
        return value
    
    @validates('completeness_score')
    def validate_completeness_score(self, key, value):
        """Validate completeness score is between 0 and 1."""
        if value is not None and not (0 <= value <= 1):
            raise ValueError("Completeness score must be between 0 and 1")
        return value
    
    @validates('period_start', 'period_end')
    def validate_period(self, key, value):
        """Validate reporting period dates."""
        if key == 'period_end' and value and self.period_start:
            if value < self.period_start:
                raise ValueError("Period end must be after period start")
        return value
    
    def __repr__(self):
        return f"<Report(id='{self.report_id}', type='{self.report_type}', status='{self.status}')>"
    
    @property
    def is_completed(self) -> bool:
        """Check if report generation is completed."""
        return self.status == ReportStatusEnum.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Check if report generation failed."""
        return self.status == ReportStatusEnum.FAILED
    
    @property
    def is_processing(self) -> bool:
        """Check if report is currently being generated."""
        return self.status == ReportStatusEnum.GENERATING
    
    @property
    def is_expired(self) -> bool:
        """Check if report has expired."""
        return self.expires_at is not None and self.expires_at < datetime.utcnow()
    
    @property
    def generation_duration_ms(self) -> Optional[int]:
        """Calculate report generation duration in milliseconds."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() * 1000)
        return None
    
    @property
    def queue_duration_ms(self) -> Optional[int]:
        """Calculate queue waiting time in milliseconds."""
        if self.requested_at and self.started_at:
            delta = self.started_at - self.requested_at
            return int(delta.total_seconds() * 1000)
        return None
    
    @property
    def period_duration_days(self) -> Optional[int]:
        """Calculate reporting period duration in days."""
        if self.period_start and self.period_end:
            delta = self.period_end.date() - self.period_start.date()
            return delta.days
        return None
    
    @property
    def file_size_mb(self) -> float:
        """Get file size in MB."""
        return self.file_size / (1024 * 1024) if self.file_size else 0
    
    def has_format(self, format_type: ReportFormatEnum) -> bool:
        """Check if report has a specific output format."""
        return self.output_formats is not None and format_type in self.output_formats
    
    def add_output_format(self, format_type: ReportFormatEnum):
        """Add an output format to the report."""
        if self.output_formats is None:
            self.output_formats = []
        if format_type not in self.output_formats:
            self.output_formats.append(format_type)
    
    def get_file_reference(self, format_type: ReportFormatEnum) -> Optional[str]:
        """Get file reference for a specific format."""
        if self.output_files and format_type.value in self.output_files:
            return self.output_files[format_type.value]
        return None
    
    def add_tag(self, tag: str):
        """Add a tag to the report."""
        if self.tags is None:
            self.tags = []
        tag = tag.strip().lower()
        if tag and tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str):
        """Remove a tag from the report."""
        if self.tags:
            tag = tag.strip().lower()
            self.tags = [t for t in self.tags if t != tag]
    
    def has_tag(self, tag: str) -> bool:
        """Check if report has a specific tag."""
        return self.tags is not None and tag.strip().lower() in self.tags
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        return {
            "generation_duration_ms": self.generation_duration_ms,
            "queue_duration_ms": self.queue_duration_ms,
            "generation_time_ms": self.generation_time_ms,
            "query_time_ms": self.query_time_ms,
            "rendering_time_ms": self.rendering_time_ms,
            "record_count": self.record_count,
            "file_size_mb": self.file_size_mb,
            "data_quality_score": self.data_quality_score,
            "completeness_score": self.completeness_score,
            "period_duration_days": self.period_duration_days,
        }
    
    def update_status(self, new_status: ReportStatusEnum, error_message: str = None):
        """Update report status with timestamp tracking."""
        old_status = self.status
        self.status = new_status
        
        now = datetime.utcnow()
        
        if new_status == ReportStatusEnum.GENERATING and old_status != ReportStatusEnum.GENERATING:
            self.started_at = now
        elif new_status in [ReportStatusEnum.COMPLETED, ReportStatusEnum.FAILED]:
            self.completed_at = now
            
        if new_status == ReportStatusEnum.FAILED:
            self.error_message = error_message
            self.retry_count += 1