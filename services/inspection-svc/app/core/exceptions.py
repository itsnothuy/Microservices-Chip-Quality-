"""Custom exceptions for inspection service"""

from typing import Any, Optional


class InspectionServiceError(Exception):
    """Base exception for all inspection service errors"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code or "INSPECTION_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(InspectionServiceError):
    """Data validation errors"""
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", details)


class InspectionNotFoundError(InspectionServiceError):
    """Inspection not found"""
    
    def __init__(self, inspection_id: str):
        super().__init__(
            f"Inspection not found: {inspection_id}",
            "INSPECTION_NOT_FOUND",
            {"inspection_id": inspection_id}
        )


class DuplicateInspectionError(InspectionServiceError):
    """Duplicate inspection detected"""
    
    def __init__(self, inspection_id: str, details: Optional[dict[str, Any]] = None):
        super().__init__(
            f"Duplicate inspection: {inspection_id}",
            "DUPLICATE_INSPECTION",
            details or {"inspection_id": inspection_id}
        )


class InspectionStatusError(InspectionServiceError):
    """Invalid inspection status transition"""
    
    def __init__(self, current_status: str, target_status: str):
        super().__init__(
            f"Invalid status transition from {current_status} to {target_status}",
            "INVALID_STATUS_TRANSITION",
            {"current_status": current_status, "target_status": target_status}
        )


class DefectNotFoundError(InspectionServiceError):
    """Defect not found"""
    
    def __init__(self, defect_id: str):
        super().__init__(
            f"Defect not found: {defect_id}",
            "DEFECT_NOT_FOUND",
            {"defect_id": defect_id}
        )


class MLInferenceError(InspectionServiceError):
    """ML inference operation failed"""
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, "ML_INFERENCE_ERROR", details)


class InferenceTimeoutError(MLInferenceError):
    """ML inference operation timed out"""
    
    def __init__(self, timeout: int):
        super().__init__(
            f"Inference operation timed out after {timeout} seconds",
            {"timeout": timeout}
        )


class ModelNotAvailableError(MLInferenceError):
    """ML model not available"""
    
    def __init__(self, model_name: str):
        super().__init__(
            f"Model not available: {model_name}",
            {"model_name": model_name}
        )


class QualityThresholdViolation(InspectionServiceError):
    """Quality threshold violation detected"""
    
    def __init__(self, score: float, threshold: float, details: Optional[dict[str, Any]] = None):
        super().__init__(
            f"Quality score {score:.4f} below threshold {threshold:.4f}",
            "QUALITY_THRESHOLD_VIOLATION",
            details or {"score": score, "threshold": threshold}
        )


class ResourceNotFoundError(InspectionServiceError):
    """Required resource not found"""
    
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            f"{resource_type} not found: {resource_id}",
            "RESOURCE_NOT_FOUND",
            {"resource_type": resource_type, "resource_id": resource_id}
        )


class ConcurrencyError(InspectionServiceError):
    """Concurrency conflict detected"""
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, "CONCURRENCY_ERROR", details)


class ConfigurationError(InspectionServiceError):
    """Configuration error"""
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, "CONFIGURATION_ERROR", details)


class ExternalServiceError(InspectionServiceError):
    """External service communication error"""
    
    def __init__(self, service: str, message: str, details: Optional[dict[str, Any]] = None):
        error_details = {"service": service}
        if details:
            error_details.update(details)
        super().__init__(
            f"External service error ({service}): {message}",
            "EXTERNAL_SERVICE_ERROR",
            error_details
        )
