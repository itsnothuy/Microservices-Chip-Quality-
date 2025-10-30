"""ML inference models for tracking inference jobs and results."""

from decimal import Decimal
from typing import Dict, Any, Optional
from datetime import datetime

from sqlalchemy import (
    Column, String, Text, Integer, Numeric, DateTime,
    ForeignKey, Index, Boolean, Float
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship, validates

from database.base import BaseModel, TimestampMixin
from database.enums import InferenceStatusEnum


class InferenceJob(BaseModel, TimestampMixin):
    """ML inference job tracking and results management."""
    
    __tablename__ = "inference_jobs"
    
    # Core identification
    job_id = Column(
        String(50),
        nullable=False,
        unique=True,
        comment="Unique inference job identifier"
    )
    correlation_id = Column(
        String(100),
        nullable=True,
        comment="Correlation ID for tracking across systems"
    )
    
    # Job configuration
    model_name = Column(
        String(100),
        nullable=False,
        comment="Name of the ML model used"
    )
    model_version = Column(
        String(20),
        nullable=False,
        comment="Version of the ML model"
    )
    model_config = Column(
        JSONB,
        nullable=True,
        comment="Model configuration and parameters"
    )
    
    # Input data references
    input_data_refs = Column(
        JSONB,
        nullable=False,
        comment="References to input data (images, files, etc.)"
    )
    batch_size = Column(
        Integer,
        nullable=True,
        comment="Number of items processed in batch"
    )
    
    # Job status and timing
    status = Column(
        InferenceStatusEnum,
        nullable=False,
        default=InferenceStatusEnum.PENDING,
        comment="Current job status"
    )
    submitted_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="When job was submitted"
    )
    started_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When job processing started"
    )
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When job was completed"
    )
    
    # Processing information
    worker_id = Column(
        String(50),
        nullable=True,
        comment="ID of the worker that processed the job"
    )
    gpu_device = Column(
        String(20),
        nullable=True,
        comment="GPU device used for inference"
    )
    triton_model_instance = Column(
        String(50),
        nullable=True,
        comment="Triton model instance identifier"
    )
    
    # Performance metrics
    processing_time_ms = Column(
        Integer,
        nullable=True,
        comment="Total processing time in milliseconds"
    )
    inference_time_ms = Column(
        Integer,
        nullable=True,
        comment="Pure inference time in milliseconds"
    )
    preprocessing_time_ms = Column(
        Integer,
        nullable=True,
        comment="Preprocessing time in milliseconds"
    )
    postprocessing_time_ms = Column(
        Integer,
        nullable=True,
        comment="Postprocessing time in milliseconds"
    )
    
    # Resource utilization
    memory_usage_mb = Column(
        Integer,
        nullable=True,
        comment="Peak memory usage in MB"
    )
    gpu_utilization = Column(
        Numeric(5, 2),
        nullable=True,
        comment="GPU utilization percentage"
    )
    cpu_utilization = Column(
        Numeric(5, 2),
        nullable=True,
        comment="CPU utilization percentage"
    )
    
    # Results and predictions
    predictions = Column(
        JSONB,
        nullable=True,
        comment="Model predictions and results"
    )
    confidence_scores = Column(
        JSONB,
        nullable=True,
        comment="Confidence scores for predictions"
    )
    model_outputs = Column(
        JSONB,
        nullable=True,
        comment="Raw model outputs"
    )
    
    # Quality metrics
    overall_confidence = Column(
        Numeric(5, 4),
        nullable=True,
        comment="Overall confidence score for the job"
    )
    prediction_count = Column(
        Integer,
        nullable=True,
        comment="Number of predictions made"
    )
    high_confidence_count = Column(
        Integer,
        nullable=True,
        comment="Number of high-confidence predictions"
    )
    
    # Error handling
    error_message = Column(
        Text,
        nullable=True,
        comment="Error message if job failed"
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
    max_retries = Column(
        Integer,
        nullable=False,
        default=3,
        comment="Maximum number of retries allowed"
    )
    
    # Integration references
    inspection_id = Column(
        UUID(as_uuid=True),
        ForeignKey("inspections.id", ondelete="SET NULL"),
        nullable=True,
        comment="Associated inspection ID"
    )
    artifact_refs = Column(
        JSONB,
        nullable=True,
        comment="References to generated artifacts"
    )
    
    # Priority and scheduling
    priority = Column(
        Integer,
        nullable=False,
        default=5,
        comment="Job priority (1=highest, 10=lowest)"
    )
    queue_name = Column(
        String(50),
        nullable=True,
        comment="Processing queue name"
    )
    
    # Metadata and context
    job_metadata = Column(
        JSONB,
        nullable=True,
        comment="Additional job metadata"
    )
    user_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User who submitted the job"
    )
    session_id = Column(
        String(100),
        nullable=True,
        comment="Session identifier"
    )
    
    # External references
    external_job_id = Column(
        String(100),
        nullable=True,
        comment="External system job identifier"
    )
    webhook_url = Column(
        String(500),
        nullable=True,
        comment="Webhook URL for job completion notification"
    )
    
    # Relationships
    inspection = relationship(
        "Inspection",
        foreign_keys=[inspection_id],
        post_update=True
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_inference_jobs_id", "job_id"),
        Index("idx_inference_jobs_status", "status"),
        Index("idx_inference_jobs_model", "model_name", "model_version"),
        Index("idx_inference_jobs_submitted", "submitted_at"),
        Index("idx_inference_jobs_inspection", "inspection_id"),
        Index("idx_inference_jobs_user", "user_id"),
        Index("idx_inference_jobs_priority", "priority"),
        Index("idx_inference_jobs_queue", "queue_name"),
        Index("idx_inference_jobs_correlation", "correlation_id"),
        Index("idx_inference_jobs_predictions", "predictions", postgresql_using="gin"),
    )
    
    @validates('job_id')
    def validate_job_id(self, key, value):
        """Validate job ID format."""
        if not value or len(value.strip()) < 5:
            raise ValueError("Job ID must be at least 5 characters")
        return value.strip()
    
    @validates('priority')
    def validate_priority(self, key, value):
        """Validate priority is in valid range."""
        if value is not None and not (1 <= value <= 10):
            raise ValueError("Priority must be between 1 and 10")
        return value
    
    @validates('overall_confidence')
    def validate_overall_confidence(self, key, value):
        """Validate confidence score is between 0 and 1."""
        if value is not None and not (0 <= value <= 1):
            raise ValueError("Overall confidence must be between 0 and 1")
        return value
    
    @validates('gpu_utilization')
    def validate_gpu_utilization(self, key, value):
        """Validate GPU utilization is between 0 and 100."""
        if value is not None and not (0 <= value <= 100):
            raise ValueError("GPU utilization must be between 0 and 100")
        return value
    
    @validates('cpu_utilization')
    def validate_cpu_utilization(self, key, value):
        """Validate CPU utilization is between 0 and 100."""
        if value is not None and not (0 <= value <= 100):
            raise ValueError("CPU utilization must be between 0 and 100")
        return value
    
    def __repr__(self):
        return f"<InferenceJob(id='{self.job_id}', model='{self.model_name}', status='{self.status}')>"
    
    @property
    def is_completed(self) -> bool:
        """Check if job is completed successfully."""
        return self.status == InferenceStatusEnum.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Check if job has failed."""
        return self.status == InferenceStatusEnum.FAILED
    
    @property
    def is_processing(self) -> bool:
        """Check if job is currently processing."""
        return self.status == InferenceStatusEnum.RUNNING
    
    @property
    def can_retry(self) -> bool:
        """Check if job can be retried."""
        return (
            self.status == InferenceStatusEnum.FAILED and
            self.retry_count < self.max_retries
        )
    
    @property
    def total_duration_ms(self) -> Optional[int]:
        """Calculate total job duration in milliseconds."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() * 1000)
        return None
    
    @property
    def queue_duration_ms(self) -> Optional[int]:
        """Calculate queue waiting time in milliseconds."""
        if self.submitted_at and self.started_at:
            delta = self.started_at - self.submitted_at
            return int(delta.total_seconds() * 1000)
        return None
    
    def calculate_throughput(self) -> Optional[float]:
        """Calculate processing throughput (items per second)."""
        if self.batch_size and self.processing_time_ms:
            return (self.batch_size * 1000) / self.processing_time_ms
        return None
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        return {
            "total_duration_ms": self.total_duration_ms,
            "queue_duration_ms": self.queue_duration_ms,
            "processing_time_ms": self.processing_time_ms,
            "inference_time_ms": self.inference_time_ms,
            "preprocessing_time_ms": self.preprocessing_time_ms,
            "postprocessing_time_ms": self.postprocessing_time_ms,
            "throughput": self.calculate_throughput(),
            "memory_usage_mb": self.memory_usage_mb,
            "gpu_utilization": float(self.gpu_utilization) if self.gpu_utilization else None,
            "cpu_utilization": float(self.cpu_utilization) if self.cpu_utilization else None,
            "overall_confidence": float(self.overall_confidence) if self.overall_confidence else None,
            "prediction_count": self.prediction_count,
            "high_confidence_count": self.high_confidence_count,
        }
    
    def update_status(self, new_status: InferenceStatusEnum, error_message: str = None):
        """Update job status with timestamp tracking."""
        old_status = self.status
        self.status = new_status
        
        now = datetime.utcnow()
        
        if new_status == InferenceStatusEnum.RUNNING and old_status != InferenceStatusEnum.RUNNING:
            self.started_at = now
        elif new_status in [InferenceStatusEnum.COMPLETED, InferenceStatusEnum.FAILED]:
            self.completed_at = now
            
        if new_status == InferenceStatusEnum.FAILED:
            self.error_message = error_message
            self.retry_count += 1