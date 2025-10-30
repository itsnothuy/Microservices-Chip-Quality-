"""Integration tests for database operations"""

import pytest
from datetime import date
from decimal import Decimal
import uuid

from sqlalchemy import select

from models.manufacturing import Part, Lot
from models.inspection import Inspection, Defect
from database.enums import (
    PartTypeEnum,
    LotStatusEnum,
    InspectionTypeEnum,
    InspectionStatusEnum,
    DefectTypeEnum,
    DefectSeverityEnum,
    DetectionMethodEnum,
)


@pytest.mark.integration
@pytest.mark.database
class TestDatabaseIntegration:
    """Integration tests for database operations"""
    
    @pytest.mark.asyncio
    async def test_create_part(self, db_session):
        """Test creating a part in the database"""
        part = Part(
            part_number="TEST-PCB-001",
            part_name="Test PCB",
            part_type=PartTypeEnum.PCB,
            specifications={"layers": 4},
            tolerance_requirements={"dimensional": "±0.1mm"},
        )
        
        db_session.add(part)
        await db_session.commit()
        await db_session.refresh(part)
        
        assert part.id is not None
        assert part.created_at is not None
        assert part.updated_at is not None
        assert part.version == 1
    
    @pytest.mark.asyncio
    async def test_create_lot_with_part(self, db_session):
        """Test creating a lot with part relationship"""
        # Create part
        part = Part(
            part_number="TEST-PCB-002",
            part_name="Test PCB 2",
            part_type=PartTypeEnum.PCB,
        )
        db_session.add(part)
        await db_session.commit()
        await db_session.refresh(part)
        
        # Create lot
        lot = Lot(
            lot_number="LOT-TEST-001",
            part_id=part.id,
            production_date=date(2025, 10, 29),
            batch_size=1000,
            production_line="LINE-A",
        )
        db_session.add(lot)
        await db_session.commit()
        await db_session.refresh(lot)
        
        assert lot.id is not None
        assert lot.part_id == part.id
        assert lot.status == LotStatusEnum.ACTIVE
        
        # Verify relationship
        result = await db_session.execute(
            select(Lot).where(Lot.id == lot.id)
        )
        retrieved_lot = result.scalar_one()
        assert retrieved_lot.part_id == part.id
    
    @pytest.mark.asyncio
    async def test_create_inspection_with_lot(self, db_session):
        """Test creating an inspection with lot relationship"""
        # Create part and lot
        part = Part(
            part_number="TEST-PCB-003",
            part_name="Test PCB 3",
            part_type=PartTypeEnum.PCB,
        )
        db_session.add(part)
        await db_session.commit()
        await db_session.refresh(part)
        
        lot = Lot(
            lot_number="LOT-TEST-002",
            part_id=part.id,
            production_date=date(2025, 10, 29),
            batch_size=500,
            production_line="LINE-B",
        )
        db_session.add(lot)
        await db_session.commit()
        await db_session.refresh(lot)
        
        # Create inspection
        inspection = Inspection(
            lot_id=lot.id,
            chip_id="CHIP-TEST-001",
            inspection_type=InspectionTypeEnum.VISUAL,
            priority=5,
            station_id="STATION-A",
        )
        db_session.add(inspection)
        await db_session.commit()
        await db_session.refresh(inspection)
        
        assert inspection.id is not None
        assert inspection.lot_id == lot.id
        assert inspection.status == InspectionStatusEnum.PENDING
    
    @pytest.mark.asyncio
    async def test_create_defect_with_inspection(self, db_session):
        """Test creating a defect with inspection relationship"""
        # Create part, lot, and inspection
        part = Part(
            part_number="TEST-PCB-004",
            part_name="Test PCB 4",
            part_type=PartTypeEnum.PCB,
        )
        db_session.add(part)
        await db_session.commit()
        await db_session.refresh(part)
        
        lot = Lot(
            lot_number="LOT-TEST-003",
            part_id=part.id,
            production_date=date(2025, 10, 29),
            batch_size=200,
            production_line="LINE-C",
        )
        db_session.add(lot)
        await db_session.commit()
        await db_session.refresh(lot)
        
        inspection = Inspection(
            lot_id=lot.id,
            chip_id="CHIP-TEST-002",
            inspection_type=InspectionTypeEnum.VISUAL,
            priority=7,
            station_id="STATION-B",
        )
        db_session.add(inspection)
        await db_session.commit()
        await db_session.refresh(inspection)
        
        # Create defect
        defect = Defect(
            inspection_id=inspection.id,
            defect_type=DefectTypeEnum.SCRATCH,
            severity=DefectSeverityEnum.MEDIUM,
            confidence=Decimal("0.95"),
            location={"x": 100, "y": 200, "width": 50, "height": 30},
            detection_method=DetectionMethodEnum.ML_AUTOMATED,
        )
        db_session.add(defect)
        await db_session.commit()
        await db_session.refresh(defect)
        
        assert defect.id is not None
        assert defect.inspection_id == inspection.id
        assert defect.confidence == Decimal("0.95")
    
    @pytest.mark.asyncio
    async def test_query_part_by_part_number(self, db_session):
        """Test querying part by part number"""
        # Create part
        part = Part(
            part_number="QUERY-TEST-001",
            part_name="Query Test Part",
            part_type=PartTypeEnum.SEMICONDUCTOR,
        )
        db_session.add(part)
        await db_session.commit()
        
        # Query by part number
        result = await db_session.execute(
            select(Part).where(Part.part_number == "QUERY-TEST-001")
        )
        retrieved_part = result.scalar_one()
        
        assert retrieved_part.part_name == "Query Test Part"
        assert retrieved_part.part_type == PartTypeEnum.SEMICONDUCTOR
    
    @pytest.mark.asyncio
    async def test_update_inspection_status(self, db_session):
        """Test updating inspection status"""
        # Create part, lot, and inspection
        part = Part(
            part_number="UPDATE-TEST-001",
            part_name="Update Test Part",
            part_type=PartTypeEnum.PCB,
        )
        db_session.add(part)
        await db_session.commit()
        await db_session.refresh(part)
        
        lot = Lot(
            lot_number="LOT-UPDATE-001",
            part_id=part.id,
            production_date=date(2025, 10, 29),
            batch_size=100,
            production_line="LINE-D",
        )
        db_session.add(lot)
        await db_session.commit()
        await db_session.refresh(lot)
        
        inspection = Inspection(
            lot_id=lot.id,
            chip_id="CHIP-UPDATE-001",
            inspection_type=InspectionTypeEnum.ELECTRICAL,
            priority=3,
            station_id="STATION-C",
        )
        db_session.add(inspection)
        await db_session.commit()
        await db_session.refresh(inspection)
        
        # Update status
        inspection.status = InspectionStatusEnum.COMPLETED
        await db_session.commit()
        await db_session.refresh(inspection)
        
        assert inspection.status == InspectionStatusEnum.COMPLETED
    
    @pytest.mark.asyncio
    async def test_cascade_delete_inspection_to_defects(self, db_session):
        """Test cascade delete from inspection to defects"""
        # Create part, lot, inspection, and defect
        part = Part(
            part_number="CASCADE-TEST-001",
            part_name="Cascade Test Part",
            part_type=PartTypeEnum.PCB,
        )
        db_session.add(part)
        await db_session.commit()
        await db_session.refresh(part)
        
        lot = Lot(
            lot_number="LOT-CASCADE-001",
            part_id=part.id,
            production_date=date(2025, 10, 29),
            batch_size=50,
            production_line="LINE-E",
        )
        db_session.add(lot)
        await db_session.commit()
        await db_session.refresh(lot)
        
        inspection = Inspection(
            lot_id=lot.id,
            chip_id="CHIP-CASCADE-001",
            inspection_type=InspectionTypeEnum.VISUAL,
            priority=5,
            station_id="STATION-D",
        )
        db_session.add(inspection)
        await db_session.commit()
        await db_session.refresh(inspection)
        
        defect = Defect(
            inspection_id=inspection.id,
            defect_type=DefectTypeEnum.VOID,
            severity=DefectSeverityEnum.LOW,
            confidence=Decimal("0.85"),
            location={"x": 10, "y": 20, "width": 5, "height": 5},
            detection_method=DetectionMethodEnum.ML_AUTOMATED,
        )
        db_session.add(defect)
        await db_session.commit()
        defect_id = defect.id
        
        # Delete inspection (should cascade to defect)
        await db_session.delete(inspection)
        await db_session.commit()
        
        # Verify defect is also deleted
        result = await db_session.execute(
            select(Defect).where(Defect.id == defect_id)
        )
        assert result.scalar_one_or_none() is None
    
    @pytest.mark.asyncio
    async def test_unique_constraint_part_number(self, db_session):
        """Test unique constraint on part number"""
        part1 = Part(
            part_number="UNIQUE-TEST-001",
            part_name="Unique Test Part 1",
            part_type=PartTypeEnum.PCB,
        )
        db_session.add(part1)
        await db_session.commit()
        
        # Try to create another part with the same part_number
        part2 = Part(
            part_number="UNIQUE-TEST-001",
            part_name="Unique Test Part 2",
            part_type=PartTypeEnum.PCB,
        )
        db_session.add(part2)
        
        with pytest.raises(Exception):  # Will raise IntegrityError
            await db_session.commit()
