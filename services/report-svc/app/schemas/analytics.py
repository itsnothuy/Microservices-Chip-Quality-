"""
Pydantic schemas for analytics requests and responses.
"""

from datetime import date
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class MetricType(str, Enum):
    """Type of quality metric"""
    DEFECT_RATE = "defect_rate"
    FIRST_PASS_YIELD = "first_pass_yield"
    PROCESS_CAPABILITY = "process_capability"
    OEE = "oee"
    THROUGHPUT = "throughput"
    CYCLE_TIME = "cycle_time"


class ChartType(str, Enum):
    """Type of control chart"""
    XBAR_R = "xbar_r"
    XBAR_S = "xbar_s"
    X_MR = "x_mr"
    P_CHART = "p_chart"
    NP_CHART = "np_chart"
    C_CHART = "c_chart"
    U_CHART = "u_chart"


# Analytics request schemas
class QualityAnalyticsRequest(BaseModel):
    """Request for quality analytics"""
    start_date: date
    end_date: date
    lot_ids: Optional[List[str]] = Field(None, description="Filter by specific lots")
    part_types: Optional[List[str]] = Field(None, description="Filter by part types")
    inspection_types: Optional[List[str]] = Field(None, description="Filter by inspection types")
    station_ids: Optional[List[str]] = Field(None, description="Filter by stations")


class SPCAnalyticsRequest(BaseModel):
    """Request for Statistical Process Control analytics"""
    start_date: date
    end_date: date
    metric: str = Field(..., description="Metric to analyze")
    chart_type: ChartType = Field(default=ChartType.XBAR_R, description="Type of control chart")
    lot_ids: Optional[List[str]] = None
    confidence_level: float = Field(default=0.997, ge=0.9, le=0.999, description="Confidence level for control limits")


class ProcessCapabilityRequest(BaseModel):
    """Request for process capability analysis"""
    start_date: date
    end_date: date
    metric: str = Field(..., description="Metric to analyze")
    lower_spec_limit: float = Field(..., description="Lower specification limit")
    upper_spec_limit: float = Field(..., description="Upper specification limit")
    target_value: Optional[float] = Field(None, description="Target value")
    lot_ids: Optional[List[str]] = None


class ParetoAnalyticsRequest(BaseModel):
    """Request for Pareto analysis"""
    start_date: date
    end_date: date
    category_field: str = Field(default="defect_type", description="Field to categorize by")
    lot_ids: Optional[List[str]] = None
    min_occurrences: int = Field(default=1, ge=1, description="Minimum occurrences to include")


# Analytics response schemas
class QualitySummaryMetrics(BaseModel):
    """Quality summary metrics"""
    total_inspections: int
    passed_inspections: int
    failed_inspections: int
    pass_rate: float = Field(..., description="Pass rate as percentage")
    total_defects: int
    defect_rate: float = Field(..., description="Defects per inspection")
    first_pass_yield: float = Field(..., description="First pass yield as percentage")
    avg_defects_per_failed: float = Field(..., description="Average defects per failed inspection")


class DefectDistribution(BaseModel):
    """Defect distribution data"""
    defect_type: str
    count: int
    percentage: float
    severity_breakdown: Dict[str, int]


class QualityTrendPoint(BaseModel):
    """Single point in quality trend"""
    date: date
    pass_rate: float
    defect_rate: float
    inspection_count: int


class QualityAnalyticsResponse(BaseModel):
    """Quality analytics response"""
    summary: QualitySummaryMetrics
    defect_distribution: List[DefectDistribution]
    trend_data: List[QualityTrendPoint]
    top_defects: List[Dict[str, Any]]
    period: Dict[str, date]


class ControlLimits(BaseModel):
    """Statistical process control limits"""
    center_line: float = Field(..., description="Process center line (average)")
    ucl: float = Field(..., description="Upper control limit")
    lcl: float = Field(..., description="Lower control limit")
    usl: Optional[float] = Field(None, description="Upper specification limit")
    lsl: Optional[float] = Field(None, description="Lower specification limit")


class SPCDataPoint(BaseModel):
    """SPC chart data point"""
    timestamp: str
    value: float
    sample_id: Optional[str] = None
    is_out_of_control: bool = False
    violation_rules: List[str] = Field(default_factory=list)


class SPCAnalyticsResponse(BaseModel):
    """SPC analytics response"""
    chart_type: ChartType
    metric_name: str
    control_limits: ControlLimits
    data_points: List[SPCDataPoint]
    out_of_control_count: int
    process_stability: str = Field(..., description="stable, unstable, or insufficient_data")
    violations_summary: Dict[str, int]
    period: Dict[str, date]


class ProcessCapabilityMetrics(BaseModel):
    """Process capability metrics"""
    cp: float = Field(..., description="Process capability index")
    cpk: float = Field(..., description="Process capability index (adjusted for centering)")
    pp: float = Field(..., description="Process performance index")
    ppk: float = Field(..., description="Process performance index (adjusted for centering)")
    mean: float = Field(..., description="Process mean")
    std_dev: float = Field(..., description="Process standard deviation")
    target: Optional[float] = Field(None, description="Target value")


class ProcessCapabilityResponse(BaseModel):
    """Process capability analysis response"""
    metrics: ProcessCapabilityMetrics
    specification_limits: Dict[str, float]
    data_summary: Dict[str, Any]
    capability_assessment: str = Field(..., description="capable, marginal, or not_capable")
    recommendations: List[str]
    period: Dict[str, date]


class ParetoItem(BaseModel):
    """Single item in Pareto analysis"""
    category: str
    count: int
    percentage: float
    cumulative_percentage: float


class ParetoAnalyticsResponse(BaseModel):
    """Pareto analysis response"""
    items: List[ParetoItem]
    total_count: int
    category_field: str
    vital_few_threshold: float = Field(default=80.0, description="Cumulative percentage for vital few")
    vital_few_categories: List[str]
    period: Dict[str, date]


class ProductionMetrics(BaseModel):
    """Production performance metrics"""
    oee: float = Field(..., description="Overall Equipment Effectiveness")
    availability: float = Field(..., description="Equipment availability")
    performance: float = Field(..., description="Performance efficiency")
    quality: float = Field(..., description="Quality rate")
    throughput: int = Field(..., description="Units produced")
    planned_production_time: float = Field(..., description="Planned time in hours")
    actual_production_time: float = Field(..., description="Actual time in hours")
    downtime: float = Field(..., description="Downtime in hours")


class ProductionAnalyticsResponse(BaseModel):
    """Production analytics response"""
    metrics: ProductionMetrics
    trend_data: List[Dict[str, Any]]
    downtime_analysis: Dict[str, Any]
    bottleneck_analysis: Dict[str, Any]
    period: Dict[str, date]
