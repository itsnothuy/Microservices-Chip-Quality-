"""
Quality assessment service.

Calculates quality metrics, scores, and manages quality thresholds
for manufacturing inspections.
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
import uuid

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from services.shared.models.inspection import Inspection, Defect
from services.shared.database.enums import (
    DefectSeverityEnum,
    InspectionStatusEnum
)
from ..core.exceptions import ValidationError, InspectionNotFoundError


logger = structlog.get_logger()


class QualityMetrics:
    """Container for quality metrics"""
    
    def __init__(
        self,
        overall_score: Decimal,
        defect_count: int,
        critical_defect_count: int,
        defect_density: Decimal,
        pass_rate: Decimal,
        confidence: Decimal,
        details: Dict[str, Any]
    ):
        self.overall_score = overall_score
        self.defect_count = defect_count
        self.critical_defect_count = critical_defect_count
        self.defect_density = defect_density
        self.pass_rate = pass_rate
        self.confidence = confidence
        self.details = details
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "overall_score": float(self.overall_score),
            "defect_count": self.defect_count,
            "critical_defect_count": self.critical_defect_count,
            "defect_density": float(self.defect_density),
            "pass_rate": float(self.pass_rate),
            "confidence": float(self.confidence),
            "details": self.details
        }


class QualityThresholds:
    """Quality thresholds configuration"""
    
    def __init__(
        self,
        critical_threshold: Decimal = Decimal("0.95"),
        high_threshold: Decimal = Decimal("0.85"),
        medium_threshold: Decimal = Decimal("0.75"),
        max_critical_defects: int = 0,
        max_high_defects: int = 2,
        max_medium_defects: int = 5
    ):
        self.critical_threshold = critical_threshold
        self.high_threshold = high_threshold
        self.medium_threshold = medium_threshold
        self.max_critical_defects = max_critical_defects
        self.max_high_defects = max_high_defects
        self.max_medium_defects = max_medium_defects


class QualityService:
    """
    Quality metrics calculation and assessment.
    
    Features:
    - Overall quality score calculation
    - Defect density metrics
    - Pass/fail determination
    - Quality trend analysis
    - Threshold management
    - Statistical process control (SPC)
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.default_thresholds = QualityThresholds()
    
    async def calculate_quality_metrics(
        self,
        inspection: Inspection,
        defects: Optional[List[Defect]] = None
    ) -> QualityMetrics:
        """
        Calculate comprehensive quality metrics for an inspection.
        
        Args:
            inspection: Inspection instance
            defects: Optional list of defects (will query if not provided)
            
        Returns:
            QualityMetrics instance
        """
        if defects is None:
            defects = inspection.defects or []
        
        # Count defects by severity
        severity_counts = self._count_defects_by_severity(defects)
        
        # Calculate defect density (defects per unit area)
        defect_density = self._calculate_defect_density(defects)
        
        # Calculate overall quality score
        overall_score = self._calculate_overall_score(
            defects,
            severity_counts,
            defect_density
        )
        
        # Calculate confidence score
        confidence = self._calculate_confidence(defects)
        
        # Determine pass rate (binary: pass or fail)
        pass_rate = Decimal("1.0") if self._determine_pass_fail(overall_score, severity_counts) else Decimal("0.0")
        
        logger.info(
            "Quality metrics calculated",
            inspection_id=inspection.inspection_id,
            overall_score=float(overall_score),
            defect_count=len(defects),
            critical_defects=severity_counts.get(DefectSeverityEnum.CRITICAL, 0)
        )
        
        return QualityMetrics(
            overall_score=overall_score,
            defect_count=len(defects),
            critical_defect_count=severity_counts.get(DefectSeverityEnum.CRITICAL, 0),
            defect_density=defect_density,
            pass_rate=pass_rate,
            confidence=confidence,
            details={
                "severity_counts": {k.value: v for k, v in severity_counts.items()},
                "inspection_type": inspection.inspection_type.value,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def assess_quality(
        self,
        inspection_id: uuid.UUID,
        thresholds: Optional[QualityThresholds] = None
    ) -> Dict[str, Any]:
        """
        Assess quality and determine pass/fail status.
        
        Args:
            inspection_id: Inspection UUID
            thresholds: Optional quality thresholds (uses defaults if not provided)
            
        Returns:
            Assessment results with pass/fail determination
        """
        # Get inspection with defects
        query = select(Inspection).where(Inspection.id == inspection_id)
        result = await self.db.execute(query)
        inspection = result.scalar_one_or_none()
        
        if not inspection:
            raise InspectionNotFoundError(str(inspection_id))
        
        # Calculate metrics
        metrics = await self.calculate_quality_metrics(inspection)
        
        # Use provided thresholds or defaults
        thresholds = thresholds or self.default_thresholds
        
        # Determine pass/fail
        passed = self._assess_against_thresholds(metrics, thresholds)
        
        # Generate assessment
        assessment = {
            "inspection_id": str(inspection_id),
            "passed": passed,
            "metrics": metrics.to_dict(),
            "thresholds": {
                "critical": float(thresholds.critical_threshold),
                "high": float(thresholds.high_threshold),
                "medium": float(thresholds.medium_threshold)
            },
            "violations": self._identify_violations(metrics, thresholds),
            "assessed_at": datetime.utcnow().isoformat()
        }
        
        logger.info(
            "Quality assessed",
            inspection_id=inspection.inspection_id,
            passed=passed,
            score=float(metrics.overall_score)
        )
        
        return assessment
    
    async def get_quality_trends(
        self,
        lot_id: Optional[uuid.UUID] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get quality trend analysis over time.
        
        Args:
            lot_id: Optional lot ID to filter by
            days: Number of days to analyze
            
        Returns:
            Quality trend data
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = (
            select(
                func.date_trunc('day', Inspection.created_at).label('date'),
                func.count(Inspection.id).label('total_inspections'),
                func.avg(Inspection.overall_quality_score).label('avg_quality'),
                func.sum(
                    func.cast(Inspection.pass_fail_status, func.Integer())
                ).label('passed_count')
            )
            .where(
                and_(
                    Inspection.created_at >= start_date,
                    Inspection.status == InspectionStatusEnum.COMPLETED
                )
            )
            .group_by(func.date_trunc('day', Inspection.created_at))
            .order_by(func.date_trunc('day', Inspection.created_at))
        )
        
        if lot_id:
            query = query.where(Inspection.lot_id == lot_id)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        trends = []
        for row in rows:
            total = row.total_inspections or 0
            passed = row.passed_count or 0
            pass_rate = (passed / total * 100) if total > 0 else 0
            
            trends.append({
                "date": row.date.isoformat() if row.date else None,
                "total_inspections": total,
                "avg_quality_score": float(row.avg_quality or 0),
                "pass_rate": pass_rate
            })
        
        return {
            "period_days": days,
            "trends": trends,
            "summary": {
                "total_inspections": sum(t["total_inspections"] for t in trends),
                "avg_quality": sum(t["avg_quality_score"] for t in trends) / len(trends) if trends else 0,
                "overall_pass_rate": sum(t["pass_rate"] for t in trends) / len(trends) if trends else 0
            }
        }
    
    def _count_defects_by_severity(self, defects: List[Defect]) -> Dict[DefectSeverityEnum, int]:
        """Count defects grouped by severity"""
        counts = {severity: 0 for severity in DefectSeverityEnum}
        
        for defect in defects:
            counts[defect.severity] = counts.get(defect.severity, 0) + 1
        
        return counts
    
    def _calculate_defect_density(self, defects: List[Defect]) -> Decimal:
        """Calculate defect density (defects per unit area)"""
        if not defects:
            return Decimal("0.0")
        
        # In a real implementation, we would use actual surface area
        # For now, use a normalized metric
        total_area = Decimal("100.0")  # Normalized area
        return Decimal(len(defects)) / total_area
    
    def _calculate_overall_score(
        self,
        defects: List[Defect],
        severity_counts: Dict[DefectSeverityEnum, int],
        defect_density: Decimal
    ) -> Decimal:
        """
        Calculate overall quality score (0-1 scale).
        
        Algorithm:
        - Start with perfect score (1.0)
        - Subtract penalty for each defect based on severity
        - Apply density penalty for high defect concentration
        """
        score = Decimal("1.0")
        
        # Severity penalties
        severity_penalties = {
            DefectSeverityEnum.CRITICAL: Decimal("0.50"),
            DefectSeverityEnum.HIGH: Decimal("0.20"),
            DefectSeverityEnum.MEDIUM: Decimal("0.10"),
            DefectSeverityEnum.LOW: Decimal("0.05"),
        }
        
        # Apply defect penalties
        for severity, count in severity_counts.items():
            penalty = severity_penalties.get(severity, Decimal("0.0"))
            score -= penalty * Decimal(count)
        
        # Apply density penalty
        density_penalty = defect_density * Decimal("0.05")
        score -= density_penalty
        
        # Ensure score stays within bounds
        return max(Decimal("0.0"), min(Decimal("1.0"), score))
    
    def _calculate_confidence(self, defects: List[Defect]) -> Decimal:
        """Calculate confidence in quality assessment"""
        if not defects:
            return Decimal("1.0")
        
        # Average ML confidence scores
        ml_defects = [d for d in defects if d.confidence_score is not None]
        
        if not ml_defects:
            return Decimal("0.80")  # Default confidence for manual inspection
        
        total_confidence = sum(d.confidence_score for d in ml_defects)
        return total_confidence / Decimal(len(ml_defects))
    
    def _determine_pass_fail(
        self,
        score: Decimal,
        severity_counts: Dict[DefectSeverityEnum, int]
    ) -> bool:
        """Determine pass/fail based on score and defect counts"""
        # Automatic fail for critical defects
        if severity_counts.get(DefectSeverityEnum.CRITICAL, 0) > 0:
            return False
        
        # Pass if score above threshold
        return score >= self.default_thresholds.medium_threshold
    
    def _assess_against_thresholds(
        self,
        metrics: QualityMetrics,
        thresholds: QualityThresholds
    ) -> bool:
        """Assess quality against configured thresholds"""
        # Check critical defect threshold
        if metrics.critical_defect_count > thresholds.max_critical_defects:
            return False
        
        # Check score threshold
        if metrics.overall_score < thresholds.medium_threshold:
            return False
        
        return True
    
    def _identify_violations(
        self,
        metrics: QualityMetrics,
        thresholds: QualityThresholds
    ) -> List[Dict[str, Any]]:
        """Identify threshold violations"""
        violations = []
        
        if metrics.critical_defect_count > thresholds.max_critical_defects:
            violations.append({
                "type": "critical_defects",
                "threshold": thresholds.max_critical_defects,
                "actual": metrics.critical_defect_count,
                "severity": "critical"
            })
        
        if metrics.overall_score < thresholds.medium_threshold:
            violations.append({
                "type": "quality_score",
                "threshold": float(thresholds.medium_threshold),
                "actual": float(metrics.overall_score),
                "severity": "high"
            })
        
        return violations
