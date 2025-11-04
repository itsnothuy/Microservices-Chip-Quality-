"""
Pydantic schemas for report requests and responses.
"""

from datetime import datetime, date
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, validator

from app.models.report import ReportTypeEnum, ReportStatusEnum, ReportFormatEnum


# Request schemas
class DateRangeSchema(BaseModel):
    """Date range for reports"""
    start_date: date = Field(..., description="Start date for the report")
    end_date: date = Field(..., description="End date for the report")
    
    @validator('end_date')
    def validate_date_range(cls, v: date, values: Dict[str, Any]) -> date:
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v


class ReportCreateRequest(BaseModel):
    """Request to create a new report"""
    report_type: ReportTypeEnum = Field(..., description="Type of report to generate")
    title: str = Field(..., min_length=1, max_length=200, description="Report title")
    description: Optional[str] = Field(None, description="Report description")
    
    # Report parameters
    date_range: DateRangeSchema = Field(..., description="Date range for the report")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Additional filters")
    format: ReportFormatEnum = Field(default=ReportFormatEnum.PDF, description="Output format")
    
    # Options
    include_charts: bool = Field(default=True, description="Include charts and visualizations")
    include_summary: bool = Field(default=True, description="Include executive summary")
    
    class Config:
        use_enum_values = True


class ReportRegenerateRequest(BaseModel):
    """Request to regenerate an existing report"""
    format: Optional[ReportFormatEnum] = Field(None, description="New output format (optional)")
    
    class Config:
        use_enum_values = True


# Response schemas
class ReportResponse(BaseModel):
    """Report response model"""
    id: UUID
    report_type: ReportTypeEnum
    title: str
    description: Optional[str]
    
    # Report parameters
    filters: Dict[str, Any]
    data_range: Dict[str, Any]
    
    # Status
    status: ReportStatusEnum
    format: ReportFormatEnum
    
    # File information
    file_path: Optional[str]
    file_size_bytes: Optional[int]
    download_url: Optional[str] = None
    
    # Access control
    generated_by: UUID
    access_permissions: Dict[str, Any]
    
    # Metadata
    metadata: Dict[str, Any]
    error_message: Optional[str]
    
    # Timestamps
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    expires_at: Optional[datetime]
    
    class Config:
        from_attributes = True
        use_enum_values = True


class ReportListResponse(BaseModel):
    """List of reports with pagination"""
    reports: List[ReportResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class ReportTemplateSchema(BaseModel):
    """Report template information"""
    id: UUID
    name: str
    display_name: str
    description: Optional[str]
    report_type: ReportTypeEnum
    supported_formats: List[str]
    parameters: Dict[str, Any]
    default_filters: Dict[str, Any]
    version: int
    is_active: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        use_enum_values = True


class ReportTemplateListResponse(BaseModel):
    """List of report templates"""
    templates: List[ReportTemplateSchema]
    total: int


class ScheduledReportSchema(BaseModel):
    """Scheduled report configuration"""
    id: UUID
    name: str
    description: Optional[str]
    report_type: ReportTypeEnum
    format: ReportFormatEnum
    schedule_pattern: str
    timezone: str
    filters: Dict[str, Any]
    parameters: Dict[str, Any]
    recipients: List[str]
    is_active: str
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        use_enum_values = True


class ScheduledReportCreateRequest(BaseModel):
    """Request to create a scheduled report"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    report_type: ReportTypeEnum
    format: ReportFormatEnum = ReportFormatEnum.PDF
    schedule_pattern: str = Field(..., description="Cron-like schedule pattern")
    timezone: str = Field(default="UTC", description="Timezone for schedule")
    filters: Dict[str, Any] = Field(default_factory=dict)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    recipients: List[str] = Field(default_factory=list, description="Email recipients")
    
    class Config:
        use_enum_values = True


class ScheduledReportUpdateRequest(BaseModel):
    """Request to update a scheduled report"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    schedule_pattern: Optional[str] = None
    timezone: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None
    recipients: Optional[List[str]] = None
    is_active: Optional[str] = None
    
    class Config:
        use_enum_values = True


class ScheduledReportListResponse(BaseModel):
    """List of scheduled reports"""
    scheduled_reports: List[ScheduledReportSchema]
    total: int
    page: int
    page_size: int
