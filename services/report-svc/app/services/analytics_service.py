"""
Statistical analytics and quality control service.
"""

from datetime import date, datetime
from typing import List, Dict, Any, Optional
import math
import structlog

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AnalyticsCalculationError
from app.schemas.analytics import (
    QualityAnalyticsRequest,
    QualityAnalyticsResponse,
    QualitySummaryMetrics,
    DefectDistribution,
    QualityTrendPoint,
    SPCAnalyticsRequest,
    SPCAnalyticsResponse,
    ControlLimits,
    SPCDataPoint,
    ChartType,
    ProcessCapabilityRequest,
    ProcessCapabilityResponse,
    ProcessCapabilityMetrics,
    ParetoAnalyticsRequest,
    ParetoAnalyticsResponse,
    ParetoItem,
    ProductionMetrics,
    ProductionAnalyticsResponse
)

logger = structlog.get_logger()


class AnalyticsService:
    """Service for statistical analytics and quality control calculations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_quality_analytics(
        self,
        request: QualityAnalyticsRequest
    ) -> QualityAnalyticsResponse:
        """Get comprehensive quality analytics"""
        logger.info(
            "Computing quality analytics",
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        # Mock data for now
        # In production, this would query actual inspection data
        summary = QualitySummaryMetrics(
            total_inspections=1000,
            passed_inspections=950,
            failed_inspections=50,
            pass_rate=95.0,
            total_defects=75,
            defect_rate=0.075,
            first_pass_yield=95.0,
            avg_defects_per_failed=1.5
        )
        
        defect_distribution = [
            DefectDistribution(
                defect_type="scratch",
                count=30,
                percentage=40.0,
                severity_breakdown={"low": 20, "medium": 8, "high": 2}
            ),
            DefectDistribution(
                defect_type="void",
                count=25,
                percentage=33.3,
                severity_breakdown={"low": 15, "medium": 8, "high": 2}
            ),
            DefectDistribution(
                defect_type="contamination",
                count=20,
                percentage=26.7,
                severity_breakdown={"low": 10, "medium": 7, "high": 3}
            )
        ]
        
        trend_data = []
        for i in range(7):
            trend_data.append(
                QualityTrendPoint(
                    date=request.start_date,
                    pass_rate=95.0 + (i * 0.5),
                    defect_rate=0.075 - (i * 0.005),
                    inspection_count=140 + (i * 5)
                )
            )
        
        top_defects = [
            {"type": "scratch", "count": 30, "severity": "medium"},
            {"type": "void", "count": 25, "severity": "low"},
            {"type": "contamination", "count": 20, "severity": "high"}
        ]
        
        return QualityAnalyticsResponse(
            summary=summary,
            defect_distribution=defect_distribution,
            trend_data=trend_data,
            top_defects=top_defects,
            period={
                "start_date": request.start_date,
                "end_date": request.end_date
            }
        )
    
    async def get_spc_analytics(
        self,
        request: SPCAnalyticsRequest
    ) -> SPCAnalyticsResponse:
        """Get Statistical Process Control analytics"""
        logger.info(
            "Computing SPC analytics",
            metric=request.metric,
            chart_type=request.chart_type
        )
        
        # Mock SPC data
        # In production, this would calculate from real data
        center_line = 95.0
        ucl = 98.5
        lcl = 91.5
        
        control_limits = ControlLimits(
            center_line=round(center_line, settings.spc_decimal_precision),
            ucl=round(ucl, settings.spc_decimal_precision),
            lcl=round(lcl, settings.spc_decimal_precision),
            usl=100.0,
            lsl=90.0
        )
        
        # Generate mock data points
        data_points = []
        for i in range(30):
            value = center_line + (i % 3 - 1) * 1.5
            is_out = value > ucl or value < lcl
            violations = []
            if is_out:
                violations.append("beyond_control_limits")
            
            data_points.append(
                SPCDataPoint(
                    timestamp=f"2025-10-{i+1:02d}",
                    value=round(value, settings.spc_decimal_precision),
                    sample_id=f"sample_{i}",
                    is_out_of_control=is_out,
                    violation_rules=violations
                )
            )
        
        out_of_control_count = sum(1 for p in data_points if p.is_out_of_control)
        
        return SPCAnalyticsResponse(
            chart_type=request.chart_type,
            metric_name=request.metric,
            control_limits=control_limits,
            data_points=data_points,
            out_of_control_count=out_of_control_count,
            process_stability="stable" if out_of_control_count == 0 else "unstable",
            violations_summary={"beyond_control_limits": out_of_control_count},
            period={
                "start_date": request.start_date,
                "end_date": request.end_date
            }
        )
    
    async def get_process_capability(
        self,
        request: ProcessCapabilityRequest
    ) -> ProcessCapabilityResponse:
        """Get process capability analysis"""
        logger.info(
            "Computing process capability",
            metric=request.metric
        )
        
        # Mock process capability calculation
        # In production, this would calculate from real data
        mean = 95.0
        std_dev = 1.5
        usl = request.upper_spec_limit
        lsl = request.lower_spec_limit
        
        # Calculate Cp and Cpk
        cp = (usl - lsl) / (6 * std_dev)
        cpu = (usl - mean) / (3 * std_dev)
        cpl = (mean - lsl) / (3 * std_dev)
        cpk = min(cpu, cpl)
        
        # For Pp and Ppk, use same values (in production, use different sigma)
        pp = cp
        ppk = cpk
        
        metrics = ProcessCapabilityMetrics(
            cp=round(cp, settings.spc_decimal_precision),
            cpk=round(cpk, settings.spc_decimal_precision),
            pp=round(pp, settings.spc_decimal_precision),
            ppk=round(ppk, settings.spc_decimal_precision),
            mean=round(mean, settings.spc_decimal_precision),
            std_dev=round(std_dev, settings.spc_decimal_precision),
            target=request.target_value
        )
        
        # Assess capability
        if cpk >= 1.33:
            assessment = "capable"
        elif cpk >= 1.0:
            assessment = "marginal"
        else:
            assessment = "not_capable"
        
        recommendations = []
        if cpk < 1.33:
            recommendations.append("Process improvement needed to meet capability targets")
        if abs(mean - ((usl + lsl) / 2)) > 0.1 * (usl - lsl):
            recommendations.append("Process centering adjustment recommended")
        
        return ProcessCapabilityResponse(
            metrics=metrics,
            specification_limits={
                "upper": usl,
                "lower": lsl,
                "target": request.target_value or (usl + lsl) / 2
            },
            data_summary={
                "sample_size": 100,
                "min_value": mean - 3 * std_dev,
                "max_value": mean + 3 * std_dev
            },
            capability_assessment=assessment,
            recommendations=recommendations,
            period={
                "start_date": request.start_date,
                "end_date": request.end_date
            }
        )
    
    async def get_pareto_analysis(
        self,
        request: ParetoAnalyticsRequest
    ) -> ParetoAnalyticsResponse:
        """Get Pareto analysis for defect prioritization"""
        logger.info(
            "Computing Pareto analysis",
            category_field=request.category_field
        )
        
        # Mock Pareto data
        # In production, this would aggregate from real data
        categories_data = [
            ("scratch", 45),
            ("void", 30),
            ("contamination", 15),
            ("misalignment", 7),
            ("crack", 3)
        ]
        
        total_count = sum(count for _, count in categories_data)
        
        items = []
        cumulative = 0.0
        vital_few = []
        
        for category, count in categories_data:
            percentage = (count / total_count) * 100
            cumulative += percentage
            
            items.append(
                ParetoItem(
                    category=category,
                    count=count,
                    percentage=round(percentage, 2),
                    cumulative_percentage=round(cumulative, 2)
                )
            )
            
            if cumulative <= 80.0:
                vital_few.append(category)
        
        return ParetoAnalyticsResponse(
            items=items,
            total_count=total_count,
            category_field=request.category_field,
            vital_few_threshold=80.0,
            vital_few_categories=vital_few,
            period={
                "start_date": request.start_date,
                "end_date": request.end_date
            }
        )
    
    async def get_production_analytics(
        self,
        start_date: date,
        end_date: date,
        production_line: Optional[str]
    ) -> ProductionAnalyticsResponse:
        """Get production performance analytics"""
        logger.info(
            "Computing production analytics",
            start_date=start_date,
            end_date=end_date
        )
        
        # Mock production metrics
        # In production, this would calculate from real data
        availability = 0.95
        performance = 0.92
        quality = 0.98
        oee = availability * performance * quality
        
        metrics = ProductionMetrics(
            oee=round(oee, 4),
            availability=round(availability, 4),
            performance=round(performance, 4),
            quality=round(quality, 4),
            throughput=9500,
            planned_production_time=240.0,
            actual_production_time=228.0,
            downtime=12.0
        )
        
        return ProductionAnalyticsResponse(
            metrics=metrics,
            trend_data=[],
            downtime_analysis={},
            bottleneck_analysis={},
            period={
                "start_date": start_date,
                "end_date": end_date
            }
        )
    
    async def get_quality_trends(
        self,
        start_date: date,
        end_date: date,
        metric: str,
        grouping: str
    ) -> Dict[str, Any]:
        """Get quality trend analysis"""
        logger.info(
            "Computing quality trends",
            metric=metric,
            grouping=grouping
        )
        
        # Mock trend data
        return {
            "metric": metric,
            "grouping": grouping,
            "data_points": [],
            "period": {
                "start_date": start_date,
                "end_date": end_date
            }
        }
