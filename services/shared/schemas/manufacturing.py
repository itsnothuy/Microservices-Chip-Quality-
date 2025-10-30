"""Pydantic schemas for manufacturing entities (Parts, Lots)"""

from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import Field, field_validator

from .common import BaseSchema, TimestampSchema
from ..database.enums import PartTypeEnum, LotStatusEnum


# ============================================================================
# PART SCHEMAS
# ============================================================================

class PartBase(BaseSchema):
    """Base part schema with common fields"""
    
    part_number: str = Field(..., min_length=1, max_length=100, description="Unique part number")
    part_name: str = Field(..., min_length=1, max_length=200, description="Part name")
    part_type: PartTypeEnum = Field(..., description="Type of part")
    specifications: dict[str, Any] = Field(default_factory=dict, description="Technical specifications")
    tolerance_requirements: dict[str, Any] = Field(default_factory=dict, description="Manufacturing tolerances")


class PartCreate(PartBase):
    """Schema for creating a new part"""
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "part_number": "PCB-2025-001",
                "part_name": "High-Density Interconnect PCB",
                "part_type": "pcb",
                "specifications": {
                    "layers": 8,
                    "thickness": "1.6mm",
                    "copper_weight": "1oz",
                    "surface_finish": "ENIG"
                },
                "tolerance_requirements": {
                    "dimensional": "±0.1mm",
                    "positional": "±0.05mm"
                }
            }
        }
    }


class PartUpdate(BaseSchema):
    """Schema for updating a part (all fields optional)"""
    
    part_name: Optional[str] = Field(None, min_length=1, max_length=200)
    specifications: Optional[dict[str, Any]] = None
    tolerance_requirements: Optional[dict[str, Any]] = None


class PartResponse(PartBase, TimestampSchema):
    """Schema for part API responses"""
    
    id: UUID = Field(..., description="Unique identifier")
    version: int = Field(..., description="Part definition version")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "part_number": "PCB-2025-001",
                "part_name": "High-Density Interconnect PCB",
                "part_type": "pcb",
                "specifications": {
                    "layers": 8,
                    "thickness": "1.6mm"
                },
                "tolerance_requirements": {
                    "dimensional": "±0.1mm"
                },
                "version": 1,
                "created_at": "2025-10-29T10:00:00Z",
                "updated_at": "2025-10-29T10:00:00Z"
            }
        }
    }


# ============================================================================
# LOT SCHEMAS
# ============================================================================

class LotBase(BaseSchema):
    """Base lot schema with common fields"""
    
    lot_number: str = Field(..., min_length=1, max_length=100, description="Unique lot number")
    part_id: UUID = Field(..., description="Reference to part being manufactured")
    production_date: date = Field(..., description="Date of production")
    batch_size: int = Field(..., gt=0, description="Number of units in batch")
    production_line: str = Field(..., min_length=1, max_length=50, description="Production line identifier")
    supplier_id: Optional[UUID] = Field(None, description="Supplier identifier (if applicable)")
    quality_requirements: dict[str, Any] = Field(default_factory=dict, description="Quality standards")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class LotCreate(LotBase):
    """Schema for creating a new lot"""
    
    @field_validator('batch_size')
    @classmethod
    def validate_batch_size(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("batch_size must be positive")
        if v > 1000000:
            raise ValueError("batch_size cannot exceed 1,000,000")
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "lot_number": "LOT-2025-001",
                "part_id": "123e4567-e89b-12d3-a456-426614174000",
                "production_date": "2025-10-29",
                "batch_size": 1000,
                "production_line": "LINE-A",
                "supplier_id": None,
                "quality_requirements": {
                    "defect_rate_threshold": 0.01,
                    "inspection_coverage": 1.0
                },
                "metadata": {
                    "shift": "morning",
                    "operator": "OP-001"
                }
            }
        }
    }


class LotUpdate(BaseSchema):
    """Schema for updating a lot (all fields optional)"""
    
    status: Optional[LotStatusEnum] = None
    quality_requirements: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None


class LotResponse(LotBase, TimestampSchema):
    """Schema for lot API responses"""
    
    id: UUID = Field(..., description="Unique identifier")
    status: LotStatusEnum = Field(..., description="Current lot status")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "223e4567-e89b-12d3-a456-426614174000",
                "lot_number": "LOT-2025-001",
                "part_id": "123e4567-e89b-12d3-a456-426614174000",
                "production_date": "2025-10-29",
                "batch_size": 1000,
                "production_line": "LINE-A",
                "supplier_id": None,
                "quality_requirements": {
                    "defect_rate_threshold": 0.01
                },
                "metadata": {},
                "status": "active",
                "created_at": "2025-10-29T10:00:00Z",
                "updated_at": "2025-10-29T10:00:00Z"
            }
        }
    }
