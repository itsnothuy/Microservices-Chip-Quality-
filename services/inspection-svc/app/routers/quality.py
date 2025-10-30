"""
Quality API endpoints.

Provides REST API for quality metrics, assessment, and trend analysis.
"""

from typing import Any, Dict, Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.dependencies import get_db_session
from ..services.quality_service import QualityService

logger = structlog.get_logger()
router = APIRouter()


# Response schemas
class QualityMetricsResponse(BaseModel):
    """Quality metrics response"""
    overall_score: float
    defect_count: int
    critical_defect_count: int
    defect_density: float
    pass_rate: float
    confidence: float
    details: Dict[str, Any]


class QualityAssessmentResponse(BaseModel):
    """Quality assessment response"""
    inspection_id: str
    passed: bool
    metrics: QualityMetricsResponse
    thresholds: Dict[str, float]
    violations: list
    assessed_at: str


class QualityTrendsResponse(BaseModel):
    """Quality trends response"""
    period_days: int
    trends: list
    summary: Dict[str, Any]


@router.get(
    "/metrics/{inspection_id}",
    response_model=QualityMetricsResponse,
    summary="Get quality metrics"
)
async def get_quality_metrics(
    inspection_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get quality metrics for an inspection.
    
    - **inspection_id**: Inspection UUID
    """
    try:
        from ..services.inspection_service import InspectionService
        
        inspection_service = InspectionService(db)
        quality_service = QualityService(db)
        
        # Get inspection
        inspection = await inspection_service.get_inspection(inspection_id)
        
        # Calculate metrics
        metrics = await quality_service.calculate_quality_metrics(inspection)
        
        return QualityMetricsResponse(**metrics.to_dict())
        
    except Exception as e:
        logger.error("Failed to get quality metrics", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quality metrics: {str(e)}"
        )


@router.get(
    "/assessment/{inspection_id}",
    response_model=QualityAssessmentResponse,
    summary="Get quality assessment"
)
async def get_quality_assessment(
    inspection_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get quality assessment with pass/fail determination.
    
    - **inspection_id**: Inspection UUID
    """
    try:
        quality_service = QualityService(db)
        
        assessment = await quality_service.assess_quality(inspection_id)
        
        return QualityAssessmentResponse(
            inspection_id=assessment["inspection_id"],
            passed=assessment["passed"],
            metrics=QualityMetricsResponse(**assessment["metrics"]),
            thresholds=assessment["thresholds"],
            violations=assessment["violations"],
            assessed_at=assessment["assessed_at"]
        )
        
    except Exception as e:
        logger.error("Failed to get quality assessment", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quality assessment: {str(e)}"
        )


@router.get(
    "/trends",
    response_model=QualityTrendsResponse,
    summary="Get quality trends"
)
async def get_quality_trends(
    lot_id: Optional[UUID] = None,
    days: int = 7,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get quality trend analysis over time.
    
    - **lot_id**: Optional lot ID to filter by
    - **days**: Number of days to analyze (default 7)
    """
    try:
        quality_service = QualityService(db)
        
        trends = await quality_service.get_quality_trends(lot_id=lot_id, days=days)
        
        return QualityTrendsResponse(**trends)
        
    except Exception as e:
        logger.error("Failed to get quality trends", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quality trends: {str(e)}"
        )
