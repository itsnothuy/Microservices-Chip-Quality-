"""
Inference request and response schemas.

Pydantic models for ML inference API endpoints.
"""

from datetime import datetime
from typing import Any, Optional
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class InferenceStatus(str, Enum):
    """Inference job status enumeration."""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class InferenceMode(str, Enum):
    """Inference processing mode."""
    REALTIME = "realtime"
    BATCH = "batch"
    ASYNC = "async"


class InferenceCreate(BaseModel):
    """Request model for creating inference job."""
    
    model_config = ConfigDict(from_attributes=True)
    
    inspection_id: str = Field(
        ...,
        description="Associated inspection ID",
        min_length=1,
        max_length=100
    )
    chip_id: str = Field(
        ...,
        description="Chip identifier",
        min_length=1,
        max_length=100
    )
    artifact_ids: list[str] = Field(
        ...,
        description="List of artifact IDs for inference",
        min_length=1
    )
    model_name: str = Field(
        ...,
        description="ML model to use for inference",
        min_length=1,
        max_length=100
    )
    model_version: Optional[str] = Field(
        None,
        description="Specific model version (latest if not specified)",
        max_length=20
    )
    inference_mode: InferenceMode = Field(
        default=InferenceMode.ASYNC,
        description="Processing mode"
    )
    inference_config: dict[str, Any] = Field(
        default_factory=dict,
        description="Model-specific configuration"
    )
    callback_url: Optional[str] = Field(
        None,
        description="Webhook URL for completion notification",
        max_length=500
    )
    priority: int = Field(
        default=5,
        description="Job priority (1-10, higher is more urgent)",
        ge=1,
        le=10
    )


class InferenceResponse(BaseModel):
    """Response model for inference job."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(..., description="Inference job ID")
    inspection_id: str = Field(..., description="Associated inspection ID")
    chip_id: str = Field(..., description="Chip identifier")
    artifact_ids: list[str] = Field(..., description="Artifact IDs processed")
    model_name: str = Field(..., description="Model name used")
    model_version: str = Field(..., description="Model version used")
    status: InferenceStatus = Field(..., description="Current job status")
    inference_mode: InferenceMode = Field(..., description="Processing mode")
    confidence_score: Optional[float] = Field(
        None,
        description="Overall confidence score",
        ge=0.0,
        le=1.0
    )
    predictions: dict[str, Any] = Field(
        default_factory=dict,
        description="Inference predictions"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Job metadata"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if failed"
    )
    created_at: datetime = Field(..., description="Job creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    submitted_at: Optional[datetime] = Field(None, description="Job submission time")
    started_at: Optional[datetime] = Field(None, description="Processing start time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")
    inference_time_ms: Optional[float] = Field(
        None,
        description="Inference execution time in milliseconds"
    )


class InferenceListResponse(BaseModel):
    """Response model for listing inference jobs."""
    
    model_config = ConfigDict(from_attributes=True)
    
    data: list[InferenceResponse] = Field(..., description="List of inference jobs")
    total: int = Field(..., description="Total number of jobs")
    has_more: bool = Field(..., description="Whether more results exist")
    next_cursor: Optional[str] = Field(None, description="Cursor for next page")


class BatchInferenceRequest(BaseModel):
    """Request model for batch inference."""
    
    model_config = ConfigDict(from_attributes=True)
    
    inspections: list[InferenceCreate] = Field(
        ...,
        description="List of inspection inference requests",
        min_length=1,
        max_length=100
    )
    batch_config: dict[str, Any] = Field(
        default_factory=dict,
        description="Batch-specific configuration"
    )


class BatchInferenceResponse(BaseModel):
    """Response model for batch inference."""
    
    model_config = ConfigDict(from_attributes=True)
    
    batch_id: str = Field(..., description="Batch job ID")
    total_jobs: int = Field(..., description="Total number of jobs in batch")
    successful: int = Field(..., description="Number of successful jobs")
    failed: int = Field(..., description="Number of failed jobs")
    pending: int = Field(..., description="Number of pending jobs")
    jobs: list[InferenceResponse] = Field(..., description="Individual job results")
    created_at: datetime = Field(..., description="Batch creation time")


class InferenceMetrics(BaseModel):
    """Inference performance metrics."""
    
    model_config = ConfigDict(from_attributes=True)
    
    total_inferences: int = Field(..., description="Total number of inferences")
    successful_inferences: int = Field(..., description="Successful inferences")
    failed_inferences: int = Field(..., description="Failed inferences")
    avg_inference_time_ms: float = Field(..., description="Average inference time")
    p50_inference_time_ms: float = Field(..., description="P50 inference latency")
    p95_inference_time_ms: float = Field(..., description="P95 inference latency")
    p99_inference_time_ms: float = Field(..., description="P99 inference latency")
    throughput_per_second: float = Field(..., description="Inferences per second")
    avg_confidence_score: float = Field(..., description="Average confidence score")
    period_start: datetime = Field(..., description="Metrics period start")
    period_end: datetime = Field(..., description="Metrics period end")
