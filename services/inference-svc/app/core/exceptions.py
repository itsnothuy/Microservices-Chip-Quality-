"""
ML-specific exceptions for inference service.

Custom exception hierarchy for ML inference operations.
"""

from typing import Any, Optional


class InferenceError(Exception):
    """Base exception for inference errors."""
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class TritonConnectionError(InferenceError):
    """Raised when connection to Triton server fails."""
    
    def __init__(self, url: str, original_error: Optional[Exception] = None):
        message = f"Failed to connect to Triton server at {url}"
        details = {"triton_url": url}
        if original_error:
            details["original_error"] = str(original_error)
        super().__init__(message, details)


class ModelNotFoundError(InferenceError):
    """Raised when requested model is not available."""
    
    def __init__(self, model_name: str, version: Optional[str] = None):
        message = f"Model '{model_name}' not found"
        if version:
            message += f" (version: {version})"
        details = {"model_name": model_name}
        if version:
            details["version"] = version
        super().__init__(message, details)


class ModelNotReadyError(InferenceError):
    """Raised when model is not ready for inference."""
    
    def __init__(self, model_name: str, status: str):
        message = f"Model '{model_name}' is not ready (status: {status})"
        details = {"model_name": model_name, "status": status}
        super().__init__(message, details)


class InferenceTimeoutError(InferenceError):
    """Raised when inference request times out."""
    
    def __init__(self, timeout_seconds: int, model_name: Optional[str] = None):
        message = f"Inference request timed out after {timeout_seconds} seconds"
        if model_name:
            message += f" for model '{model_name}'"
        details = {"timeout_seconds": timeout_seconds}
        if model_name:
            details["model_name"] = model_name
        super().__init__(message, details)


class InvalidImageError(InferenceError):
    """Raised when image data is invalid or corrupted."""
    
    def __init__(self, reason: str):
        message = f"Invalid image data: {reason}"
        details = {"reason": reason}
        super().__init__(message, details)


class ImagePreprocessingError(InferenceError):
    """Raised when image preprocessing fails."""
    
    def __init__(self, reason: str, step: Optional[str] = None):
        message = f"Image preprocessing failed: {reason}"
        if step:
            message += f" (step: {step})"
        details = {"reason": reason}
        if step:
            details["preprocessing_step"] = step
        super().__init__(message, details)


class ModelInferenceError(InferenceError):
    """Raised when model inference execution fails."""
    
    def __init__(self, model_name: str, reason: str):
        message = f"Inference failed for model '{model_name}': {reason}"
        details = {"model_name": model_name, "reason": reason}
        super().__init__(message, details)


class BatchSizeExceededError(InferenceError):
    """Raised when batch size exceeds maximum allowed."""
    
    def __init__(self, requested: int, maximum: int):
        message = f"Batch size {requested} exceeds maximum allowed {maximum}"
        details = {"requested_size": requested, "maximum_size": maximum}
        super().__init__(message, details)


class ModelVersionConflictError(InferenceError):
    """Raised when there's a version conflict in model deployment."""
    
    def __init__(self, model_name: str, existing_version: str, new_version: str):
        message = f"Version conflict for model '{model_name}': existing {existing_version}, new {new_version}"
        details = {
            "model_name": model_name,
            "existing_version": existing_version,
            "new_version": new_version
        }
        super().__init__(message, details)


class InsufficientConfidenceError(InferenceError):
    """Raised when prediction confidence is below threshold."""
    
    def __init__(self, confidence: float, threshold: float):
        message = f"Prediction confidence {confidence:.3f} below threshold {threshold:.3f}"
        details = {"confidence": confidence, "threshold": threshold}
        super().__init__(message, details)
