"""
Business-Specific Metrics for Manufacturing Platform

Provides comprehensive business metrics tracking:
- Quality metrics (defect rates, quality scores)
- Production metrics (throughput, efficiency)
- ML performance metrics (accuracy, latency)
- User activity metrics (authentication, features)
- System performance metrics (API, database)
- Cost metrics (resource utilization)
"""

from typing import Optional, Dict, Any
from prometheus_client import Counter, Histogram, Gauge, Summary
import structlog

logger = structlog.get_logger()


class QualityMetrics:
    """
    Quality-related business metrics for defect detection and inspection.
    
    Tracks:
    - Inspection defect rates by product type
    - Quality score distributions
    - Inspection throughput
    - Manual review requirements
    - False positive/negative rates
    - Compliance violations
    """
    
    def __init__(self) -> None:
        # Defect metrics
        self.inspection_defect_rate = Counter(
            'inspection_defects_total',
            'Total number of defects detected',
            ['product_type', 'defect_type', 'severity']
        )
        
        self.inspection_passed = Counter(
            'inspections_passed_total',
            'Total number of passed inspections',
            ['product_type', 'inspection_type']
        )
        
        self.inspection_failed = Counter(
            'inspections_failed_total',
            'Total number of failed inspections',
            ['product_type', 'inspection_type', 'reason']
        )
        
        # Quality score metrics
        self.quality_score = Histogram(
            'quality_score',
            'Quality score distribution',
            ['product_type'],
            buckets=[0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.99, 1.0]
        )
        
        # Inspection throughput
        self.inspections_completed = Counter(
            'inspections_completed_total',
            'Total number of completed inspections',
            ['product_type', 'status']
        )
        
        self.inspection_duration = Histogram(
            'inspection_duration_seconds',
            'Time taken to complete inspection',
            ['product_type', 'inspection_type'],
            buckets=[1, 5, 10, 30, 60, 120, 300, 600]
        )
        
        # Manual review metrics
        self.manual_review_required = Counter(
            'manual_reviews_required_total',
            'Number of inspections requiring manual review',
            ['product_type', 'reason']
        )
        
        self.manual_review_rate = Gauge(
            'manual_review_rate',
            'Percentage of inspections requiring manual review',
            ['product_type']
        )
        
        # Model accuracy metrics
        self.false_positive_rate = Gauge(
            'false_positive_rate',
            'False positive detection rate',
            ['model_version', 'defect_type']
        )
        
        self.false_negative_rate = Gauge(
            'false_negative_rate',
            'False negative detection rate',
            ['model_version', 'defect_type']
        )
        
        # Compliance metrics
        self.compliance_violations = Counter(
            'compliance_violations_total',
            'Compliance violations detected',
            ['regulation', 'severity', 'product_type']
        )
        
        # Active quality alerts
        self.quality_alerts_active = Gauge(
            'quality_alerts_active',
            'Number of active quality alerts',
            ['alert_type', 'severity']
        )
        
        logger.info("Quality metrics initialized")
    
    def record_defect(
        self,
        product_type: str,
        defect_type: str,
        severity: str = "medium"
    ) -> None:
        """Record a detected defect."""
        self.inspection_defect_rate.labels(
            product_type=product_type,
            defect_type=defect_type,
            severity=severity
        ).inc()
    
    def record_inspection_result(
        self,
        product_type: str,
        inspection_type: str,
        passed: bool,
        quality_score: float,
        duration_seconds: float,
        reason: Optional[str] = None
    ) -> None:
        """Record inspection result with quality metrics."""
        if passed:
            self.inspection_passed.labels(
                product_type=product_type,
                inspection_type=inspection_type
            ).inc()
        else:
            self.inspection_failed.labels(
                product_type=product_type,
                inspection_type=inspection_type,
                reason=reason or "quality_threshold"
            ).inc()
        
        self.quality_score.labels(product_type=product_type).observe(quality_score)
        self.inspection_duration.labels(
            product_type=product_type,
            inspection_type=inspection_type
        ).observe(duration_seconds)
        
        self.inspections_completed.labels(
            product_type=product_type,
            status="passed" if passed else "failed"
        ).inc()
    
    def record_manual_review(
        self,
        product_type: str,
        reason: str
    ) -> None:
        """Record requirement for manual review."""
        self.manual_review_required.labels(
            product_type=product_type,
            reason=reason
        ).inc()


class ProductionMetrics:
    """
    Production and manufacturing efficiency metrics.
    
    Tracks:
    - Batch processing times
    - Manufacturing efficiency (OEE)
    - Yield rates
    - Downtime duration
    - Resource utilization
    - Cost per unit
    """
    
    def __init__(self) -> None:
        # Batch processing
        self.batch_processing_time = Histogram(
            'batch_processing_time_seconds',
            'Time to complete batch processing',
            ['product_type', 'batch_size_range'],
            buckets=[60, 300, 600, 1800, 3600, 7200, 14400]
        )
        
        self.batches_completed = Counter(
            'batches_completed_total',
            'Total batches completed',
            ['product_type', 'status']
        )
        
        # Manufacturing efficiency (Overall Equipment Effectiveness)
        self.equipment_availability = Gauge(
            'equipment_availability',
            'Equipment availability percentage',
            ['equipment_id', 'station']
        )
        
        self.equipment_performance = Gauge(
            'equipment_performance',
            'Equipment performance efficiency',
            ['equipment_id', 'station']
        )
        
        self.equipment_quality = Gauge(
            'equipment_quality',
            'Equipment quality rate',
            ['equipment_id', 'station']
        )
        
        # Yield metrics
        self.production_yield_rate = Gauge(
            'production_yield_rate',
            'Production yield percentage',
            ['product_type', 'production_line']
        )
        
        self.units_produced = Counter(
            'units_produced_total',
            'Total units produced',
            ['product_type', 'production_line']
        )
        
        self.units_rejected = Counter(
            'units_rejected_total',
            'Total units rejected',
            ['product_type', 'rejection_reason']
        )
        
        # Downtime tracking
        self.downtime_duration = Summary(
            'downtime_duration_seconds',
            'Unplanned downtime duration',
            ['equipment_id', 'reason']
        )
        
        self.downtime_events = Counter(
            'downtime_events_total',
            'Number of downtime events',
            ['equipment_id', 'reason', 'planned']
        )
        
        # Resource utilization
        self.resource_utilization = Gauge(
            'resource_utilization',
            'Resource utilization percentage',
            ['resource_type', 'resource_id']
        )
        
        # Cost metrics
        self.cost_per_unit = Gauge(
            'cost_per_unit',
            'Manufacturing cost per unit',
            ['product_type', 'cost_category']
        )
        
        self.operational_costs = Counter(
            'operational_costs_total',
            'Total operational costs',
            ['category', 'department']
        )
        
        logger.info("Production metrics initialized")
    
    def record_batch_completion(
        self,
        product_type: str,
        batch_size: int,
        duration_seconds: float,
        status: str = "completed"
    ) -> None:
        """Record batch processing completion."""
        # Categorize batch size for better aggregation
        if batch_size < 10:
            size_range = "small"
        elif batch_size < 50:
            size_range = "medium"
        elif batch_size < 200:
            size_range = "large"
        else:
            size_range = "xlarge"
        
        self.batch_processing_time.labels(
            product_type=product_type,
            batch_size_range=size_range
        ).observe(duration_seconds)
        
        self.batches_completed.labels(
            product_type=product_type,
            status=status
        ).inc()
    
    def update_oee_metrics(
        self,
        equipment_id: str,
        station: str,
        availability: float,
        performance: float,
        quality: float
    ) -> None:
        """Update Overall Equipment Effectiveness (OEE) metrics."""
        self.equipment_availability.labels(
            equipment_id=equipment_id,
            station=station
        ).set(availability)
        
        self.equipment_performance.labels(
            equipment_id=equipment_id,
            station=station
        ).set(performance)
        
        self.equipment_quality.labels(
            equipment_id=equipment_id,
            station=station
        ).set(quality)


class MLPerformanceMetrics:
    """
    Machine Learning model performance metrics.
    
    Tracks:
    - Model inference latency
    - Model accuracy and drift
    - Training pipeline success
    - Feature importance
    - Prediction confidence
    """
    
    def __init__(self) -> None:
        # Inference metrics
        self.model_inference_latency = Histogram(
            'model_inference_latency_seconds',
            'ML model inference latency',
            ['model_name', 'model_version'],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        )
        
        self.inference_requests = Counter(
            'inference_requests_total',
            'Total inference requests',
            ['model_name', 'model_version', 'status']
        )
        
        # Model accuracy
        self.model_accuracy_score = Gauge(
            'model_accuracy_score',
            'Model accuracy score',
            ['model_name', 'model_version', 'metric_type']
        )
        
        self.model_precision = Gauge(
            'model_precision',
            'Model precision score',
            ['model_name', 'model_version', 'class']
        )
        
        self.model_recall = Gauge(
            'model_recall',
            'Model recall score',
            ['model_name', 'model_version', 'class']
        )
        
        self.model_f1_score = Gauge(
            'model_f1_score',
            'Model F1 score',
            ['model_name', 'model_version', 'class']
        )
        
        # Model drift detection
        self.model_drift_score = Gauge(
            'model_drift_score',
            'Model drift detection score',
            ['model_name', 'model_version', 'drift_type']
        )
        
        # Prediction confidence
        self.prediction_confidence = Histogram(
            'prediction_confidence',
            'Prediction confidence distribution',
            ['model_name', 'model_version'],
            buckets=[0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.99, 1.0]
        )
        
        # Training pipeline
        self.training_jobs = Counter(
            'training_jobs_total',
            'Total training jobs',
            ['model_name', 'status']
        )
        
        self.training_duration = Histogram(
            'training_duration_seconds',
            'Training job duration',
            ['model_name'],
            buckets=[60, 300, 600, 1800, 3600, 7200, 14400, 28800]
        )
        
        # Feature importance
        self.feature_importance = Gauge(
            'feature_importance',
            'Feature importance scores',
            ['model_name', 'feature_name']
        )
        
        logger.info("ML performance metrics initialized")
    
    def record_inference(
        self,
        model_name: str,
        model_version: str,
        latency_seconds: float,
        confidence: Optional[float] = None,
        success: bool = True
    ) -> None:
        """Record ML inference request."""
        self.model_inference_latency.labels(
            model_name=model_name,
            model_version=model_version
        ).observe(latency_seconds)
        
        self.inference_requests.labels(
            model_name=model_name,
            model_version=model_version,
            status="success" if success else "failure"
        ).inc()
        
        if confidence is not None:
            self.prediction_confidence.labels(
                model_name=model_name,
                model_version=model_version
            ).observe(confidence)
    
    def update_model_metrics(
        self,
        model_name: str,
        model_version: str,
        accuracy: float,
        precision: Optional[Dict[str, float]] = None,
        recall: Optional[Dict[str, float]] = None,
        f1: Optional[Dict[str, float]] = None
    ) -> None:
        """Update model performance metrics."""
        self.model_accuracy_score.labels(
            model_name=model_name,
            model_version=model_version,
            metric_type="overall"
        ).set(accuracy)
        
        if precision:
            for class_name, score in precision.items():
                self.model_precision.labels(
                    model_name=model_name,
                    model_version=model_version,
                    class_=class_name
                ).set(score)
        
        if recall:
            for class_name, score in recall.items():
                self.model_recall.labels(
                    model_name=model_name,
                    model_version=model_version,
                    class_=class_name
                ).set(score)
        
        if f1:
            for class_name, score in f1.items():
                self.model_f1_score.labels(
                    model_name=model_name,
                    model_version=model_version,
                    class_=class_name
                ).set(score)
