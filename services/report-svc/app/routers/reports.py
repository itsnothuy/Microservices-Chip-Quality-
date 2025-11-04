"""
Report management API endpoints.
"""

from typing import List, Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.core.exceptions import ReportNotFoundError
from app.schemas.report import (
    ReportCreateRequest,
    ReportResponse,
    ReportListResponse,
    ReportRegenerateRequest,
    ScheduledReportSchema,
    ScheduledReportCreateRequest,
    ScheduledReportUpdateRequest,
    ScheduledReportListResponse
)
from app.services.report_service import ReportService

logger = structlog.get_logger()
router = APIRouter()


@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    request: ReportCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Query(default="system", description="User ID for authorization")
):
    """
    Generate a new report.
    
    - **report_type**: Type of report to generate
    - **title**: Report title
    - **date_range**: Date range for the report data
    - **filters**: Additional filters for the report
    - **format**: Output format (PDF, Excel, CSV, JSON)
    """
    logger.info(
        "Creating report",
        report_type=request.report_type,
        format=request.format,
        user_id=user_id
    )
    
    try:
        service = ReportService(db)
        report = await service.create_report(request, user_id=UUID(user_id))
        
        logger.info(
            "Report created successfully",
            report_id=str(report.id),
            report_type=request.report_type
        )
        
        return report
    except Exception as e:
        logger.error(
            "Failed to create report",
            error=str(e),
            report_type=request.report_type,
            exc_info=True
        )
        raise


@router.get("/", response_model=ReportListResponse)
async def list_reports(
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Query(default="system", description="User ID for authorization"),
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Page size")
):
    """
    List reports with filtering and pagination.
    
    - **report_type**: Filter by report type (optional)
    - **status**: Filter by status (optional)
    - **page**: Page number for pagination
    - **page_size**: Number of items per page
    """
    logger.info(
        "Listing reports",
        user_id=user_id,
        report_type=report_type,
        status=status,
        page=page
    )
    
    try:
        service = ReportService(db)
        result = await service.list_reports(
            user_id=UUID(user_id),
            report_type=report_type,
            status_filter=status,
            page=page,
            page_size=page_size
        )
        
        return result
    except Exception as e:
        logger.error(
            "Failed to list reports",
            error=str(e),
            exc_info=True
        )
        raise


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Query(default="system", description="User ID for authorization")
):
    """
    Get report details by ID.
    
    - **report_id**: UUID of the report
    """
    logger.info(
        "Getting report details",
        report_id=str(report_id),
        user_id=user_id
    )
    
    try:
        service = ReportService(db)
        report = await service.get_report(report_id, user_id=UUID(user_id))
        
        if not report:
            raise ReportNotFoundError(str(report_id))
        
        return report
    except ReportNotFoundError:
        raise
    except Exception as e:
        logger.error(
            "Failed to get report",
            report_id=str(report_id),
            error=str(e),
            exc_info=True
        )
        raise


@router.get("/{report_id}/download")
async def download_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Query(default="system", description="User ID for authorization")
):
    """
    Download report file.
    
    - **report_id**: UUID of the report
    """
    logger.info(
        "Downloading report",
        report_id=str(report_id),
        user_id=user_id
    )
    
    try:
        service = ReportService(db)
        file_stream, filename, media_type = await service.download_report(
            report_id,
            user_id=UUID(user_id)
        )
        
        return StreamingResponse(
            file_stream,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except ReportNotFoundError:
        raise
    except Exception as e:
        logger.error(
            "Failed to download report",
            report_id=str(report_id),
            error=str(e),
            exc_info=True
        )
        raise


@router.post("/{report_id}/regenerate", response_model=ReportResponse)
async def regenerate_report(
    report_id: UUID,
    request: ReportRegenerateRequest,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Query(default="system", description="User ID for authorization")
):
    """
    Regenerate an existing report, optionally in a different format.
    
    - **report_id**: UUID of the report to regenerate
    - **format**: New output format (optional)
    """
    logger.info(
        "Regenerating report",
        report_id=str(report_id),
        new_format=request.format,
        user_id=user_id
    )
    
    try:
        service = ReportService(db)
        report = await service.regenerate_report(
            report_id,
            new_format=request.format,
            user_id=UUID(user_id)
        )
        
        logger.info(
            "Report regenerated successfully",
            report_id=str(report.id)
        )
        
        return report
    except ReportNotFoundError:
        raise
    except Exception as e:
        logger.error(
            "Failed to regenerate report",
            report_id=str(report_id),
            error=str(e),
            exc_info=True
        )
        raise


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Query(default="system", description="User ID for authorization")
):
    """
    Delete a report.
    
    - **report_id**: UUID of the report to delete
    """
    logger.info(
        "Deleting report",
        report_id=str(report_id),
        user_id=user_id
    )
    
    try:
        service = ReportService(db)
        await service.delete_report(report_id, user_id=UUID(user_id))
        
        logger.info(
            "Report deleted successfully",
            report_id=str(report_id)
        )
    except ReportNotFoundError:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete report",
            report_id=str(report_id),
            error=str(e),
            exc_info=True
        )
        raise


# Scheduled reports endpoints
@router.get("/scheduled", response_model=ScheduledReportListResponse)
async def list_scheduled_reports(
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Query(default="system", description="User ID for authorization"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Page size")
):
    """List scheduled reports"""
    logger.info("Listing scheduled reports", user_id=user_id)
    
    try:
        service = ReportService(db)
        return await service.list_scheduled_reports(
            user_id=UUID(user_id),
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.error("Failed to list scheduled reports", error=str(e), exc_info=True)
        raise


@router.post("/scheduled", response_model=ScheduledReportSchema, status_code=status.HTTP_201_CREATED)
async def create_scheduled_report(
    request: ScheduledReportCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Query(default="system", description="User ID for authorization")
):
    """Create a scheduled report"""
    logger.info("Creating scheduled report", name=request.name, user_id=user_id)
    
    try:
        service = ReportService(db)
        return await service.create_scheduled_report(request, user_id=UUID(user_id))
    except Exception as e:
        logger.error("Failed to create scheduled report", error=str(e), exc_info=True)
        raise


@router.put("/scheduled/{schedule_id}", response_model=ScheduledReportSchema)
async def update_scheduled_report(
    schedule_id: UUID,
    request: ScheduledReportUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Query(default="system", description="User ID for authorization")
):
    """Update a scheduled report"""
    logger.info("Updating scheduled report", schedule_id=str(schedule_id), user_id=user_id)
    
    try:
        service = ReportService(db)
        return await service.update_scheduled_report(schedule_id, request, user_id=UUID(user_id))
    except Exception as e:
        logger.error("Failed to update scheduled report", error=str(e), exc_info=True)
        raise


@router.delete("/scheduled/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheduled_report(
    schedule_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Query(default="system", description="User ID for authorization")
):
    """Delete a scheduled report"""
    logger.info("Deleting scheduled report", schedule_id=str(schedule_id), user_id=user_id)
    
    try:
        service = ReportService(db)
        await service.delete_scheduled_report(schedule_id, user_id=UUID(user_id))
    except Exception as e:
        logger.error("Failed to delete scheduled report", error=str(e), exc_info=True)
        raise
