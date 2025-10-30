"""Unit tests for validation utilities"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from app.utils.validation import (
    validate_chip_id,
    validate_priority,
    validate_quality_score,
    validate_confidence_score,
    validate_defect_location,
    validate_metadata,
    validate_inspection_request,
    validate_timestamp_range
)


class TestValidation:
    """Test cases for validation utilities"""
    
    def test_validate_chip_id_valid(self):
        """Test valid chip ID"""
        result = validate_chip_id("CHIP-001")
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_chip_id_empty(self):
        """Test empty chip ID"""
        result = validate_chip_id("")
        assert result.is_valid is False
        assert "cannot be empty" in result.errors[0]
    
    def test_validate_chip_id_too_short(self):
        """Test chip ID too short"""
        result = validate_chip_id("AB")
        assert result.is_valid is False
        assert "between 3 and 100" in result.errors[0]
    
    def test_validate_chip_id_invalid_chars(self):
        """Test chip ID with invalid characters"""
        result = validate_chip_id("CHIP@001")
        assert result.is_valid is False
        assert "alphanumeric" in result.errors[0]
    
    def test_validate_priority_valid(self):
        """Test valid priority"""
        result = validate_priority(5)
        assert result.is_valid is True
    
    def test_validate_priority_too_low(self):
        """Test priority too low"""
        result = validate_priority(0)
        assert result.is_valid is False
    
    def test_validate_priority_too_high(self):
        """Test priority too high"""
        result = validate_priority(11)
        assert result.is_valid is False
    
    def test_validate_priority_not_integer(self):
        """Test priority not integer"""
        result = validate_priority(5.5)
        assert result.is_valid is False
    
    def test_validate_quality_score_valid(self):
        """Test valid quality score"""
        result = validate_quality_score(Decimal("0.95"))
        assert result.is_valid is True
    
    def test_validate_quality_score_too_high(self):
        """Test quality score too high"""
        result = validate_quality_score(Decimal("1.5"))
        assert result.is_valid is False
    
    def test_validate_quality_score_negative(self):
        """Test negative quality score"""
        result = validate_quality_score(Decimal("-0.1"))
        assert result.is_valid is False
    
    def test_validate_confidence_score_valid(self):
        """Test valid confidence score"""
        result = validate_confidence_score(Decimal("0.85"))
        assert result.is_valid is True
    
    def test_validate_defect_location_valid(self):
        """Test valid defect location"""
        location = {
            "x": 100,
            "y": 200,
            "width": 50,
            "height": 30
        }
        result = validate_defect_location(location)
        assert result.is_valid is True
    
    def test_validate_defect_location_missing_field(self):
        """Test defect location with missing field"""
        location = {"x": 100, "y": 200}
        result = validate_defect_location(location)
        assert result.is_valid is False
        assert "must contain 'width'" in result.errors[0] or "must contain 'height'" in result.errors[0]
    
    def test_validate_defect_location_negative_value(self):
        """Test defect location with negative value"""
        location = {
            "x": -10,
            "y": 200,
            "width": 50,
            "height": 30
        }
        result = validate_defect_location(location)
        assert result.is_valid is False
    
    def test_validate_defect_location_zero_width(self):
        """Test defect location with zero width"""
        location = {
            "x": 100,
            "y": 200,
            "width": 0,
            "height": 30
        }
        result = validate_defect_location(location)
        assert result.is_valid is False
    
    def test_validate_metadata_valid(self):
        """Test valid metadata"""
        metadata = {"key": "value", "number": 42}
        result = validate_metadata(metadata)
        assert result.is_valid is True
    
    def test_validate_metadata_not_dict(self):
        """Test metadata not a dictionary"""
        result = validate_metadata("not a dict")
        assert result.is_valid is False
    
    def test_validate_metadata_too_large(self):
        """Test metadata too large"""
        metadata = {"large_data": "x" * 20000}
        result = validate_metadata(metadata, max_size=10000)
        assert result.is_valid is False
    
    def test_validate_inspection_request_valid(self):
        """Test valid inspection request"""
        result = validate_inspection_request(
            chip_id="CHIP-001",
            priority=5,
            metadata={"test": "data"}
        )
        assert result.is_valid is True
    
    def test_validate_inspection_request_invalid_chip_id(self):
        """Test inspection request with invalid chip ID"""
        result = validate_inspection_request(
            chip_id="X",  # Too short
            priority=5
        )
        assert result.is_valid is False
    
    def test_validate_inspection_request_invalid_priority(self):
        """Test inspection request with invalid priority"""
        result = validate_inspection_request(
            chip_id="CHIP-001",
            priority=15  # Too high
        )
        assert result.is_valid is False
    
    def test_validate_timestamp_range_valid(self):
        """Test valid timestamp range"""
        start = datetime.utcnow()
        end = start + timedelta(hours=2)
        
        result = validate_timestamp_range(start, end)
        assert result.is_valid is True
    
    def test_validate_timestamp_range_end_before_start(self):
        """Test timestamp range with end before start"""
        start = datetime.utcnow()
        end = start - timedelta(hours=1)
        
        result = validate_timestamp_range(start, end)
        assert result.is_valid is False
    
    def test_validate_timestamp_range_too_long(self):
        """Test timestamp range too long"""
        start = datetime.utcnow()
        end = start + timedelta(hours=48)
        
        result = validate_timestamp_range(start, end, max_duration_hours=24)
        assert result.is_valid is False
