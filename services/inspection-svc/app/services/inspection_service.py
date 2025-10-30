"""
Core inspection workflow orchestration service.

This service manages the complete inspection lifecycle from creation to completion,
coordinating with ML inference, quality assessment, and notification services.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from decimal import Decimal

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import structlog

from services.shared.models.inspection import Inspection, Defect
from services.shared.models.manufacturing import Lot
from services.shared.database.enums import (
    InspectionStatusEnum,
    InspectionTypeEnum,
    ReviewStatusEnum
)
from ..core.exceptions import (
    InspectionNotFoundError,
    DuplicateInspectionError,
    InspectionStatusError,
    ValidationError,
    ResourceNotFoundError
)


logger = structlog.get_logger()


class InspectionService:
    """
    Core inspection workflow orchestration.
    
    Manages the complete inspection lifecycle:
    1. Validation and creation with idempotency
    2. Status tracking and transitions
    3. Integration with ML inference
    4. Quality assessment coordination
    5. Manual review workflow
    6. Event publishing and notifications
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self._idempotency_cache: Dict[str, uuid.UUID] = {}
    
    async def create_inspection(
        self,
        lot_id: uuid.UUID,
        chip_id: str,
        inspection_type: InspectionTypeEnum,
        priority: int = 5,
        station_id: Optional[str] = None,
        operator_id: Optional[uuid.UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None
    ) -> Inspection:
        """
        Create a new inspection with idempotency support.
        
        Args:
            lot_id: Manufacturing lot UUID
            chip_id: Individual chip identifier
            inspection_type: Type of inspection to perform
            priority: Priority level (1-10, higher is more urgent)
            station_id: Inspection station identifier
            operator_id: Operator performing the inspection
            metadata: Additional metadata
            idempotency_key: Unique key for idempotent creation
            
        Returns:
            Created inspection instance
            
        Raises:
            DuplicateInspectionError: If inspection already exists for this key
            ValidationError: If validation fails
            ResourceNotFoundError: If lot not found
        """
        logger.info(
            "Creating inspection",
            lot_id=str(lot_id),
            chip_id=chip_id,
            inspection_type=inspection_type.value,
            priority=priority
        )
        
        # Check idempotency
        if idempotency_key:
            existing_id = await self._check_idempotency(idempotency_key)
            if existing_id:
                return await self.get_inspection(existing_id)
        
        # Validate lot exists
        await self._validate_lot_exists(lot_id)
        
        # Validate priority
        if not 1 <= priority <= 10:
            raise ValidationError("Priority must be between 1 and 10", {"priority": priority})
        
        # Generate unique inspection ID
        inspection_id = self._generate_inspection_id(chip_id, inspection_type)
        
        # Create inspection
        inspection = Inspection(
            inspection_id=inspection_id,
            lot_id=lot_id,
            inspection_type=inspection_type,
            status=InspectionStatusEnum.PENDING,
            review_status=ReviewStatusEnum.PENDING,
            inspector_id=operator_id,
            station_id=station_id or f"STATION-DEFAULT",
            scheduled_at=datetime.utcnow(),
            inspection_parameters=metadata or {},
            correlation_id=str(uuid.uuid4())
        )
        
        self.db.add(inspection)
        await self.db.commit()
        await self.db.refresh(inspection)
        
        # Cache idempotency key
        if idempotency_key:
            self._idempotency_cache[idempotency_key] = inspection.id
        
        logger.info(
            "Inspection created",
            inspection_id=inspection.inspection_id,
            id=str(inspection.id),
            lot_id=str(lot_id)
        )
        
        return inspection
    
    async def get_inspection(self, inspection_id: uuid.UUID) -> Inspection:
        """
        Get inspection by ID with related defects.
        
        Args:
            inspection_id: Inspection UUID
            
        Returns:
            Inspection instance
            
        Raises:
            InspectionNotFoundError: If inspection not found
        """
        query = (
            select(Inspection)
            .options(selectinload(Inspection.defects))
            .where(Inspection.id == inspection_id)
        )
        
        result = await self.db.execute(query)
        inspection = result.scalar_one_or_none()
        
        if not inspection:
            raise InspectionNotFoundError(str(inspection_id))
        
        return inspection
    
    async def get_inspection_by_inspection_id(self, inspection_id: str) -> Inspection:
        """
        Get inspection by inspection_id string.
        
        Args:
            inspection_id: Inspection identifier string
            
        Returns:
            Inspection instance
            
        Raises:
            InspectionNotFoundError: If inspection not found
        """
        query = (
            select(Inspection)
            .options(selectinload(Inspection.defects))
            .where(Inspection.inspection_id == inspection_id)
        )
        
        result = await self.db.execute(query)
        inspection = result.scalar_one_or_none()
        
        if not inspection:
            raise InspectionNotFoundError(inspection_id)
        
        return inspection
    
    async def list_inspections(
        self,
        lot_id: Optional[uuid.UUID] = None,
        status: Optional[InspectionStatusEnum] = None,
        inspection_type: Optional[InspectionTypeEnum] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Inspection]:
        """
        List inspections with filtering.
        
        Args:
            lot_id: Filter by lot ID
            status: Filter by status
            inspection_type: Filter by type
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of inspections
        """
        query = select(Inspection).options(selectinload(Inspection.defects))
        
        filters = []
        if lot_id:
            filters.append(Inspection.lot_id == lot_id)
        if status:
            filters.append(Inspection.status == status)
        if inspection_type:
            filters.append(Inspection.inspection_type == inspection_type)
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.order_by(Inspection.created_at.desc()).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def start_inspection(self, inspection_id: uuid.UUID) -> Inspection:
        """
        Start an inspection (transition to IN_PROGRESS).
        
        Args:
            inspection_id: Inspection UUID
            
        Returns:
            Updated inspection
            
        Raises:
            InspectionNotFoundError: If inspection not found
            InspectionStatusError: If invalid status transition
        """
        inspection = await self.get_inspection(inspection_id)
        
        if inspection.status != InspectionStatusEnum.PENDING:
            raise InspectionStatusError(
                inspection.status.value,
                InspectionStatusEnum.IN_PROGRESS.value
            )
        
        inspection.status = InspectionStatusEnum.IN_PROGRESS
        inspection.started_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(inspection)
        
        logger.info("Inspection started", inspection_id=inspection.inspection_id)
        
        return inspection
    
    async def complete_inspection(
        self,
        inspection_id: uuid.UUID,
        quality_score: Optional[Decimal] = None,
        pass_fail: Optional[bool] = None,
        results: Optional[Dict[str, Any]] = None
    ) -> Inspection:
        """
        Complete an inspection.
        
        Args:
            inspection_id: Inspection UUID
            quality_score: Overall quality score (0-1)
            pass_fail: Pass/fail determination
            results: Processed results
            
        Returns:
            Updated inspection
            
        Raises:
            InspectionNotFoundError: If inspection not found
            InspectionStatusError: If invalid status transition
        """
        inspection = await self.get_inspection(inspection_id)
        
        if inspection.status not in [InspectionStatusEnum.IN_PROGRESS, InspectionStatusEnum.PENDING]:
            raise InspectionStatusError(
                inspection.status.value,
                InspectionStatusEnum.COMPLETED.value
            )
        
        inspection.status = InspectionStatusEnum.COMPLETED
        inspection.completed_at = datetime.utcnow()
        
        if quality_score is not None:
            inspection.overall_quality_score = quality_score
        if pass_fail is not None:
            inspection.pass_fail_status = pass_fail
        if results:
            inspection.processed_results = results
        
        await self.db.commit()
        await self.db.refresh(inspection)
        
        logger.info(
            "Inspection completed",
            inspection_id=inspection.inspection_id,
            quality_score=float(quality_score) if quality_score else None,
            pass_fail=pass_fail
        )
        
        return inspection
    
    async def fail_inspection(
        self,
        inspection_id: uuid.UUID,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> Inspection:
        """
        Mark inspection as failed.
        
        Args:
            inspection_id: Inspection UUID
            error_message: Error description
            error_details: Additional error details
            
        Returns:
            Updated inspection
        """
        inspection = await self.get_inspection(inspection_id)
        
        inspection.status = InspectionStatusEnum.FAILED
        inspection.notes = error_message
        
        if error_details:
            inspection.processed_results = {
                "error": error_message,
                "details": error_details,
                "failed_at": datetime.utcnow().isoformat()
            }
        
        await self.db.commit()
        await self.db.refresh(inspection)
        
        logger.error(
            "Inspection failed",
            inspection_id=inspection.inspection_id,
            error=error_message
        )
        
        return inspection
    
    async def update_inspection_status(
        self,
        inspection_id: uuid.UUID,
        status: InspectionStatusEnum
    ) -> Inspection:
        """
        Update inspection status.
        
        Args:
            inspection_id: Inspection UUID
            status: New status
            
        Returns:
            Updated inspection
        """
        inspection = await self.get_inspection(inspection_id)
        inspection.status = status
        
        await self.db.commit()
        await self.db.refresh(inspection)
        
        logger.info(
            "Inspection status updated",
            inspection_id=inspection.inspection_id,
            status=status.value
        )
        
        return inspection
    
    def _generate_inspection_id(
        self,
        chip_id: str,
        inspection_type: InspectionTypeEnum
    ) -> str:
        """Generate unique inspection ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        type_prefix = inspection_type.value[:3].upper()
        return f"INS-{type_prefix}-{chip_id}-{timestamp}"
    
    async def _check_idempotency(self, idempotency_key: str) -> Optional[uuid.UUID]:
        """Check if idempotency key was already used"""
        if idempotency_key in self._idempotency_cache:
            return self._idempotency_cache[idempotency_key]
        
        # In production, check Redis or database
        return None
    
    async def _validate_lot_exists(self, lot_id: uuid.UUID) -> None:
        """Validate that lot exists"""
        query = select(Lot).where(Lot.id == lot_id)
        result = await self.db.execute(query)
        lot = result.scalar_one_or_none()
        
        if not lot:
            raise ResourceNotFoundError("Lot", str(lot_id))
