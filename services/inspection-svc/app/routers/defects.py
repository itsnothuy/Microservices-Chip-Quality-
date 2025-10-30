"""
Defect API endpoints.

Provides REST API for defect management, review, and analysis.
"""

from typing import List, Optional
from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
import structlog

from services.shared.database.enums import (
    DefectTypeEnum,
    DefectSeverityEnum,
    DetectionMethodEnum
)
from ..core.dependencies import get_db_session
from ..core.exceptions import DefectNotFoundError
from ..services.defect_service import DefectService


logger = structlog.get_logger()
router = APIRouter()


# Request/Response schemas
class DefectCreateRequest(BaseModel):
    """Request to create a new defect"""
    inspection_id: UUID
    defect_type: DefectTypeEnum
    severity: DefectSeverityEnum
    confidence: Decimal = Field(..., ge=0, le=1)
    location: dict
    description: Optional[str] = None
    characteristics: Optional[dict] = None


class DefectResponse(BaseModel):
    """Defect response"""
    id: UUID
    defect_id: str
    inspection_id: UUID
    defect_type: str
    severity: str
    confidence: float
    location: dict
    is_confirmed: bool
    is_false_positive: bool
    created_at: str
    
    model_config = {"from_attributes": True}


@router.post(
    "/",
    response_model=DefectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new defect"
)
async def create_defect(
    request: DefectCreateRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new defect record."""
    try:
        service = DefectService(db)
        
        defect = await service.create_defect(
            inspection_id=request.inspection_id,
            defect_type=request.defect_type,
            severity=request.severity,
            confidence=request.confidence,
            location=request.location,
            description=request.description,
            characteristics=request.characteristics
        )
        
        return DefectResponse(
            id=defect.id,
            defect_id=defect.defect_id,
            inspection_id=defect.inspection_id,
            defect_type=defect.defect_type.value,
            severity=defect.severity.value,
            confidence=float(defect.confidence_score),
            location=defect.location_data,
            is_confirmed=defect.is_confirmed,
            is_false_positive=defect.is_false_positive,
            created_at=defect.created_at.isoformat()
        )
        
    except Exception as e:
        logger.error("Failed to create defect", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create defect: {str(e)}"
        )


@router.get(
    "/{defect_id}",
    response_model=DefectResponse,
    summary="Get defect details"
)
async def get_defect(
    defect_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Get defect by ID."""
    try:
        service = DefectService(db)
        defect = await service.get_defect(defect_id)
        
        return DefectResponse(
            id=defect.id,
            defect_id=defect.defect_id,
            inspection_id=defect.inspection_id,
            defect_type=defect.defect_type.value,
            severity=defect.severity.value,
            confidence=float(defect.confidence_score),
            location=defect.location_data,
            is_confirmed=defect.is_confirmed,
            is_false_positive=defect.is_false_positive,
            created_at=defect.created_at.isoformat()
        )
        
    except DefectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Defect not found: {defect_id}"
        )
    except Exception as e:
        logger.error("Failed to get defect", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get defect: {str(e)}"
        )


@router.post(
    "/{defect_id}/confirm",
    response_model=DefectResponse,
    summary="Confirm defect"
)
async def confirm_defect(
    defect_id: UUID,
    reviewer_id: UUID,
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """Confirm a defect (human review)."""
    try:
        service = DefectService(db)
        defect = await service.confirm_defect(defect_id, reviewer_id, notes)
        
        return DefectResponse(
            id=defect.id,
            defect_id=defect.defect_id,
            inspection_id=defect.inspection_id,
            defect_type=defect.defect_type.value,
            severity=defect.severity.value,
            confidence=float(defect.confidence_score),
            location=defect.location_data,
            is_confirmed=defect.is_confirmed,
            is_false_positive=defect.is_false_positive,
            created_at=defect.created_at.isoformat()
        )
        
    except Exception as e:
        logger.error("Failed to confirm defect", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm defect: {str(e)}"
        )


@router.get(
    "/",
    response_model=List[DefectResponse],
    summary="List defects"
)
async def list_defects(
    inspection_id: Optional[UUID] = None,
    severity: Optional[DefectSeverityEnum] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db_session)
):
    """List defects with filtering."""
    try:
        service = DefectService(db)
        
        defects = await service.list_defects(
            inspection_id=inspection_id,
            severity=severity,
            limit=limit,
            offset=offset
        )
        
        return [
            DefectResponse(
                id=defect.id,
                defect_id=defect.defect_id,
                inspection_id=defect.inspection_id,
                defect_type=defect.defect_type.value,
                severity=defect.severity.value,
                confidence=float(defect.confidence_score),
                location=defect.location_data,
                is_confirmed=defect.is_confirmed,
                is_false_positive=defect.is_false_positive,
                created_at=defect.created_at.isoformat()
            )
            for defect in defects
        ]
        
    except Exception as e:
        logger.error("Failed to list defects", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list defects: {str(e)}"
        )
