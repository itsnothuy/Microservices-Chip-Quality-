"""Inspection models for quality control and defect management."""

from decimal import Decimal
from typing import Dict, Any, Optional, List
from datetime import datetime

from sqlalchemy import (
    Column, String, Text, Integer, Numeric, DateTime,
    ForeignKey, Index, Boolean, Float
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship, validates

from database.base import BaseModel, TimestampMixin
from database.enums import (
    InspectionTypeEnum, InspectionStatusEnum, DefectTypeEnum,
    DefectSeverityEnum, DetectionMethodEnum, ReviewStatusEnum
)


class Inspection(BaseModel, TimestampMixin):
    """Quality inspection instances with comprehensive tracking."""
    
    __tablename__ = "inspections"
    
    # Core identification
    inspection_id = Column(
        String(50),
        nullable=False,
        unique=True,
        comment="Unique inspection identifier"
    )
    lot_id = Column(
        UUID(as_uuid=True),
        ForeignKey("lots.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Reference to the lot being inspected"
    )
    
    # Inspection details
    inspection_type = Column(
        InspectionTypeEnum,
        nullable=False,
        comment="Type of inspection performed"
    )
    status = Column(
        InspectionStatusEnum,
        nullable=False,
        default=InspectionStatusEnum.PENDING,
        comment="Current inspection status"
    )
    
    # Timing information
    scheduled_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When inspection was scheduled"
    )
    started_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When inspection actually started"
    )
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When inspection was completed"
    )
    
    # Personnel and equipment
    inspector_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Inspector assigned to this inspection"
    )
    equipment_id = Column(
        String(50),
        nullable=True,
        comment="Inspection equipment identifier"
    )
    station_id = Column(
        String(50),
        nullable=True,
        comment="Inspection station identifier"
    )
    
    # Inspection parameters and results
    inspection_parameters = Column(
        JSONB,
        nullable=True,
        comment="Parameters and settings for the inspection"
    )
    raw_results = Column(
        JSONB,
        nullable=True,
        comment="Raw inspection data and measurements"
    )
    processed_results = Column(
        JSONB,
        nullable=True,
        comment="Processed and analyzed inspection results"
    )
    
    # Quality assessment
    overall_quality_score = Column(
        Numeric(5, 4),
        nullable=True,
        comment="Overall quality score (0.0000 to 1.0000)"
    )
    pass_fail_status = Column(
        Boolean,
        nullable=True,
        comment="Overall pass/fail determination"
    )
    confidence_score = Column(
        Numeric(5, 4),
        nullable=True,
        comment="Confidence in the inspection results"
    )
    
    # Review and validation
    review_status = Column(
        ReviewStatusEnum,
        nullable=False,
        default=ReviewStatusEnum.PENDING,
        comment="Human review status"
    )
    reviewed_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User who performed the review"
    )
    reviewed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When review was completed"
    )
    review_notes = Column(
        Text,
        nullable=True,
        comment="Notes from human review"
    )
    
    # Environmental and context data
    environmental_conditions = Column(
        JSONB,
        nullable=True,
        comment="Environmental conditions during inspection"
    )
    
    # Metadata and tracking
    correlation_id = Column(
        String(100),
        nullable=True,
        comment="Correlation ID for tracking across systems"
    )
    external_ref_id = Column(
        String(100),
        nullable=True,
        comment="External system reference ID"
    )
    
    # Notes and observations
    notes = Column(
        Text,
        nullable=True,
        comment="Additional notes and observations"
    )
    
    # Relationships
    lot = relationship("Lot", back_populates="inspections")
    defects = relationship(
        "Defect",
        back_populates="inspection",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_inspections_id", "inspection_id"),
        Index("idx_inspections_lot_id", "lot_id"),
        Index("idx_inspections_type", "inspection_type"),
        Index("idx_inspections_status", "status"),
        Index("idx_inspections_scheduled", "scheduled_at"),
        Index("idx_inspections_inspector", "inspector_id"),
        Index("idx_inspections_equipment", "equipment_id"),
        Index("idx_inspections_review_status", "review_status"),
        Index("idx_inspections_pass_fail", "pass_fail_status"),
        Index("idx_inspections_params", "inspection_parameters", postgresql_using="gin"),
    )
    
    @validates('inspection_id')
    def validate_inspection_id(self, key, value):
        """Validate inspection ID format."""
        if not value or len(value.strip()) < 5:
            raise ValueError("Inspection ID must be at least 5 characters")
        return value.strip().upper()
    
    @validates('overall_quality_score')
    def validate_quality_score(self, key, value):
        """Validate quality score is between 0 and 1."""
        if value is not None and not (0 <= value <= 1):
            raise ValueError("Quality score must be between 0 and 1")
        return value
    
    @validates('confidence_score')
    def validate_confidence_score(self, key, value):
        """Validate confidence score is between 0 and 1."""
        if value is not None and not (0 <= value <= 1):
            raise ValueError("Confidence score must be between 0 and 1")
        return value
    
    def __repr__(self):
        return f"<Inspection(id='{self.inspection_id}', type='{self.inspection_type}', status='{self.status}')>"
    
    @property
    def duration_minutes(self) -> Optional[float]:
        """Calculate inspection duration in minutes."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds() / 60
        return None
    
    @property
    def is_completed(self) -> bool:
        """Check if inspection is completed."""
        return self.status == InspectionStatusEnum.COMPLETED
    
    @property
    def requires_review(self) -> bool:
        """Check if inspection requires human review."""
        return self.review_status == ReviewStatusEnum.PENDING
    
    def can_be_reviewed(self) -> bool:
        """Check if inspection can be reviewed."""
        return (
            self.status == InspectionStatusEnum.COMPLETED and
            self.review_status in [ReviewStatusEnum.PENDING, ReviewStatusEnum.IN_REVIEW]
        )


class Defect(BaseModel, TimestampMixin):
    """Defect detection and classification records."""
    
    __tablename__ = "defects"
    
    # Core identification
    defect_id = Column(
        String(50),
        nullable=False,
        unique=True,
        comment="Unique defect identifier"
    )
    inspection_id = Column(
        UUID(as_uuid=True),
        ForeignKey("inspections.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to the inspection that found this defect"
    )
    
    # Defect classification
    defect_type = Column(
        DefectTypeEnum,
        nullable=False,
        comment="Type/category of defect"
    )
    severity = Column(
        DefectSeverityEnum,
        nullable=False,
        comment="Severity level of the defect"
    )
    detection_method = Column(
        DetectionMethodEnum,
        nullable=False,
        comment="How the defect was detected"
    )
    
    # Location and geometry
    location_data = Column(
        JSONB,
        nullable=True,
        comment="Spatial location data (coordinates, bounding box, etc.)"
    )
    affected_area = Column(
        Numeric(10, 6),
        nullable=True,
        comment="Area affected by the defect (in square units)"
    )
    
    # Measurement and characteristics
    dimensions = Column(
        JSONB,
        nullable=True,
        comment="Defect dimensions (length, width, depth, etc.)"
    )
    characteristics = Column(
        JSONB,
        nullable=True,
        comment="Additional defect characteristics and properties"
    )
    
    # Detection confidence and validation
    confidence_score = Column(
        Numeric(5, 4),
        nullable=True,
        comment="ML model confidence in defect detection"
    )
    is_confirmed = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether defect has been confirmed by human inspector"
    )
    is_false_positive = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether defect was determined to be false positive"
    )
    
    # Review and validation
    reviewed_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Inspector who reviewed the defect"
    )
    reviewed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When defect review was completed"
    )
    review_notes = Column(
        Text,
        nullable=True,
        comment="Notes from defect review"
    )
    
    # Impact and disposition
    impact_assessment = Column(
        JSONB,
        nullable=True,
        comment="Assessment of defect impact on functionality"
    )
    disposition = Column(
        String(50),
        nullable=True,
        comment="Disposition decision (accept, reject, rework, etc.)"
    )
    
    # Root cause and analysis
    root_cause = Column(
        String(200),
        nullable=True,
        comment="Identified root cause of the defect"
    )
    corrective_action = Column(
        Text,
        nullable=True,
        comment="Corrective actions taken or recommended"
    )
    
    # Image and artifact references
    image_refs = Column(
        JSONB,
        nullable=True,
        comment="References to defect images and artifacts"
    )
    
    # External references
    external_ref_id = Column(
        String(100),
        nullable=True,
        comment="External system reference ID"
    )
    
    # Relationships
    inspection = relationship("Inspection", back_populates="defects")
    
    # Indexes
    __table_args__ = (
        Index("idx_defects_id", "defect_id"),
        Index("idx_defects_inspection_id", "inspection_id"),
        Index("idx_defects_type", "defect_type"),
        Index("idx_defects_severity", "severity"),
        Index("idx_defects_detection_method", "detection_method"),
        Index("idx_defects_confirmed", "is_confirmed"),
        Index("idx_defects_false_positive", "is_false_positive"),
        Index("idx_defects_reviewed", "reviewed_by"),
        Index("idx_defects_location", "location_data", postgresql_using="gin"),
        Index("idx_defects_characteristics", "characteristics", postgresql_using="gin"),
    )
    
    @validates('defect_id')
    def validate_defect_id(self, key, value):
        """Validate defect ID format."""
        if not value or len(value.strip()) < 5:
            raise ValueError("Defect ID must be at least 5 characters")
        return value.strip().upper()
    
    @validates('confidence_score')
    def validate_confidence_score(self, key, value):
        """Validate confidence score is between 0 and 1."""
        if value is not None and not (0 <= value <= 1):
            raise ValueError("Confidence score must be between 0 and 1")
        return value
    
    @validates('affected_area')
    def validate_affected_area(self, key, value):
        """Validate affected area is positive."""
        if value is not None and value <= 0:
            raise ValueError("Affected area must be positive")
        return value
    
    def __repr__(self):
        return f"<Defect(id='{self.defect_id}', type='{self.defect_type}', severity='{self.severity}')>"
    
    @property
    def is_critical(self) -> bool:
        """Check if defect is critical severity."""
        return self.severity == DefectSeverityEnum.CRITICAL
    
    @property
    def is_reviewed(self) -> bool:
        """Check if defect has been reviewed."""
        return self.reviewed_by is not None and self.reviewed_at is not None
    
    @property
    def is_ml_detected(self) -> bool:
        """Check if defect was detected by ML."""
        return self.detection_method in [DetectionMethodEnum.ML, DetectionMethodEnum.HYBRID]
    
    def calculate_severity_score(self) -> float:
        """Calculate numeric severity score for analytics."""
        severity_scores = {
            DefectSeverityEnum.LOW: 1.0,
            DefectSeverityEnum.MEDIUM: 2.0,
            DefectSeverityEnum.HIGH: 3.0,
            DefectSeverityEnum.CRITICAL: 4.0,
        }
        return severity_scores.get(self.severity, 0.0)