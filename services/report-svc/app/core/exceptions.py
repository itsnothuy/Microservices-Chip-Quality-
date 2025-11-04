"""
Custom exceptions for Report Service.
"""

from typing import Any, Dict, Optional


class ReportServiceError(Exception):
    """Base exception for all report service errors"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "REPORT_SERVICE_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ReportServiceError):
    """Data validation errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details
        )


class ReportNotFoundError(ReportServiceError):
    """Report not found"""
    
    def __init__(self, report_id: str):
        super().__init__(
            message=f"Report not found: {report_id}",
            error_code="REPORT_NOT_FOUND",
            details={"report_id": report_id}
        )


class TemplateNotFoundError(ReportServiceError):
    """Template not found"""
    
    def __init__(self, template_name: str):
        super().__init__(
            message=f"Report template not found: {template_name}",
            error_code="TEMPLATE_NOT_FOUND",
            details={"template_name": template_name}
        )


class ReportGenerationError(ReportServiceError):
    """Report generation failed"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="REPORT_GENERATION_ERROR",
            details=details
        )


class AnalyticsCalculationError(ReportServiceError):
    """Analytics calculation failed"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="ANALYTICS_CALCULATION_ERROR",
            details=details
        )


class ExportError(ReportServiceError):
    """Report export failed"""
    
    def __init__(self, message: str, format: str, details: Optional[Dict[str, Any]] = None):
        export_details = {"format": format}
        if details:
            export_details.update(details)
        super().__init__(
            message=message,
            error_code="EXPORT_ERROR",
            details=export_details
        )


class DataTooLargeError(ReportServiceError):
    """Dataset exceeds maximum size"""
    
    def __init__(self, record_count: int, max_records: int):
        super().__init__(
            message=f"Dataset too large: {record_count} records exceeds maximum of {max_records}",
            error_code="DATA_TOO_LARGE",
            details={"record_count": record_count, "max_records": max_records}
        )


class ConcurrentLimitError(ReportServiceError):
    """Too many concurrent report generation requests"""
    
    def __init__(self, current_count: int, max_concurrent: int):
        super().__init__(
            message=f"Maximum concurrent reports ({max_concurrent}) exceeded",
            error_code="CONCURRENT_LIMIT_ERROR",
            details={"current_count": current_count, "max_concurrent": max_concurrent}
        )


class StorageError(ReportServiceError):
    """Report storage operation failed"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="STORAGE_ERROR",
            details=details
        )


class DatabaseError(ReportServiceError):
    """Database operation failed"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details
        )
