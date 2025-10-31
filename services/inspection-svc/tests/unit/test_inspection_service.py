"""Unit tests for inspection service"""

import pytest
from decimal import Decimal
from datetime import datetime
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from services.shared.database.enums import (
    InspectionTypeEnum,
    InspectionStatusEnum,
    ReviewStatusEnum
)
from app.services.inspection_service import InspectionService
from app.core.exceptions import (
    InspectionNotFoundError,
    ValidationError,
    ResourceNotFoundError
)


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def inspection_service(mock_db_session):
    """Create inspection service with mocked session"""
    return InspectionService(mock_db_session)


class TestInspectionService:
    """Test cases for InspectionService"""
    
    @pytest.mark.asyncio
    async def test_create_inspection_success(self, inspection_service, mock_db_session):
        """Test successful inspection creation"""
        lot_id = uuid.uuid4()
        chip_id = "CHIP-001"
        inspection_type = InspectionTypeEnum.VISUAL
        
        # Mock lot validation
        mock_lot = MagicMock()
        mock_db_session.execute.return_value.scalar_one_or_none = AsyncMock(return_value=mock_lot)
        
        # Create inspection
        inspection = await inspection_service.create_inspection(
            lot_id=lot_id,
            chip_id=chip_id,
            inspection_type=inspection_type,
            priority=5
        )
        
        # Assertions
        assert inspection is not None
        assert inspection.lot_id == lot_id
        assert inspection.inspection_type == inspection_type
        assert inspection.status == InspectionStatusEnum.PENDING
        
        # Verify database operations
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_inspection_invalid_priority(self, inspection_service):
        """Test inspection creation with invalid priority"""
        with pytest.raises(ValidationError) as exc_info:
            await inspection_service.create_inspection(
                lot_id=uuid.uuid4(),
                chip_id="CHIP-001",
                inspection_type=InspectionTypeEnum.VISUAL,
                priority=11  # Invalid: > 10
            )
        
        assert "Priority must be between 1 and 10" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_inspection_lot_not_found(self, inspection_service, mock_db_session):
        """Test inspection creation when lot doesn't exist"""
        # Mock lot not found
        mock_db_session.execute.return_value.scalar_one_or_none = AsyncMock(return_value=None)
        
        with pytest.raises(ResourceNotFoundError) as exc_info:
            await inspection_service.create_inspection(
                lot_id=uuid.uuid4(),
                chip_id="CHIP-001",
                inspection_type=InspectionTypeEnum.VISUAL
            )
        
        assert "Lot" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_inspection_with_idempotency(self, inspection_service, mock_db_session):
        """Test idempotent inspection creation"""
        lot_id = uuid.uuid4()
        chip_id = "CHIP-001"
        idempotency_key = "test-key-123"
        
        # Mock lot validation
        mock_lot = MagicMock()
        mock_db_session.execute.return_value.scalar_one_or_none = AsyncMock(return_value=mock_lot)
        
        # First creation
        inspection1 = await inspection_service.create_inspection(
            lot_id=lot_id,
            chip_id=chip_id,
            inspection_type=InspectionTypeEnum.VISUAL,
            idempotency_key=idempotency_key
        )
        
        # Mock get_inspection for second call
        inspection_service.get_inspection = AsyncMock(return_value=inspection1)
        
        # Second creation with same key should return cached result
        inspection2 = await inspection_service.create_inspection(
            lot_id=lot_id,
            chip_id=chip_id,
            inspection_type=InspectionTypeEnum.VISUAL,
            idempotency_key=idempotency_key
        )
        
        assert inspection1.id == inspection2.id
    
    @pytest.mark.asyncio
    async def test_start_inspection_success(self, inspection_service):
        """Test starting an inspection"""
        inspection_id = uuid.uuid4()
        
        # Mock inspection in PENDING state
        mock_inspection = MagicMock()
        mock_inspection.id = inspection_id
        mock_inspection.status = InspectionStatusEnum.PENDING
        mock_inspection.inspection_id = "INS-VIS-CHIP-001-20251030"
        
        inspection_service.get_inspection = AsyncMock(return_value=mock_inspection)
        
        # Start inspection
        result = await inspection_service.start_inspection(inspection_id)
        
        # Assertions
        assert result.status == InspectionStatusEnum.IN_PROGRESS
        assert result.started_at is not None
    
    @pytest.mark.asyncio
    async def test_complete_inspection_success(self, inspection_service, mock_db_session):
        """Test completing an inspection"""
        inspection_id = uuid.uuid4()
        quality_score = Decimal("0.95")
        
        # Mock inspection in IN_PROGRESS state
        mock_inspection = MagicMock()
        mock_inspection.id = inspection_id
        mock_inspection.status = InspectionStatusEnum.IN_PROGRESS
        mock_inspection.inspection_id = "INS-VIS-CHIP-001-20251030"
        
        inspection_service.get_inspection = AsyncMock(return_value=mock_inspection)
        
        # Complete inspection
        result = await inspection_service.complete_inspection(
            inspection_id=inspection_id,
            quality_score=quality_score,
            pass_fail=True
        )
        
        # Assertions
        assert result.status == InspectionStatusEnum.COMPLETED
        assert result.completed_at is not None
        assert result.overall_quality_score == quality_score
        assert result.pass_fail_status is True
    
    def test_generate_inspection_id(self, inspection_service):
        """Test inspection ID generation"""
        chip_id = "CHIP-001"
        inspection_type = InspectionTypeEnum.VISUAL
        
        inspection_id = inspection_service._generate_inspection_id(chip_id, inspection_type)
        
        assert inspection_id.startswith("INS-VIS-")
        assert chip_id in inspection_id
        assert len(inspection_id) > 10
