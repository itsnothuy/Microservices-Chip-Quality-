"""
Unit tests for Report Service.
"""

import pytest
from datetime import date, datetime
from uuid import UUID, uuid4

from app.schemas.report import (
    DateRangeSchema,
    ReportCreateRequest,
    ReportFormatEnum
)
from app.models.report import ReportTypeEnum, ReportStatusEnum


class TestReportSchemas:
    """Test report Pydantic schemas"""
    
    def test_date_range_schema_valid(self):
        """Test valid date range"""
        date_range = DateRangeSchema(
            start_date=date(2025, 10, 1),
            end_date=date(2025, 10, 31)
        )
        assert date_range.start_date == date(2025, 10, 1)
        assert date_range.end_date == date(2025, 10, 31)
    
    def test_date_range_schema_invalid(self):
        """Test invalid date range (end before start)"""
        with pytest.raises(ValueError):
            DateRangeSchema(
                start_date=date(2025, 10, 31),
                end_date=date(2025, 10, 1)
            )
    
    def test_report_create_request_valid(self):
        """Test valid report creation request"""
        request = ReportCreateRequest(
            report_type=ReportTypeEnum.QUALITY_METRICS,
            title="Test Quality Report",
            date_range=DateRangeSchema(
                start_date=date(2025, 10, 1),
                end_date=date(2025, 10, 31)
            ),
            format=ReportFormatEnum.PDF
        )
        
        assert request.report_type == ReportTypeEnum.QUALITY_METRICS
        assert request.title == "Test Quality Report"
        assert request.format == ReportFormatEnum.PDF
        assert request.include_charts is True
        assert request.include_summary is True
    
    def test_report_create_request_with_filters(self):
        """Test report creation with filters"""
        request = ReportCreateRequest(
            report_type=ReportTypeEnum.DEFECT_ANALYSIS,
            title="Defect Analysis Report",
            date_range=DateRangeSchema(
                start_date=date(2025, 10, 1),
                end_date=date(2025, 10, 31)
            ),
            filters={
                "lot_ids": ["LOT-001", "LOT-002"],
                "severity": ["high", "critical"]
            },
            format=ReportFormatEnum.EXCEL
        )
        
        assert request.filters["lot_ids"] == ["LOT-001", "LOT-002"]
        assert request.filters["severity"] == ["high", "critical"]


class TestReportEnums:
    """Test report enumerations"""
    
    def test_report_type_enum(self):
        """Test report type enum values"""
        assert ReportTypeEnum.INSPECTION_SUMMARY == "inspection_summary"
        assert ReportTypeEnum.QUALITY_METRICS == "quality_metrics"
        assert ReportTypeEnum.DEFECT_ANALYSIS == "defect_analysis"
    
    def test_report_status_enum(self):
        """Test report status enum values"""
        assert ReportStatusEnum.QUEUED == "queued"
        assert ReportStatusEnum.GENERATING == "generating"
        assert ReportStatusEnum.COMPLETED == "completed"
        assert ReportStatusEnum.FAILED == "failed"
    
    def test_report_format_enum(self):
        """Test report format enum values"""
        assert ReportFormatEnum.PDF == "pdf"
        assert ReportFormatEnum.EXCEL == "excel"
        assert ReportFormatEnum.CSV == "csv"
        assert ReportFormatEnum.JSON == "json"


@pytest.mark.asyncio
class TestReportExceptions:
    """Test custom exceptions"""
    
    def test_report_not_found_error(self):
        """Test ReportNotFoundError"""
        from app.core.exceptions import ReportNotFoundError
        
        report_id = str(uuid4())
        error = ReportNotFoundError(report_id)
        
        assert error.error_code == "REPORT_NOT_FOUND"
        assert report_id in error.message
        assert error.details["report_id"] == report_id
    
    def test_validation_error(self):
        """Test ValidationError"""
        from app.core.exceptions import ValidationError
        
        error = ValidationError(
            "Invalid date range",
            details={"field": "date_range"}
        )
        
        assert error.error_code == "VALIDATION_ERROR"
        assert error.message == "Invalid date range"
        assert error.details["field"] == "date_range"
    
    def test_report_generation_error(self):
        """Test ReportGenerationError"""
        from app.core.exceptions import ReportGenerationError
        
        error = ReportGenerationError(
            "Failed to generate PDF",
            details={"format": "pdf", "error": "Template not found"}
        )
        
        assert error.error_code == "REPORT_GENERATION_ERROR"
        assert "PDF" in error.message
