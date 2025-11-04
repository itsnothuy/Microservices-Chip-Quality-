"""
Analytics API endpoints.
"""

from datetime import date
from typing import Optional, List

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.schemas.analytics import (
    QualityAnalyticsRequest,
    QualityAnalyticsResponse,
    SPCAnalyticsRequest,
    SPCAnalyticsResponse,
    ProcessCapabilityRequest,
    ProcessCapabilityResponse,
    ParetoAnalyticsRequest,
    ParetoAnalyticsResponse,
    ProductionAnalyticsResponse
)
from app.services.analytics_service import AnalyticsService

logger = structlog.get_logger()
router = APIRouter()


@router.post("/quality", response_model=QualityAnalyticsResponse)
async def get_quality_analytics(
    request: QualityAnalyticsRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get comprehensive quality analytics.
    
    Provides quality summary metrics, defect distribution, trend data,
    and top defects for the specified period.
    """
    logger.info(
        "Getting quality analytics",
        start_date=request.start_date,
        end_date=request.end_date
    )
    
    try:
        service = AnalyticsService(db)
        result = await service.get_quality_analytics(request)
        
        logger.info(
            "Quality analytics computed",
            total_inspections=result.summary.total_inspections
        )
        
        return result
    except Exception as e:
        logger.error(
            "Failed to compute quality analytics",
            error=str(e),
            exc_info=True
        )
        raise


@router.post("/spc", response_model=SPCAnalyticsResponse)
async def get_spc_analytics(
    request: SPCAnalyticsRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get Statistical Process Control (SPC) analytics.
    
    Generates control charts with control limits, identifies out-of-control
    points, and assesses process stability.
    """
    logger.info(
        "Getting SPC analytics",
        metric=request.metric,
        chart_type=request.chart_type
    )
    
    try:
        service = AnalyticsService(db)
        result = await service.get_spc_analytics(request)
        
        logger.info(
            "SPC analytics computed",
            data_points=len(result.data_points),
            out_of_control=result.out_of_control_count
        )
        
        return result
    except Exception as e:
        logger.error(
            "Failed to compute SPC analytics",
            error=str(e),
            exc_info=True
        )
        raise


@router.post("/capability", response_model=ProcessCapabilityResponse)
async def get_process_capability(
    request: ProcessCapabilityRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get process capability analysis.
    
    Calculates Cp, Cpk, Pp, and Ppk indices to assess process capability
    relative to specification limits.
    """
    logger.info(
        "Getting process capability analysis",
        metric=request.metric
    )
    
    try:
        service = AnalyticsService(db)
        result = await service.get_process_capability(request)
        
        logger.info(
            "Process capability computed",
            cpk=result.metrics.cpk,
            assessment=result.capability_assessment
        )
        
        return result
    except Exception as e:
        logger.error(
            "Failed to compute process capability",
            error=str(e),
            exc_info=True
        )
        raise


@router.post("/pareto", response_model=ParetoAnalyticsResponse)
async def get_pareto_analysis(
    request: ParetoAnalyticsRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get Pareto analysis for defect prioritization.
    
    Identifies the vital few defect categories that contribute to
    the majority of quality issues.
    """
    logger.info(
        "Getting Pareto analysis",
        category_field=request.category_field
    )
    
    try:
        service = AnalyticsService(db)
        result = await service.get_pareto_analysis(request)
        
        logger.info(
            "Pareto analysis computed",
            total_items=len(result.items),
            vital_few=len(result.vital_few_categories)
        )
        
        return result
    except Exception as e:
        logger.error(
            "Failed to compute Pareto analysis",
            error=str(e),
            exc_info=True
        )
        raise


@router.get("/production", response_model=ProductionAnalyticsResponse)
async def get_production_analytics(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    production_line: Optional[str] = Query(None, description="Filter by production line"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get production performance analytics.
    
    Calculates OEE (Overall Equipment Effectiveness) and related
    production metrics.
    """
    logger.info(
        "Getting production analytics",
        start_date=start_date,
        end_date=end_date
    )
    
    try:
        service = AnalyticsService(db)
        result = await service.get_production_analytics(
            start_date,
            end_date,
            production_line
        )
        
        logger.info(
            "Production analytics computed",
            oee=result.metrics.oee
        )
        
        return result
    except Exception as e:
        logger.error(
            "Failed to compute production analytics",
            error=str(e),
            exc_info=True
        )
        raise


@router.get("/trends")
async def get_quality_trends(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    metric: str = Query(..., description="Metric to analyze"),
    grouping: str = Query(default="daily", description="Time grouping (daily, weekly, monthly)"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get quality trend analysis.
    
    Analyzes quality metrics over time with configurable time grouping.
    """
    logger.info(
        "Getting quality trends",
        metric=metric,
        grouping=grouping
    )
    
    try:
        service = AnalyticsService(db)
        result = await service.get_quality_trends(
            start_date,
            end_date,
            metric,
            grouping
        )
        
        return result
    except Exception as e:
        logger.error(
            "Failed to compute quality trends",
            error=str(e),
            exc_info=True
        )
        raise
