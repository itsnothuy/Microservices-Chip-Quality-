"""Unit tests for Pydantic schemas"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from pydantic import ValidationError

from schemas.common import PaginationParams, PaginatedResponse, ErrorResponse
from schemas.manufacturing import PartCreate, PartUpdate, PartResponse, LotCreate, LotUpdate, LotResponse
from schemas.inspection import InspectionCreate, InspectionUpdate, InspectionResponse, DefectCreate, DefectResponse
from database.enums import (
    PartTypeEnum,
    LotStatusEnum,
    InspectionTypeEnum,
    InspectionStatusEnum,
    DefectTypeEnum,
    DefectSeverityEnum,
    DetectionMethodEnum,
)


class TestCommonSchemas:
    """Tests for common schemas"""
    
    def test_pagination_params_defaults(self):
        """Test PaginationParams default values"""
        params = PaginationParams()
        assert params.skip == 0
        assert params.limit == 100
    
    def test_pagination_params_validation(self):
        """Test PaginationParams validation"""
        # Valid params
        params = PaginationParams(skip=10, limit=50)
        assert params.skip == 10
        assert params.limit == 50
        
        # Invalid skip (negative)
        with pytest.raises(ValidationError):
            PaginationParams(skip=-1)
        
        # Invalid limit (too high)
        with pytest.raises(ValidationError):
            PaginationParams(limit=2000)
    
    def test_paginated_response(self):
        """Test PaginatedResponse creation"""
        response = PaginatedResponse(
            items=[{"id": 1}, {"id": 2}],
            total=10,
            skip=0,
            limit=2,
            has_more=True
        )
        
        assert len(response.items) == 2
        assert response.total == 10
        assert response.has_more is True
    
    def test_error_response(self):
        """Test ErrorResponse creation"""
        error = ErrorResponse(
            error="validation_error",
            message="Invalid input",
            details={"field": "priority"},
        )
        
        assert error.error == "validation_error"
        assert error.message == "Invalid input"
        assert error.details == {"field": "priority"}


class TestManufacturingSchemas:
    """Tests for manufacturing schemas"""
    
    def test_part_create_valid(self):
        """Test valid PartCreate schema"""
        part = PartCreate(
            part_number="PCB-001",
            part_name="Test PCB",
            part_type=PartTypeEnum.PCB,
            specifications={"layers": 4},
            tolerance_requirements={"dimensional": "±0.1mm"},
        )
        
        assert part.part_number == "PCB-001"
        assert part.part_type == PartTypeEnum.PCB
        assert part.specifications["layers"] == 4
    
    def test_part_create_validation(self):
        """Test PartCreate validation"""
        # Missing required field
        with pytest.raises(ValidationError):
            PartCreate(
                part_name="Test PCB",
                part_type=PartTypeEnum.PCB,
            )
        
        # Empty part_number
        with pytest.raises(ValidationError):
            PartCreate(
                part_number="",
                part_name="Test PCB",
                part_type=PartTypeEnum.PCB,
            )
    
    def test_part_update(self):
        """Test PartUpdate schema"""
        update = PartUpdate(
            part_name="Updated Name",
            specifications={"layers": 8},
        )
        
        assert update.part_name == "Updated Name"
        assert update.specifications["layers"] == 8
        assert update.tolerance_requirements is None
    
    def test_part_response(self):
        """Test PartResponse schema"""
        part_id = uuid4()
        now = datetime.utcnow()
        
        response = PartResponse(
            id=part_id,
            part_number="PCB-001",
            part_name="Test PCB",
            part_type=PartTypeEnum.PCB,
            specifications={},
            tolerance_requirements={},
            version=1,
            created_at=now,
            updated_at=now,
        )
        
        assert response.id == part_id
        assert response.version == 1
    
    def test_lot_create_valid(self):
        """Test valid LotCreate schema"""
        lot = LotCreate(
            lot_number="LOT-001",
            part_id=uuid4(),
            production_date=date(2025, 10, 29),
            batch_size=1000,
            production_line="LINE-A",
        )
        
        assert lot.lot_number == "LOT-001"
        assert lot.batch_size == 1000
    
    def test_lot_create_batch_size_validation(self):
        """Test LotCreate batch_size validation"""
        # Valid batch size
        lot = LotCreate(
            lot_number="LOT-001",
            part_id=uuid4(),
            production_date=date(2025, 10, 29),
            batch_size=100,
            production_line="LINE-A",
        )
        assert lot.batch_size == 100
        
        # Invalid batch size (zero)
        with pytest.raises(ValidationError):
            LotCreate(
                lot_number="LOT-001",
                part_id=uuid4(),
                production_date=date(2025, 10, 29),
                batch_size=0,
                production_line="LINE-A",
            )
        
        # Invalid batch size (too large)
        with pytest.raises(ValidationError):
            LotCreate(
                lot_number="LOT-001",
                part_id=uuid4(),
                production_date=date(2025, 10, 29),
                batch_size=2000000,
                production_line="LINE-A",
            )


class TestInspectionSchemas:
    """Tests for inspection schemas"""
    
    def test_inspection_create_valid(self):
        """Test valid InspectionCreate schema"""
        inspection = InspectionCreate(
            lot_id=uuid4(),
            chip_id="CHIP-001",
            inspection_type=InspectionTypeEnum.VISUAL,
            priority=5,
            station_id="STATION-A",
        )
        
        assert inspection.chip_id == "CHIP-001"
        assert inspection.priority == 5
    
    def test_inspection_create_priority_validation(self):
        """Test InspectionCreate priority validation"""
        # Valid priority
        inspection = InspectionCreate(
            lot_id=uuid4(),
            chip_id="CHIP-001",
            inspection_type=InspectionTypeEnum.VISUAL,
            priority=7,
            station_id="STATION-A",
        )
        assert inspection.priority == 7
        
        # Invalid priority (too low)
        with pytest.raises(ValidationError):
            InspectionCreate(
                lot_id=uuid4(),
                chip_id="CHIP-001",
                inspection_type=InspectionTypeEnum.VISUAL,
                priority=0,
                station_id="STATION-A",
            )
        
        # Invalid priority (too high)
        with pytest.raises(ValidationError):
            InspectionCreate(
                lot_id=uuid4(),
                chip_id="CHIP-001",
                inspection_type=InspectionTypeEnum.VISUAL,
                priority=11,
                station_id="STATION-A",
            )
    
    def test_inspection_update(self):
        """Test InspectionUpdate schema"""
        update = InspectionUpdate(
            status=InspectionStatusEnum.COMPLETED,
            completed_at=datetime.utcnow(),
        )
        
        assert update.status == InspectionStatusEnum.COMPLETED
        assert update.completed_at is not None
    
    def test_defect_create_valid(self):
        """Test valid DefectCreate schema"""
        defect = DefectCreate(
            inspection_id=uuid4(),
            defect_type=DefectTypeEnum.SCRATCH,
            severity=DefectSeverityEnum.MEDIUM,
            confidence=Decimal("0.95"),
            location={"x": 100, "y": 200, "width": 50, "height": 30},
            detection_method=DetectionMethodEnum.ML_AUTOMATED,
        )
        
        assert defect.defect_type == DefectTypeEnum.SCRATCH
        assert defect.confidence == Decimal("0.95")
    
    def test_defect_create_confidence_validation(self):
        """Test DefectCreate confidence validation"""
        # Valid confidence
        defect = DefectCreate(
            inspection_id=uuid4(),
            defect_type=DefectTypeEnum.VOID,
            severity=DefectSeverityEnum.LOW,
            confidence=Decimal("0.85"),
            location={"x": 0, "y": 0, "width": 1, "height": 1},
            detection_method=DetectionMethodEnum.ML_AUTOMATED,
        )
        assert defect.confidence == Decimal("0.85")
        
        # Invalid confidence (too high)
        with pytest.raises(ValidationError):
            DefectCreate(
                inspection_id=uuid4(),
                defect_type=DefectTypeEnum.VOID,
                severity=DefectSeverityEnum.LOW,
                confidence=Decimal("1.5"),
                location={"x": 0, "y": 0, "width": 1, "height": 1},
                detection_method=DetectionMethodEnum.ML_AUTOMATED,
            )
    
    def test_defect_create_location_validation(self):
        """Test DefectCreate location validation"""
        # Valid location
        defect = DefectCreate(
            inspection_id=uuid4(),
            defect_type=DefectTypeEnum.SCRATCH,
            severity=DefectSeverityEnum.MEDIUM,
            confidence=Decimal("0.9"),
            location={"x": 10, "y": 20, "width": 5, "height": 5},
            detection_method=DetectionMethodEnum.ML_AUTOMATED,
        )
        assert "x" in defect.location
        
        # Invalid location (missing fields)
        with pytest.raises(ValidationError):
            DefectCreate(
                inspection_id=uuid4(),
                defect_type=DefectTypeEnum.SCRATCH,
                severity=DefectSeverityEnum.MEDIUM,
                confidence=Decimal("0.9"),
                location={"x": 10, "y": 20},  # Missing width and height
                detection_method=DetectionMethodEnum.ML_AUTOMATED,
            )
