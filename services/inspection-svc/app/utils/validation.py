"""
Business rule validation utilities.

Validation functions for inspection business rules and constraints.
"""

import re
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional


class ValidationResult:
    """Result of validation check"""
    
    def __init__(self, is_valid: bool, errors: Optional[List[str]] = None):
        self.is_valid = is_valid
        self.errors = errors or []
    
    def add_error(self, error: str) -> None:
        """Add validation error"""
        self.is_valid = False
        self.errors.append(error)


def validate_chip_id(chip_id: str) -> ValidationResult:
    """
    Validate chip ID format.
    
    Rules:
    - Must be alphanumeric with hyphens
    - Length between 3 and 100 characters
    - Must start with letter or number
    
    Args:
        chip_id: Chip identifier
        
    Returns:
        ValidationResult
    """
    result = ValidationResult(True)
    
    if not chip_id or not chip_id.strip():
        result.add_error("Chip ID cannot be empty")
        return result
    
    chip_id = chip_id.strip()
    
    if not 3 <= len(chip_id) <= 100:
        result.add_error("Chip ID must be between 3 and 100 characters")
    
    if not re.match(r'^[A-Za-z0-9][A-Za-z0-9\-_]*$', chip_id):
        result.add_error("Chip ID must be alphanumeric with hyphens or underscores")
    
    return result


def validate_priority(priority: int) -> ValidationResult:
    """
    Validate priority value.
    
    Rules:
    - Must be integer between 1 and 10
    
    Args:
        priority: Priority value
        
    Returns:
        ValidationResult
    """
    result = ValidationResult(True)
    
    if not isinstance(priority, int):
        result.add_error("Priority must be an integer")
        return result
    
    if not 1 <= priority <= 10:
        result.add_error("Priority must be between 1 and 10")
    
    return result


def validate_quality_score(score: Decimal) -> ValidationResult:
    """
    Validate quality score value.
    
    Rules:
    - Must be between 0.0 and 1.0
    
    Args:
        score: Quality score
        
    Returns:
        ValidationResult
    """
    result = ValidationResult(True)
    
    if not isinstance(score, (Decimal, float, int)):
        result.add_error("Quality score must be numeric")
        return result
    
    score = Decimal(str(score))
    
    if not 0 <= score <= 1:
        result.add_error("Quality score must be between 0.0 and 1.0")
    
    return result


def validate_confidence_score(confidence: Decimal) -> ValidationResult:
    """
    Validate ML confidence score.
    
    Rules:
    - Must be between 0.0 and 1.0
    
    Args:
        confidence: Confidence score
        
    Returns:
        ValidationResult
    """
    result = ValidationResult(True)
    
    if not isinstance(confidence, (Decimal, float, int)):
        result.add_error("Confidence score must be numeric")
        return result
    
    confidence = Decimal(str(confidence))
    
    if not 0 <= confidence <= 1:
        result.add_error("Confidence score must be between 0.0 and 1.0")
    
    return result


def validate_defect_location(location: Dict[str, Any]) -> ValidationResult:
    """
    Validate defect location data.
    
    Rules:
    - Must contain x, y, width, height fields
    - All values must be non-negative numbers
    
    Args:
        location: Location dictionary
        
    Returns:
        ValidationResult
    """
    result = ValidationResult(True)
    
    required_fields = ['x', 'y', 'width', 'height']
    
    for field in required_fields:
        if field not in location:
            result.add_error(f"Location must contain '{field}' field")
    
    if not result.is_valid:
        return result
    
    # Validate numeric values
    for field in required_fields:
        value = location[field]
        if not isinstance(value, (int, float)):
            result.add_error(f"Location '{field}' must be numeric")
        elif value < 0:
            result.add_error(f"Location '{field}' must be non-negative")
    
    # Validate dimensions
    if result.is_valid:
        if location['width'] <= 0:
            result.add_error("Location width must be positive")
        if location['height'] <= 0:
            result.add_error("Location height must be positive")
    
    return result


def validate_metadata(metadata: Dict[str, Any], max_size: int = 10000) -> ValidationResult:
    """
    Validate metadata dictionary.
    
    Rules:
    - Must be a dictionary
    - Size must not exceed max_size bytes when serialized
    
    Args:
        metadata: Metadata dictionary
        max_size: Maximum size in bytes
        
    Returns:
        ValidationResult
    """
    result = ValidationResult(True)
    
    if not isinstance(metadata, dict):
        result.add_error("Metadata must be a dictionary")
        return result
    
    # Check size
    import json
    try:
        serialized = json.dumps(metadata)
        if len(serialized) > max_size:
            result.add_error(f"Metadata size exceeds {max_size} bytes")
    except (TypeError, ValueError) as e:
        result.add_error(f"Metadata is not JSON serializable: {str(e)}")
    
    return result


def validate_inspection_request(
    chip_id: str,
    priority: int,
    metadata: Optional[Dict[str, Any]] = None
) -> ValidationResult:
    """
    Validate complete inspection creation request.
    
    Args:
        chip_id: Chip identifier
        priority: Priority value
        metadata: Optional metadata
        
    Returns:
        ValidationResult
    """
    result = ValidationResult(True)
    
    # Validate chip ID
    chip_result = validate_chip_id(chip_id)
    if not chip_result.is_valid:
        result.errors.extend(chip_result.errors)
        result.is_valid = False
    
    # Validate priority
    priority_result = validate_priority(priority)
    if not priority_result.is_valid:
        result.errors.extend(priority_result.errors)
        result.is_valid = False
    
    # Validate metadata if provided
    if metadata:
        metadata_result = validate_metadata(metadata)
        if not metadata_result.is_valid:
            result.errors.extend(metadata_result.errors)
            result.is_valid = False
    
    return result


def validate_timestamp_range(
    start_time: datetime,
    end_time: datetime,
    max_duration_hours: int = 24
) -> ValidationResult:
    """
    Validate timestamp range.
    
    Rules:
    - End time must be after start time
    - Duration must not exceed max_duration_hours
    
    Args:
        start_time: Start timestamp
        end_time: End timestamp
        max_duration_hours: Maximum allowed duration in hours
        
    Returns:
        ValidationResult
    """
    result = ValidationResult(True)
    
    if end_time <= start_time:
        result.add_error("End time must be after start time")
        return result
    
    duration = end_time - start_time
    max_duration = max_duration_hours * 3600  # Convert to seconds
    
    if duration.total_seconds() > max_duration:
        result.add_error(f"Duration exceeds maximum of {max_duration_hours} hours")
    
    return result
