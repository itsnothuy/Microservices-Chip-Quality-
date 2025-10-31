"""Unit tests for quality service"""

import pytest
from decimal import Decimal
from datetime import datetime
import uuid
from unittest.mock import AsyncMock, MagicMock

from services.shared.database.enums import DefectSeverityEnum, InspectionTypeEnum
from app.services.quality_service import (
    QualityService,
    QualityMetrics,
    QualityThresholds
)


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    return AsyncMock()


@pytest.fixture
def quality_service(mock_db_session):
    """Create quality service with mocked session"""
    return QualityService(mock_db_session)


@pytest.fixture
def mock_inspection():
    """Mock inspection for testing"""
    inspection = MagicMock()
    inspection.id = uuid.uuid4()
    inspection.inspection_id = "INS-VIS-CHIP-001-20251030"
    inspection.inspection_type = InspectionTypeEnum.VISUAL
    inspection.defects = []
    return inspection


@pytest.fixture
def mock_defects():
    """Mock defects for testing"""
    defects = []
    
    # Create defects with different severities
    for i, severity in enumerate([
        DefectSeverityEnum.CRITICAL,
        DefectSeverityEnum.HIGH,
        DefectSeverityEnum.MEDIUM,
        DefectSeverityEnum.LOW
    ]):
        defect = MagicMock()
        defect.id = uuid.uuid4()
        defect.severity = severity
        defect.confidence_score = Decimal("0.90")
        defect.defect_type = "scratch"
        defects.append(defect)
    
    return defects


class TestQualityService:
    """Test cases for QualityService"""
    
    @pytest.mark.asyncio
    async def test_calculate_quality_metrics_no_defects(
        self,
        quality_service,
        mock_inspection
    ):
        """Test quality metrics calculation with no defects"""
        metrics = await quality_service.calculate_quality_metrics(mock_inspection)
        
        assert metrics.overall_score == Decimal("1.0")
        assert metrics.defect_count == 0
        assert metrics.critical_defect_count == 0
        assert metrics.pass_rate == Decimal("1.0")
    
    @pytest.mark.asyncio
    async def test_calculate_quality_metrics_with_defects(
        self,
        quality_service,
        mock_inspection,
        mock_defects
    ):
        """Test quality metrics calculation with defects"""
        mock_inspection.defects = mock_defects
        
        metrics = await quality_service.calculate_quality_metrics(mock_inspection)
        
        assert metrics.overall_score < Decimal("1.0")
        assert metrics.defect_count == len(mock_defects)
        assert metrics.critical_defect_count == 1  # One critical defect
        assert metrics.pass_rate == Decimal("0.0")  # Should fail due to critical defect
    
    def test_count_defects_by_severity(self, quality_service, mock_defects):
        """Test defect counting by severity"""
        counts = quality_service._count_defects_by_severity(mock_defects)
        
        assert counts[DefectSeverityEnum.CRITICAL] == 1
        assert counts[DefectSeverityEnum.HIGH] == 1
        assert counts[DefectSeverityEnum.MEDIUM] == 1
        assert counts[DefectSeverityEnum.LOW] == 1
    
    def test_calculate_overall_score_perfect(self, quality_service):
        """Test overall score calculation with no defects"""
        score = quality_service._calculate_overall_score(
            defects=[],
            severity_counts={},
            defect_density=Decimal("0.0")
        )
        
        assert score == Decimal("1.0")
    
    def test_calculate_overall_score_with_critical_defect(self, quality_service):
        """Test overall score with critical defect"""
        mock_defect = MagicMock()
        mock_defect.severity = DefectSeverityEnum.CRITICAL
        
        severity_counts = {DefectSeverityEnum.CRITICAL: 1}
        
        score = quality_service._calculate_overall_score(
            defects=[mock_defect],
            severity_counts=severity_counts,
            defect_density=Decimal("0.01")
        )
        
        # Score should be significantly reduced
        assert score < Decimal("0.5")
    
    def test_determine_pass_fail_critical_defect(self, quality_service):
        """Test pass/fail determination with critical defect"""
        severity_counts = {DefectSeverityEnum.CRITICAL: 1}
        
        passed = quality_service._determine_pass_fail(
            Decimal("0.9"),
            severity_counts
        )
        
        assert passed is False
    
    def test_determine_pass_fail_low_score(self, quality_service):
        """Test pass/fail determination with low score"""
        severity_counts = {DefectSeverityEnum.LOW: 1}
        
        passed = quality_service._determine_pass_fail(
            Decimal("0.5"),  # Below threshold
            severity_counts
        )
        
        assert passed is False
    
    def test_determine_pass_fail_passing(self, quality_service):
        """Test pass/fail determination with passing score"""
        severity_counts = {DefectSeverityEnum.LOW: 1}
        
        passed = quality_service._determine_pass_fail(
            Decimal("0.85"),  # Above threshold
            severity_counts
        )
        
        assert passed is True
    
    def test_quality_thresholds_defaults(self):
        """Test default quality thresholds"""
        thresholds = QualityThresholds()
        
        assert thresholds.critical_threshold == Decimal("0.95")
        assert thresholds.high_threshold == Decimal("0.85")
        assert thresholds.medium_threshold == Decimal("0.75")
        assert thresholds.max_critical_defects == 0
    
    def test_quality_metrics_to_dict(self):
        """Test QualityMetrics conversion to dictionary"""
        metrics = QualityMetrics(
            overall_score=Decimal("0.95"),
            defect_count=2,
            critical_defect_count=0,
            defect_density=Decimal("0.02"),
            pass_rate=Decimal("1.0"),
            confidence=Decimal("0.90"),
            details={"test": "data"}
        )
        
        result = metrics.to_dict()
        
        assert result["overall_score"] == 0.95
        assert result["defect_count"] == 2
        assert result["critical_defect_count"] == 0
        assert "details" in result
