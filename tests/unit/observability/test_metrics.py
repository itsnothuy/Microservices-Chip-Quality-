"""
Unit tests for observability metrics module.
"""

import pytest
from prometheus_client import REGISTRY

from services.shared.observability.metrics.business_metrics import (
    QualityMetrics,
    ProductionMetrics,
    MLPerformanceMetrics,
)
from services.shared.observability.metrics.system_metrics import (
    SystemMetrics,
    APIMetrics,
)


class TestQualityMetrics:
    """Tests for QualityMetrics."""
    
    def test_quality_metrics_initialization(self):
        """Test quality metrics initialization."""
        metrics = QualityMetrics()
        
        assert metrics.inspection_defect_rate is not None
        assert metrics.quality_score is not None
        assert metrics.inspection_duration is not None
    
    def test_record_defect(self):
        """Test recording a defect."""
        metrics = QualityMetrics()
        
        # Record a defect
        metrics.record_defect(
            product_type="PCB-A",
            defect_type="scratch",
            severity="high"
        )
        
        # Verify counter was incremented
        # Note: In real tests, you'd check the metric value
        # Here we just verify it doesn't raise an exception
    
    def test_record_inspection_result(self):
        """Test recording an inspection result."""
        metrics = QualityMetrics()
        
        # Record passed inspection
        metrics.record_inspection_result(
            product_type="PCB-A",
            inspection_type="visual",
            passed=True,
            quality_score=0.95,
            duration_seconds=45.5
        )
        
        # Record failed inspection
        metrics.record_inspection_result(
            product_type="PCB-A",
            inspection_type="visual",
            passed=False,
            quality_score=0.65,
            duration_seconds=50.2,
            reason="quality_threshold"
        )
    
    def test_record_manual_review(self):
        """Test recording manual review requirement."""
        metrics = QualityMetrics()
        
        metrics.record_manual_review(
            product_type="PCB-B",
            reason="low_confidence"
        )


class TestProductionMetrics:
    """Tests for ProductionMetrics."""
    
    def test_production_metrics_initialization(self):
        """Test production metrics initialization."""
        metrics = ProductionMetrics()
        
        assert metrics.batch_processing_time is not None
        assert metrics.production_yield_rate is not None
        assert metrics.equipment_availability is not None
    
    def test_record_batch_completion(self):
        """Test recording batch completion."""
        metrics = ProductionMetrics()
        
        # Record small batch
        metrics.record_batch_completion(
            product_type="PCB-A",
            batch_size=5,
            duration_seconds=120.5,
            status="completed"
        )
        
        # Record large batch
        metrics.record_batch_completion(
            product_type="PCB-B",
            batch_size=150,
            duration_seconds=3600.0,
            status="completed"
        )
    
    def test_update_oee_metrics(self):
        """Test updating OEE metrics."""
        metrics = ProductionMetrics()
        
        metrics.update_oee_metrics(
            equipment_id="EQ-001",
            station="inspection-1",
            availability=0.95,
            performance=0.88,
            quality=0.92
        )


class TestMLPerformanceMetrics:
    """Tests for MLPerformanceMetrics."""
    
    def test_ml_metrics_initialization(self):
        """Test ML performance metrics initialization."""
        metrics = MLPerformanceMetrics()
        
        assert metrics.model_inference_latency is not None
        assert metrics.model_accuracy_score is not None
        assert metrics.prediction_confidence is not None
    
    def test_record_inference(self):
        """Test recording an inference request."""
        metrics = MLPerformanceMetrics()
        
        # Record successful inference
        metrics.record_inference(
            model_name="defect_detector",
            model_version="v2.1",
            latency_seconds=0.125,
            confidence=0.95,
            success=True
        )
        
        # Record failed inference
        metrics.record_inference(
            model_name="defect_detector",
            model_version="v2.1",
            latency_seconds=0.050,
            success=False
        )
    
    def test_update_model_metrics(self):
        """Test updating model performance metrics."""
        metrics = MLPerformanceMetrics()
        
        metrics.update_model_metrics(
            model_name="defect_detector",
            model_version="v2.1",
            accuracy=0.94,
            precision={"scratch": 0.92, "crack": 0.96},
            recall={"scratch": 0.88, "crack": 0.94},
            f1={"scratch": 0.90, "crack": 0.95}
        )


class TestSystemMetrics:
    """Tests for SystemMetrics."""
    
    def test_system_metrics_initialization(self):
        """Test system metrics initialization."""
        metrics = SystemMetrics()
        
        assert metrics.http_requests_total is not None
        assert metrics.db_queries_total is not None
        assert metrics.cache_operations is not None


class TestAPIMetrics:
    """Tests for APIMetrics."""
    
    def test_api_metrics_initialization(self):
        """Test API metrics initialization."""
        metrics = APIMetrics()
        
        assert metrics.rate_limit_hits is not None
        assert metrics.auth_attempts is not None
        assert metrics.active_requests is not None


class TestMetricsIntegration:
    """Integration tests for metrics."""
    
    def test_multiple_metrics_instances(self):
        """Test creating multiple metric instances."""
        quality_metrics = QualityMetrics()
        production_metrics = ProductionMetrics()
        ml_metrics = MLPerformanceMetrics()
        
        # Record various metrics
        quality_metrics.record_defect("PCB-A", "scratch", "medium")
        production_metrics.record_batch_completion("PCB-A", 10, 300.0)
        ml_metrics.record_inference("model", "v1", 0.1, 0.9, True)
        
        # All should work without conflicts
