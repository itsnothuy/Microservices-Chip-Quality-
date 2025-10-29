"""Pydantic schemas for inspection entities"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import Field, field_validator

from .common import BaseSchema, TimestampSchema
from ..database.enums import (
    InspectionTypeEnum,
    InspectionStatusEnum,
    DefectTypeEnum,
    DefectSeverityEnum,
    DetectionMethodEnum,
    ReviewStatusEnum,
)


# ============================================================================
# INSPECTION SCHEMAS
# ============================================================================

class InspectionBase(BaseSchema):
    """Base inspection schema with common fields"""
    
    lot_id: UUID = Field(..., description="Reference to manufacturing lot")
    chip_id: str = Field(..., min_length=1, max_length=100, description="Individual chip identifier")
    inspection_type: InspectionTypeEnum = Field(..., description="Type of inspection")
    priority: int = Field(default=5, ge=1, le=10, description="Priority (1-10, higher is more urgent)")
    station_id: str = Field(..., min_length=1, max_length=50, description="Inspection station identifier")
    operator_id: Optional[UUID] = Field(None, description="Operator performing inspection")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class InspectionCreate(InspectionBase):
    """Schema for creating a new inspection"""
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v: int) -> int:
        if not 1 <= v <= 10:
            raise ValueError("priority must be between 1 and 10")
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "lot_id": "223e4567-e89b-12d3-a456-426614174000",
                "chip_id": "CHIP-001",
                "inspection_type": "visual",
                "priority": 5,
                "station_id": "STATION-A1",
                "operator_id": "323e4567-e89b-12d3-a456-426614174000",
                "metadata": {
                    "camera_id": "CAM-001",
                    "lighting_config": "standard"
                }
            }
        }
    }


class InspectionUpdate(BaseSchema):
    """Schema for updating an inspection"""
    
    status: Optional[InspectionStatusEnum] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    operator_id: Optional[UUID] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = None


class InspectionResponse(InspectionBase, TimestampSchema):
    """Schema for inspection API responses"""
    
    id: UUID = Field(..., description="Unique identifier")
    status: InspectionStatusEnum = Field(..., description="Current inspection status")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "423e4567-e89b-12d3-a456-426614174000",
                "lot_id": "223e4567-e89b-12d3-a456-426614174000",
                "chip_id": "CHIP-001",
                "inspection_type": "visual",
                "status": "completed",
                "priority": 5,
                "station_id": "STATION-A1",
                "operator_id": "323e4567-e89b-12d3-a456-426614174000",
                "started_at": "2025-10-29T10:00:00Z",
                "completed_at": "2025-10-29T10:05:00Z",
                "metadata": {},
                "created_at": "2025-10-29T10:00:00Z",
                "updated_at": "2025-10-29T10:05:00Z"
            }
        }
    }


# ============================================================================
# DEFECT SCHEMAS
# ============================================================================

class DefectBase(BaseSchema):
    """Base defect schema with common fields"""
    
    inspection_id: UUID = Field(..., description="Reference to inspection")
    defect_type: DefectTypeEnum = Field(..., description="Type of defect")
    severity: DefectSeverityEnum = Field(..., description="Defect severity")
    confidence: Decimal = Field(..., ge=0, le=1, description="Detection confidence (0-1)")
    location: dict[str, Any] = Field(..., description="Defect location (bounding box)")
    description: Optional[str] = Field(None, description="Detailed description")
    detection_method: DetectionMethodEnum = Field(..., description="Detection method")
    corrective_action: Optional[str] = Field(None, description="Corrective action taken")
    artifact_references: list[str] = Field(default_factory=list, description="Related artifact IDs")


class DefectCreate(DefectBase):
    """Schema for creating a new defect"""
    
    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v: Decimal) -> Decimal:
        if not 0 <= v <= 1:
            raise ValueError("confidence must be between 0 and 1")
        return v
    
    @field_validator('location')
    @classmethod
    def validate_location(cls, v: dict[str, Any]) -> dict[str, Any]:
        required_fields = ['x', 'y', 'width', 'height']
        for field in required_fields:
            if field not in v:
                raise ValueError(f"location must contain '{field}' field")
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "inspection_id": "423e4567-e89b-12d3-a456-426614174000",
                "defect_type": "scratch",
                "severity": "medium",
                "confidence": 0.95,
                "location": {
                    "x": 100,
                    "y": 200,
                    "width": 50,
                    "height": 30
                },
                "description": "Surface scratch detected on component",
                "detection_method": "ml_automated",
                "corrective_action": None,
                "artifact_references": []
            }
        }
    }


class DefectResponse(DefectBase, TimestampSchema):
    """Schema for defect API responses"""
    
    id: UUID = Field(..., description="Unique identifier")
    reviewer_id: Optional[UUID] = Field(None, description="Reviewer user ID")
    review_status: ReviewStatusEnum = Field(..., description="Review status")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "523e4567-e89b-12d3-a456-426614174000",
                "inspection_id": "423e4567-e89b-12d3-a456-426614174000",
                "defect_type": "scratch",
                "severity": "medium",
                "confidence": 0.95,
                "location": {
                    "x": 100,
                    "y": 200,
                    "width": 50,
                    "height": 30
                },
                "description": "Surface scratch detected",
                "detection_method": "ml_automated",
                "reviewer_id": None,
                "review_status": "pending",
                "corrective_action": None,
                "artifact_references": [],
                "created_at": "2025-10-29T10:05:00Z",
                "updated_at": "2025-10-29T10:05:00Z"
            }
        }
    }
