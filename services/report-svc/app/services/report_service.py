"""
Core report generation and management service.
"""

from datetime import datetime, timedelta
from typing import Optional, AsyncIterator
from uuid import UUID
import structlog

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ReportNotFoundError, ValidationError
from app.models.report import Report, ReportStatusEnum, ScheduledReport
from app.schemas.report import (
    ReportCreateRequest,
    ReportResponse,
    ReportListResponse,
    ReportFormatEnum,
    ScheduledReportSchema,
    ScheduledReportCreateRequest,
    ScheduledReportUpdateRequest,
    ScheduledReportListResponse
)

logger = structlog.get_logger()


class ReportService:
    """Service for report generation and management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_report(
        self,
        request: ReportCreateRequest,
        user_id: UUID
    ) -> ReportResponse:
        """Create a new report generation request"""
        logger.info(
            "Creating report",
            report_type=request.report_type,
            format=request.format
        )
        
        # Create report record
        report = Report(
            report_type=request.report_type,
            title=request.title,
            description=request.description,
            filters=request.filters,
            data_range={
                "start_date": request.date_range.start_date.isoformat(),
                "end_date": request.date_range.end_date.isoformat()
            },
            status=ReportStatusEnum.QUEUED,
            format=request.format,
            generated_by=user_id,
            access_permissions={},
            report_metadata={
                "include_charts": request.include_charts,
                "include_summary": request.include_summary
            },
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        
        logger.info(
            "Report created",
            report_id=str(report.id),
            status=report.status
        )
        
        return ReportResponse.model_validate(report)
    
    async def get_report(
        self,
        report_id: UUID,
        user_id: UUID
    ) -> Optional[ReportResponse]:
        """Get report by ID"""
        result = await self.db.execute(
            select(Report).where(Report.id == report_id)
        )
        report = result.scalar_one_or_none()
        
        if not report:
            return None
        
        return ReportResponse.model_validate(report)
    
    async def list_reports(
        self,
        user_id: UUID,
        report_type: Optional[str] = None,
        status_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> ReportListResponse:
        """List reports with pagination"""
        query = select(Report).where(Report.generated_by == user_id)
        
        if report_type:
            query = query.where(Report.report_type == report_type)
        
        if status_filter:
            query = query.where(Report.status == status_filter)
        
        query = query.order_by(Report.created_at.desc())
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size + 1)
        
        result = await self.db.execute(query)
        reports = result.scalars().all()
        
        has_more = len(reports) > page_size
        if has_more:
            reports = reports[:page_size]
        
        report_responses = [ReportResponse.model_validate(r) for r in reports]
        
        # Get total count
        count_result = await self.db.execute(
            select(Report).where(Report.generated_by == user_id)
        )
        total = len(count_result.scalars().all())
        
        return ReportListResponse(
            reports=report_responses,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more
        )
    
    async def download_report(
        self,
        report_id: UUID,
        user_id: UUID
    ) -> tuple[AsyncIterator[bytes], str, str]:
        """Download report file"""
        result = await self.db.execute(
            select(Report).where(Report.id == report_id)
        )
        report = result.scalar_one_or_none()
        
        if not report:
            raise ReportNotFoundError(str(report_id))
        
        if report.status != ReportStatusEnum.COMPLETED:
            raise ValidationError(
                "Report is not completed yet",
                details={"status": report.status}
            )
        
        # For now, return a mock file stream
        # In production, this would retrieve from MinIO
        async def file_stream() -> AsyncIterator[bytes]:
            yield b"Mock report content"
        
        filename = f"report_{report_id}.{report.format}"
        media_type_map = {
            ReportFormatEnum.PDF: "application/pdf",
            ReportFormatEnum.EXCEL: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ReportFormatEnum.CSV: "text/csv",
            ReportFormatEnum.JSON: "application/json",
            ReportFormatEnum.HTML: "text/html"
        }
        media_type = media_type_map.get(report.format, "application/octet-stream")
        
        return file_stream(), filename, media_type
    
    async def regenerate_report(
        self,
        report_id: UUID,
        new_format: Optional[ReportFormatEnum],
        user_id: UUID
    ) -> ReportResponse:
        """Regenerate an existing report"""
        result = await self.db.execute(
            select(Report).where(Report.id == report_id)
        )
        report = result.scalar_one_or_none()
        
        if not report:
            raise ReportNotFoundError(str(report_id))
        
        # Update format if provided
        if new_format:
            report.format = new_format
        
        # Reset status to regenerate
        report.status = ReportStatusEnum.QUEUED
        report.started_at = None
        report.completed_at = None
        report.file_path = None
        report.error_message = None
        
        await self.db.commit()
        await self.db.refresh(report)
        
        return ReportResponse.model_validate(report)
    
    async def delete_report(
        self,
        report_id: UUID,
        user_id: UUID
    ) -> None:
        """Delete a report"""
        result = await self.db.execute(
            select(Report).where(Report.id == report_id)
        )
        report = result.scalar_one_or_none()
        
        if not report:
            raise ReportNotFoundError(str(report_id))
        
        await self.db.delete(report)
        await self.db.commit()
    
    async def list_scheduled_reports(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20
    ) -> ScheduledReportListResponse:
        """List scheduled reports"""
        query = select(ScheduledReport).where(ScheduledReport.created_by == user_id)
        query = query.order_by(ScheduledReport.created_at.desc())
        
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        schedules = result.scalars().all()
        
        schedule_responses = [ScheduledReportSchema.model_validate(s) for s in schedules]
        
        return ScheduledReportListResponse(
            scheduled_reports=schedule_responses,
            total=len(schedule_responses),
            page=page,
            page_size=page_size
        )
    
    async def create_scheduled_report(
        self,
        request: ScheduledReportCreateRequest,
        user_id: UUID
    ) -> ScheduledReportSchema:
        """Create a scheduled report"""
        schedule = ScheduledReport(
            name=request.name,
            description=request.description,
            report_type=request.report_type,
            format=request.format,
            schedule_pattern=request.schedule_pattern,
            timezone=request.timezone,
            filters=request.filters,
            parameters=request.parameters,
            recipients=request.recipients,
            is_active="true",
            created_by=user_id
        )
        
        self.db.add(schedule)
        await self.db.commit()
        await self.db.refresh(schedule)
        
        return ScheduledReportSchema.model_validate(schedule)
    
    async def update_scheduled_report(
        self,
        schedule_id: UUID,
        request: ScheduledReportUpdateRequest,
        user_id: UUID
    ) -> ScheduledReportSchema:
        """Update a scheduled report"""
        result = await self.db.execute(
            select(ScheduledReport).where(ScheduledReport.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        
        if not schedule:
            raise ReportNotFoundError(str(schedule_id))
        
        # Update fields
        if request.name is not None:
            schedule.name = request.name
        if request.description is not None:
            schedule.description = request.description
        if request.schedule_pattern is not None:
            schedule.schedule_pattern = request.schedule_pattern
        if request.timezone is not None:
            schedule.timezone = request.timezone
        if request.filters is not None:
            schedule.filters = request.filters
        if request.parameters is not None:
            schedule.parameters = request.parameters
        if request.recipients is not None:
            schedule.recipients = request.recipients
        if request.is_active is not None:
            schedule.is_active = request.is_active
        
        await self.db.commit()
        await self.db.refresh(schedule)
        
        return ScheduledReportSchema.model_validate(schedule)
    
    async def delete_scheduled_report(
        self,
        schedule_id: UUID,
        user_id: UUID
    ) -> None:
        """Delete a scheduled report"""
        result = await self.db.execute(
            select(ScheduledReport).where(ScheduledReport.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        
        if not schedule:
            raise ReportNotFoundError(str(schedule_id))
        
        await self.db.delete(schedule)
        await self.db.commit()
