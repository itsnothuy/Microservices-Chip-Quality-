"""
Unit tests for Analytics Service.
"""

import pytest
from datetime import date

from app.schemas.analytics import (
    QualityAnalyticsRequest,
    SPCAnalyticsRequest,
    ProcessCapabilityRequest,
    ParetoAnalyticsRequest,
    ChartType
)


class TestAnalyticsSchemas:
    """Test analytics Pydantic schemas"""
    
    def test_quality_analytics_request(self):
        """Test quality analytics request schema"""
        request = QualityAnalyticsRequest(
            start_date=date(2025, 10, 1),
            end_date=date(2025, 10, 31),
            lot_ids=["LOT-001", "LOT-002"]
        )
        
        assert request.start_date == date(2025, 10, 1)
        assert request.end_date == date(2025, 10, 31)
        assert request.lot_ids == ["LOT-001", "LOT-002"]
    
    def test_spc_analytics_request(self):
        """Test SPC analytics request schema"""
        request = SPCAnalyticsRequest(
            start_date=date(2025, 10, 1),
            end_date=date(2025, 10, 31),
            metric="defect_rate",
            chart_type=ChartType.XBAR_R,
            confidence_level=0.997
        )
        
        assert request.metric == "defect_rate"
        assert request.chart_type == ChartType.XBAR_R
        assert request.confidence_level == 0.997
    
    def test_process_capability_request(self):
        """Test process capability request schema"""
        request = ProcessCapabilityRequest(
            start_date=date(2025, 10, 1),
            end_date=date(2025, 10, 31),
            metric="dimension",
            lower_spec_limit=9.5,
            upper_spec_limit=10.5,
            target_value=10.0
        )
        
        assert request.metric == "dimension"
        assert request.lower_spec_limit == 9.5
        assert request.upper_spec_limit == 10.5
        assert request.target_value == 10.0
    
    def test_pareto_analytics_request(self):
        """Test Pareto analytics request schema"""
        request = ParetoAnalyticsRequest(
            start_date=date(2025, 10, 1),
            end_date=date(2025, 10, 31),
            category_field="defect_type",
            min_occurrences=5
        )
        
        assert request.category_field == "defect_type"
        assert request.min_occurrences == 5


class TestAnalyticsEnums:
    """Test analytics enumerations"""
    
    def test_chart_type_enum(self):
        """Test chart type enum values"""
        assert ChartType.XBAR_R == "xbar_r"
        assert ChartType.XBAR_S == "xbar_s"
        assert ChartType.X_MR == "x_mr"
        assert ChartType.P_CHART == "p_chart"
        assert ChartType.C_CHART == "c_chart"


class TestStatisticalCalculations:
    """Test statistical calculation helpers"""
    
    def test_process_capability_cp(self):
        """Test Cp calculation"""
        # Cp = (USL - LSL) / (6 * sigma)
        usl = 10.5
        lsl = 9.5
        sigma = 0.167
        
        cp = (usl - lsl) / (6 * sigma)
        
        assert abs(cp - 1.0) < 0.01
    
    def test_process_capability_cpk(self):
        """Test Cpk calculation"""
        # Cpk = min((USL - mean) / (3 * sigma), (mean - LSL) / (3 * sigma))
        usl = 10.5
        lsl = 9.5
        mean = 10.0
        sigma = 0.167
        
        cpu = (usl - mean) / (3 * sigma)
        cpl = (mean - lsl) / (3 * sigma)
        cpk = min(cpu, cpl)
        
        assert abs(cpk - 1.0) < 0.01
    
    def test_control_limits_xbar(self):
        """Test X-bar control limits calculation"""
        # UCL = mean + A2 * R_bar
        # LCL = mean - A2 * R_bar
        mean = 10.0
        r_bar = 0.5
        a2 = 0.577  # For sample size 5
        
        ucl = mean + a2 * r_bar
        lcl = mean - a2 * r_bar
        
        assert ucl > mean
        assert lcl < mean
        assert abs(ucl - lcl - 2 * a2 * r_bar) < 0.01
