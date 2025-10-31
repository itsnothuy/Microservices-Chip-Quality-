"""
Model management schemas.

Pydantic models for ML model lifecycle management.
"""

from datetime import datetime
from typing import Any, Optional
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class ModelStatus(str, Enum):
    """Model deployment status."""
    LOADING = "loading"
    READY = "ready"
    UNLOADING = "unloading"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class ModelPlatform(str, Enum):
    """Supported model platforms."""
    ONNX = "onnxruntime_onnx"
    PYTORCH = "pytorch_libtorch"
    TENSORFLOW = "tensorflow_savedmodel"
    TENSORRT = "tensorrt_plan"
    PYTHON = "python"


class ModelInfo(BaseModel):
    """Model information and metadata."""
    
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., description="Model name")
    version: str = Field(..., description="Model version")
    platform: ModelPlatform = Field(..., description="Model platform")
    description: str = Field(..., description="Model description")
    status: ModelStatus = Field(..., description="Current model status")
    input_shapes: dict[str, list[int]] = Field(
        ...,
        description="Input tensor shapes"
    )
    output_shapes: dict[str, list[int]] = Field(
        ...,
        description="Output tensor shapes"
    )
    max_batch_size: int = Field(..., description="Maximum batch size")
    instance_count: int = Field(..., description="Number of model instances")
    performance_metrics: dict[str, float] = Field(
        default_factory=dict,
        description="Performance metrics"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    created_at: datetime = Field(..., description="Model creation time")
    updated_at: datetime = Field(..., description="Last update time")


class ModelListResponse(BaseModel):
    """Response model for listing models."""
    
    model_config = ConfigDict(from_attributes=True)
    
    models: list[ModelInfo] = Field(..., description="List of available models")
    total: int = Field(..., description="Total number of models")


class ModelVersionInfo(BaseModel):
    """Information about specific model version."""
    
    model_config = ConfigDict(from_attributes=True)
    
    version: str = Field(..., description="Version identifier")
    status: ModelStatus = Field(..., description="Version status")
    is_default: bool = Field(..., description="Whether this is the default version")
    deployment_date: datetime = Field(..., description="When version was deployed")
    performance_score: float = Field(..., description="Performance score")
    accuracy_metrics: dict[str, float] = Field(
        default_factory=dict,
        description="Accuracy metrics"
    )


class ModelVersionListResponse(BaseModel):
    """Response model for listing model versions."""
    
    model_config = ConfigDict(from_attributes=True)
    
    model_name: str = Field(..., description="Model name")
    versions: list[ModelVersionInfo] = Field(..., description="Available versions")
    total: int = Field(..., description="Total number of versions")


class ModelDeployRequest(BaseModel):
    """Request model for deploying a model."""
    
    model_config = ConfigDict(from_attributes=True)
    
    model_name: str = Field(
        ...,
        description="Model name",
        min_length=1,
        max_length=100
    )
    version: str = Field(
        ...,
        description="Version to deploy",
        min_length=1,
        max_length=20
    )
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Deployment configuration"
    )
    set_as_default: bool = Field(
        default=False,
        description="Set as default version"
    )


class ModelDeployResponse(BaseModel):
    """Response model for model deployment."""
    
    model_config = ConfigDict(from_attributes=True)
    
    model_name: str = Field(..., description="Model name")
    version: str = Field(..., description="Deployed version")
    status: ModelStatus = Field(..., description="Deployment status")
    message: str = Field(..., description="Deployment message")
    deployed_at: datetime = Field(..., description="Deployment timestamp")


class ModelConfigUpdate(BaseModel):
    """Request model for updating model configuration."""
    
    model_config = ConfigDict(from_attributes=True)
    
    max_batch_size: Optional[int] = Field(
        None,
        description="Maximum batch size",
        ge=1
    )
    preferred_batch_sizes: Optional[list[int]] = Field(
        None,
        description="Preferred batch sizes for dynamic batching"
    )
    instance_count: Optional[int] = Field(
        None,
        description="Number of model instances",
        ge=1
    )
    optimization_config: Optional[dict[str, Any]] = Field(
        None,
        description="Optimization parameters"
    )


class ModelPerformanceMetrics(BaseModel):
    """Model performance metrics."""
    
    model_config = ConfigDict(from_attributes=True)
    
    model_name: str = Field(..., description="Model name")
    version: str = Field(..., description="Model version")
    total_requests: int = Field(..., description="Total inference requests")
    successful_requests: int = Field(..., description="Successful requests")
    failed_requests: int = Field(..., description="Failed requests")
    avg_latency_ms: float = Field(..., description="Average latency in ms")
    p50_latency_ms: float = Field(..., description="P50 latency")
    p95_latency_ms: float = Field(..., description="P95 latency")
    p99_latency_ms: float = Field(..., description="P99 latency")
    throughput_per_second: float = Field(..., description="Throughput per second")
    gpu_utilization_percent: Optional[float] = Field(
        None,
        description="GPU utilization percentage"
    )
    memory_usage_mb: Optional[float] = Field(
        None,
        description="Memory usage in MB"
    )
    period_start: datetime = Field(..., description="Metrics period start")
    period_end: datetime = Field(..., description="Metrics period end")


class ModelValidationRequest(BaseModel):
    """Request model for model validation."""
    
    model_config = ConfigDict(from_attributes=True)
    
    test_dataset_path: str = Field(
        ...,
        description="Path to test dataset",
        min_length=1
    )
    validation_config: dict[str, Any] = Field(
        default_factory=dict,
        description="Validation configuration"
    )


class ModelValidationResponse(BaseModel):
    """Response model for model validation."""
    
    model_config = ConfigDict(from_attributes=True)
    
    model_name: str = Field(..., description="Model name")
    version: str = Field(..., description="Model version")
    accuracy: float = Field(..., description="Overall accuracy")
    precision: float = Field(..., description="Precision score")
    recall: float = Field(..., description="Recall score")
    f1_score: float = Field(..., description="F1 score")
    confusion_matrix: list[list[int]] = Field(
        ...,
        description="Confusion matrix"
    )
    validation_results: dict[str, Any] = Field(
        default_factory=dict,
        description="Detailed validation results"
    )
    validated_at: datetime = Field(..., description="Validation timestamp")
