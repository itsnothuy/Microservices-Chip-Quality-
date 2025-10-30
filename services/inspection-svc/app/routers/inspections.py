"""
Inspection API endpoints.

Provides REST API for inspection management, workflow orchestration,
and status tracking.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
import structlog

from services.shared.database.enums import (
    InspectionTypeEnum,
    InspectionStatusEnum
)
from ..core.dependencies import get_db_session
from ..core.exceptions import (
    InspectionServiceError,
    InspectionNotFoundError,
    DuplicateInspectionError
)
from ..services.inspection_service import InspectionService
from ..services.quality_service import QualityService
from ..services.ml_service import MLService
from ..services.defect_service import DefectService
from ..services.notification_service import NotificationService


logger = structlog.get_logger()
router = APIRouter()


# Request/Response schemas
class InspectionCreateRequest(BaseModel):
    """Request to create a new inspection"""
    lot_id: UUID = Field(..., description="Manufacturing lot UUID")
    chip_id: str = Field(..., min_length=1, max_length=100, description="Chip identifier")
    inspection_type: InspectionTypeEnum = Field(..., description="Type of inspection")
    priority: int = Field(default=5, ge=1, le=10, description="Priority (1-10)")
    station_id: Optional[str] = Field(None, description="Inspection station ID")
    operator_id: Optional[UUID] = Field(None, description="Operator UUID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class InspectionResponse(BaseModel):
    """Inspection response"""
    id: UUID
    inspection_id: str
    lot_id: UUID
    inspection_type: str
    status: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    quality_score: Optional[float] = None
    pass_fail: Optional[bool] = None
    defect_count: int = 0
    
    model_config = {"from_attributes": True}


class InspectionListResponse(BaseModel):
    """List of inspections with pagination"""
    inspections: List[InspectionResponse]
    total: int
    limit: int
    offset: int


@router.post(
    "/",
    response_model=InspectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new inspection"
)
async def create_inspection(
    request: InspectionCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """
    Create a new inspection with idempotency support.
    
    - **lot_id**: Manufacturing lot identifier
    - **chip_id**: Individual chip identifier
    - **inspection_type**: Type of quality inspection
    - **priority**: Priority level (1-10, higher is more urgent)
    - **station_id**: Inspection station identifier
    - **operator_id**: Operator performing inspection
    - **metadata**: Additional metadata
    
    Supports idempotency via Idempotency-Key header.
    """
    try:
        service = InspectionService(db)
        notification_service = NotificationService()
        
        inspection = await service.create_inspection(
            lot_id=request.lot_id,
            chip_id=request.chip_id,
            inspection_type=request.inspection_type,
            priority=request.priority,
            station_id=request.station_id,
            operator_id=request.operator_id,
            metadata=request.metadata,
            idempotency_key=idempotency_key
        )
        
        # Send notification
        await notification_service.send_inspection_created(
            inspection_id=inspection.id,
            lot_id=request.lot_id,
            inspection_type=request.inspection_type.value
        )
        
        return InspectionResponse(
            id=inspection.id,
            inspection_id=inspection.inspection_id,
            lot_id=inspection.lot_id,
            inspection_type=inspection.inspection_type.value,
            status=inspection.status.value,
            created_at=inspection.created_at.isoformat(),
            started_at=inspection.started_at.isoformat() if inspection.started_at else None,
            completed_at=inspection.completed_at.isoformat() if inspection.completed_at else None,
            quality_score=float(inspection.overall_quality_score) if inspection.overall_quality_score else None,
            pass_fail=inspection.pass_fail_status,
            defect_count=len(inspection.defects) if inspection.defects else 0
        )
        
    except InspectionServiceError:
        raise
    except Exception as e:
        logger.error("Failed to create inspection", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create inspection: {str(e)}"
        )


@router.get(
    "/",
    response_model=InspectionListResponse,
    summary="List inspections"
)
async def list_inspections(
    lot_id: Optional[UUID] = None,
    inspection_status: Optional[InspectionStatusEnum] = None,
    inspection_type: Optional[InspectionTypeEnum] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db_session)
):
    """
    List inspections with filtering and pagination.
    
    - **lot_id**: Filter by lot ID
    - **inspection_status**: Filter by status
    - **inspection_type**: Filter by type
    - **limit**: Maximum results (default 50)
    - **offset**: Pagination offset (default 0)
    """
    try:
        service = InspectionService(db)
        
        inspections = await service.list_inspections(
            lot_id=lot_id,
            status=inspection_status,
            inspection_type=inspection_type,
            limit=limit,
            offset=offset
        )
        
        responses = []
        for inspection in inspections:
            responses.append(InspectionResponse(
                id=inspection.id,
                inspection_id=inspection.inspection_id,
                lot_id=inspection.lot_id,
                inspection_type=inspection.inspection_type.value,
                status=inspection.status.value,
                created_at=inspection.created_at.isoformat(),
                started_at=inspection.started_at.isoformat() if inspection.started_at else None,
                completed_at=inspection.completed_at.isoformat() if inspection.completed_at else None,
                quality_score=float(inspection.overall_quality_score) if inspection.overall_quality_score else None,
                pass_fail=inspection.pass_fail_status,
                defect_count=len(inspection.defects) if inspection.defects else 0
            ))
        
        return InspectionListResponse(
            inspections=responses,
            total=len(responses),
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error("Failed to list inspections", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list inspections: {str(e)}"
        )


@router.get(
    "/{inspection_id}",
    response_model=InspectionResponse,
    summary="Get inspection details"
)
async def get_inspection(
    inspection_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get detailed inspection information by ID.
    
    - **inspection_id**: Inspection UUID
    """
    try:
        service = InspectionService(db)
        inspection = await service.get_inspection(inspection_id)
        
        return InspectionResponse(
            id=inspection.id,
            inspection_id=inspection.inspection_id,
            lot_id=inspection.lot_id,
            inspection_type=inspection.inspection_type.value,
            status=inspection.status.value,
            created_at=inspection.created_at.isoformat(),
            started_at=inspection.started_at.isoformat() if inspection.started_at else None,
            completed_at=inspection.completed_at.isoformat() if inspection.completed_at else None,
            quality_score=float(inspection.overall_quality_score) if inspection.overall_quality_score else None,
            pass_fail=inspection.pass_fail_status,
            defect_count=len(inspection.defects) if inspection.defects else 0
        )
        
    except InspectionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection not found: {inspection_id}"
        )
    except Exception as e:
        logger.error("Failed to get inspection", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get inspection: {str(e)}"
        )


@router.post(
    "/{inspection_id}/start",
    response_model=InspectionResponse,
    summary="Start inspection"
)
async def start_inspection(
    inspection_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Start an inspection (transition to IN_PROGRESS).
    
    - **inspection_id**: Inspection UUID
    """
    try:
        service = InspectionService(db)
        inspection = await service.start_inspection(inspection_id)
        
        return InspectionResponse(
            id=inspection.id,
            inspection_id=inspection.inspection_id,
            lot_id=inspection.lot_id,
            inspection_type=inspection.inspection_type.value,
            status=inspection.status.value,
            created_at=inspection.created_at.isoformat(),
            started_at=inspection.started_at.isoformat() if inspection.started_at else None,
            completed_at=inspection.completed_at.isoformat() if inspection.completed_at else None,
            quality_score=float(inspection.overall_quality_score) if inspection.overall_quality_score else None,
            pass_fail=inspection.pass_fail_status,
            defect_count=len(inspection.defects) if inspection.defects else 0
        )
        
    except InspectionServiceError:
        raise
    except Exception as e:
        logger.error("Failed to start inspection", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start inspection: {str(e)}"
        )


@router.post(
    "/{inspection_id}/complete",
    response_model=InspectionResponse,
    summary="Complete inspection"
)
async def complete_inspection(
    inspection_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Complete an inspection.
    
    - **inspection_id**: Inspection UUID
    """
    try:
        service = InspectionService(db)
        quality_service = QualityService(db)
        notification_service = NotificationService()
        
        # Get inspection
        inspection = await service.get_inspection(inspection_id)
        
        # Calculate quality metrics
        metrics = await quality_service.calculate_quality_metrics(inspection)
        
        # Complete inspection with quality results
        inspection = await service.complete_inspection(
            inspection_id=inspection_id,
            quality_score=metrics.overall_score,
            pass_fail=metrics.pass_rate > 0,
            results=metrics.to_dict()
        )
        
        # Send completion notification
        await notification_service.send_inspection_completed(
            inspection_id=inspection.id,
            quality_score=float(metrics.overall_score),
            passed=metrics.pass_rate > 0
        )
        
        return InspectionResponse(
            id=inspection.id,
            inspection_id=inspection.inspection_id,
            lot_id=inspection.lot_id,
            inspection_type=inspection.inspection_type.value,
            status=inspection.status.value,
            created_at=inspection.created_at.isoformat(),
            started_at=inspection.started_at.isoformat() if inspection.started_at else None,
            completed_at=inspection.completed_at.isoformat() if inspection.completed_at else None,
            quality_score=float(inspection.overall_quality_score) if inspection.overall_quality_score else None,
            pass_fail=inspection.pass_fail_status,
            defect_count=len(inspection.defects) if inspection.defects else 0
        )
        
    except InspectionServiceError:
        raise
    except Exception as e:
        logger.error("Failed to complete inspection", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete inspection: {str(e)}"
        )
