"""Manufacturing models for parts and lots management."""

from decimal import Decimal
from typing import Dict, Any, Optional
from datetime import date, datetime

from sqlalchemy import (
    Column, String, Text, Integer, Numeric, Date, DateTime,
    ForeignKey, Index, UniqueConstraint, Boolean
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship, validates

from database.base import BaseModel, TimestampMixin
from database.enums import PartTypeEnum, LotStatusEnum


class Part(BaseModel, TimestampMixin):
    """Part definitions with specifications and tolerances."""
    
    __tablename__ = "parts"
    
    # Core identification
    part_number = Column(
        String(50), 
        nullable=False, 
        unique=True,
        comment="Unique part number identifier"
    )
    part_name = Column(
        String(200), 
        nullable=False,
        comment="Human-readable part name"
    )
    part_type = Column(
        PartTypeEnum,
        nullable=False,
        comment="Type of part (PCB, semiconductor, etc.)"
    )
    
    # Specifications and requirements
    specifications = Column(
        JSONB,
        nullable=True,
        comment="Technical specifications as JSON"
    )
    tolerance_requirements = Column(
        JSONB,
        nullable=True,
        comment="Tolerance requirements and limits"
    )
    
    # Version control
    version = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Part specification version"
    )
    
    # Optional fields
    description = Column(
        Text,
        nullable=True,
        comment="Detailed part description"
    )
    supplier_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Reference to supplier (future use)"
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether part is active in production"
    )
    
    # Relationships
    lots = relationship(
        "Lot",
        back_populates="part",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_parts_number", "part_number"),
        Index("idx_parts_type", "part_type"),
        Index("idx_parts_active", "is_active"),
        Index("idx_parts_specs", "specifications", postgresql_using="gin"),
    )
    
    @validates('part_number')
    def validate_part_number(self, key, value):
        """Validate part number format."""
        if not value or len(value.strip()) < 3:
            raise ValueError("Part number must be at least 3 characters")
        return value.strip().upper()
    
    @validates('specifications')
    def validate_specifications(self, key, value):
        """Validate specifications JSON structure."""
        if value is not None and not isinstance(value, dict):
            raise ValueError("Specifications must be a JSON object")
        return value
    
    def __repr__(self):
        return f"<Part(part_number='{self.part_number}', type='{self.part_type}')>"


class Lot(BaseModel, TimestampMixin):
    """Manufacturing batches with production metadata."""
    
    __tablename__ = "lots"
    
    # Core identification
    lot_number = Column(
        String(50),
        nullable=False,
        unique=True,
        comment="Unique lot identifier"
    )
    part_id = Column(
        UUID(as_uuid=True),
        ForeignKey("parts.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Reference to part being manufactured"
    )
    
    # Production information
    quantity = Column(
        Integer,
        nullable=False,
        comment="Number of units in the lot"
    )
    production_date = Column(
        Date,
        nullable=False,
        comment="Date of production"
    )
    expiry_date = Column(
        Date,
        nullable=True,
        comment="Expiry date for time-sensitive parts"
    )
    
    # Status and workflow
    status = Column(
        LotStatusEnum,
        nullable=False,
        default=LotStatusEnum.ACTIVE,
        comment="Current lot status"
    )
    
    # Manufacturing metadata
    production_line = Column(
        String(50),
        nullable=True,
        comment="Production line identifier"
    )
    shift = Column(
        String(20),
        nullable=True,
        comment="Production shift (day/night/weekend)"
    )
    operator_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Operator responsible for production"
    )
    
    # Quality and process data
    process_parameters = Column(
        JSONB,
        nullable=True,
        comment="Manufacturing process parameters"
    )
    environmental_conditions = Column(
        JSONB,
        nullable=True,
        comment="Environmental conditions during production"
    )
    
    # Tracking and compliance
    batch_record_id = Column(
        String(100),
        nullable=True,
        comment="External batch record identifier"
    )
    compliance_data = Column(
        JSONB,
        nullable=True,
        comment="Regulatory compliance information"
    )
    
    # Release information
    released_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when lot was released"
    )
    released_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User who released the lot"
    )
    
    # Notes and comments
    notes = Column(
        Text,
        nullable=True,
        comment="Additional notes and observations"
    )
    
    # Relationships
    part = relationship("Part", back_populates="lots")
    inspections = relationship(
        "Inspection",
        back_populates="lot",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_lots_number", "lot_number"),
        Index("idx_lots_part_id", "part_id"),
        Index("idx_lots_status", "status"),
        Index("idx_lots_production_date", "production_date"),
        Index("idx_lots_line", "production_line"),
        Index("idx_lots_process_params", "process_parameters", postgresql_using="gin"),
        UniqueConstraint("lot_number", name="uq_lots_number"),
    )
    
    @validates('lot_number')
    def validate_lot_number(self, key, value):
        """Validate lot number format."""
        if not value or len(value.strip()) < 3:
            raise ValueError("Lot number must be at least 3 characters")
        return value.strip().upper()
    
    @validates('quantity')
    def validate_quantity(self, key, value):
        """Validate quantity is positive."""
        if value is not None and value <= 0:
            raise ValueError("Quantity must be positive")
        return value
    
    @validates('production_date')
    def validate_production_date(self, key, value):
        """Validate production date is not in the future."""
        if value and value > date.today():
            raise ValueError("Production date cannot be in the future")
        return value
    
    def __repr__(self):
        return f"<Lot(lot_number='{self.lot_number}', status='{self.status}')>"
    
    @property
    def is_released(self) -> bool:
        """Check if lot has been released."""
        return self.status == LotStatusEnum.RELEASED and self.released_at is not None
    
    @property
    def is_quarantined(self) -> bool:
        """Check if lot is quarantined."""
        return self.status == LotStatusEnum.QUARANTINED
    
    def can_be_inspected(self) -> bool:
        """Check if lot is eligible for inspection."""
        return self.status in [LotStatusEnum.ACTIVE, LotStatusEnum.QUARANTINED]