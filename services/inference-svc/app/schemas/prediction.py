"""
Prediction result schemas.

Pydantic models for ML prediction outputs.
"""

from typing import Any, Optional
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class DefectType(str, Enum):
    """Types of defects that can be detected."""
    SCRATCH = "scratch"
    VOID = "void"
    CONTAMINATION = "contamination"
    CRACK = "crack"
    DISCOLORATION = "discoloration"
    DELAMINATION = "delamination"
    SHORT_CIRCUIT = "short_circuit"
    OPEN_CIRCUIT = "open_circuit"
    MISALIGNMENT = "misalignment"
    DIMENSION_ERROR = "dimension_error"
    SURFACE_DEFECT = "surface_defect"
    UNKNOWN = "unknown"


class DefectSeverity(str, Enum):
    """Severity levels for detected defects."""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    COSMETIC = "cosmetic"


class BoundingBox(BaseModel):
    """Bounding box coordinates for defect location."""
    
    model_config = ConfigDict(from_attributes=True)
    
    x: float = Field(..., description="X coordinate (top-left)", ge=0)
    y: float = Field(..., description="Y coordinate (top-left)", ge=0)
    width: float = Field(..., description="Bounding box width", gt=0)
    height: float = Field(..., description="Bounding box height", gt=0)


class DefectCharacteristics(BaseModel):
    """Physical characteristics of detected defect."""
    
    model_config = ConfigDict(from_attributes=True)
    
    area: float = Field(..., description="Defect area in pixels", ge=0)
    perimeter: float = Field(..., description="Defect perimeter in pixels", ge=0)
    circularity: Optional[float] = Field(
        None,
        description="Circularity measure (0-1)",
        ge=0,
        le=1
    )
    aspect_ratio: Optional[float] = Field(
        None,
        description="Width to height ratio",
        gt=0
    )
    orientation: Optional[float] = Field(
        None,
        description="Orientation angle in degrees",
        ge=0,
        lt=360
    )


class DefectPrediction(BaseModel):
    """Individual defect prediction result."""
    
    model_config = ConfigDict(from_attributes=True)
    
    defect_id: str = Field(..., description="Unique defect identifier")
    defect_type: DefectType = Field(..., description="Type of defect detected")
    severity: DefectSeverity = Field(..., description="Severity level")
    confidence: float = Field(
        ...,
        description="Confidence score for detection",
        ge=0.0,
        le=1.0
    )
    bounding_box: BoundingBox = Field(..., description="Defect location")
    characteristics: DefectCharacteristics = Field(
        ...,
        description="Physical characteristics"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


class ClassificationResult(BaseModel):
    """Classification prediction result."""
    
    model_config = ConfigDict(from_attributes=True)
    
    class_name: str = Field(..., description="Predicted class name")
    confidence: float = Field(
        ...,
        description="Classification confidence",
        ge=0.0,
        le=1.0
    )
    probabilities: dict[str, float] = Field(
        default_factory=dict,
        description="Class probabilities"
    )


class QualityAssessment(BaseModel):
    """Overall quality assessment result."""
    
    model_config = ConfigDict(from_attributes=True)
    
    overall_quality: str = Field(..., description="Overall quality classification")
    quality_score: float = Field(
        ...,
        description="Quality score (0-100)",
        ge=0.0,
        le=100.0
    )
    pass_fail: bool = Field(..., description="Pass/fail determination")
    confidence: float = Field(
        ...,
        description="Assessment confidence",
        ge=0.0,
        le=1.0
    )
    defect_count: int = Field(..., description="Total number of defects detected", ge=0)
    critical_defects: int = Field(..., description="Number of critical defects", ge=0)
    major_defects: int = Field(..., description="Number of major defects", ge=0)
    minor_defects: int = Field(..., description="Number of minor defects", ge=0)


class PredictionResult(BaseModel):
    """Complete prediction result from inference."""
    
    model_config = ConfigDict(from_attributes=True)
    
    defects: list[DefectPrediction] = Field(
        default_factory=list,
        description="List of detected defects"
    )
    classification: Optional[ClassificationResult] = Field(
        None,
        description="Classification result if applicable"
    )
    quality_assessment: QualityAssessment = Field(
        ...,
        description="Overall quality assessment"
    )
    raw_outputs: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw model outputs"
    )
    inference_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Inference execution metadata"
    )


class PredictionSummary(BaseModel):
    """Summary statistics for prediction results."""
    
    model_config = ConfigDict(from_attributes=True)
    
    total_defects: int = Field(..., description="Total defects detected")
    defects_by_type: dict[str, int] = Field(
        ...,
        description="Defect counts by type"
    )
    defects_by_severity: dict[str, int] = Field(
        ...,
        description="Defect counts by severity"
    )
    avg_confidence: float = Field(
        ...,
        description="Average confidence score",
        ge=0.0,
        le=1.0
    )
    total_defect_area: float = Field(
        ...,
        description="Total area covered by defects",
        ge=0
    )
