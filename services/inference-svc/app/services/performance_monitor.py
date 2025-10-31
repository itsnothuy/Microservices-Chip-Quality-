"""
ML model performance monitoring and optimization.

Performance Metrics:
- Inference latency and throughput monitoring
- GPU utilization and memory usage tracking
- Model accuracy and confidence score analysis
- Error rate and failure pattern detection
- Resource consumption optimization
- Cost per inference calculation

Model Health Monitoring:
- Model drift detection and alerting
- Accuracy degradation monitoring
- Performance regression identification
- Resource utilization anomaly detection
- Predictive maintenance for model updates
- Real-time dashboard for model health

Business Impact Monitoring:
- Quality improvement metrics from ML implementation
- False positive/negative rate tracking
- Business value measurement (cost savings, efficiency gains)
- ROI calculation for ML investment
- Integration with business intelligence systems
"""

import asyncio
from typing import Any
from datetime import datetime, timedelta
from collections import defaultdict, deque

import structlog
from redis import asyncio as aioredis

from ..core.config import settings


logger = structlog.get_logger()


class PerformanceMonitor:
    """
    Performance monitoring service for ML models.
    
    Tracks and analyzes model performance metrics,
    detects anomalies, and provides insights.
    """
    
    def __init__(self, redis: aioredis.Redis):
        """
        Initialize performance monitor.
        
        Args:
            redis: Redis client for metric storage
        """
        self.redis = redis
        self._metrics_buffer: defaultdict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        logger.info("Performance monitor initialized")
    
    async def record_inference(
        self,
        model_name: str,
        model_version: str,
        latency_ms: float,
        success: bool,
        confidence: float | None = None,
        metadata: dict[str, Any] | None = None
    ) -> None:
        """
        Record inference performance metrics.
        
        Args:
            model_name: Name of the model
            model_version: Model version
            latency_ms: Inference latency in milliseconds
            success: Whether inference succeeded
            confidence: Prediction confidence score
            metadata: Additional metadata
        """
        timestamp = datetime.utcnow()
        
        # Store in buffer
        metric_key = f"{model_name}:{model_version}"
        self._metrics_buffer[metric_key].append({
            "timestamp": timestamp,
            "latency_ms": latency_ms,
            "success": success,
            "confidence": confidence,
            "metadata": metadata or {}
        })
        
        # Store in Redis with TTL
        redis_key = f"metrics:{model_name}:{model_version}:{timestamp.timestamp()}"
        metric_data = {
            "latency_ms": str(latency_ms),
            "success": str(success),
            "confidence": str(confidence) if confidence else "",
            "timestamp": timestamp.isoformat()
        }
        
        await self.redis.hset(redis_key, mapping=metric_data)
        await self.redis.expire(redis_key, 86400)  # 24 hour TTL
        
        logger.debug(
            "Inference metric recorded",
            model_name=model_name,
            latency_ms=latency_ms,
            success=success
        )
    
    async def get_metrics(
        self,
        model_name: str,
        model_version: str = "",
        period_minutes: int = 60
    ) -> dict[str, Any]:
        """
        Get aggregated metrics for a model.
        
        Args:
            model_name: Name of the model
            model_version: Model version (all if empty)
            period_minutes: Time period to aggregate
            
        Returns:
            Dictionary of aggregated metrics
        """
        metric_key = f"{model_name}:{model_version}"
        
        # Get recent metrics from buffer
        recent_metrics = list(self._metrics_buffer.get(metric_key, []))
        
        # Filter by time period
        cutoff_time = datetime.utcnow() - timedelta(minutes=period_minutes)
        recent_metrics = [
            m for m in recent_metrics
            if m["timestamp"] >= cutoff_time
        ]
        
        if not recent_metrics:
            return {
                "model_name": model_name,
                "model_version": model_version,
                "total_requests": 0,
                "period_minutes": period_minutes
            }
        
        # Calculate aggregations
        latencies = [m["latency_ms"] for m in recent_metrics]
        successes = [m for m in recent_metrics if m["success"]]
        confidences = [m["confidence"] for m in recent_metrics if m["confidence"] is not None]
        
        metrics = {
            "model_name": model_name,
            "model_version": model_version,
            "period_minutes": period_minutes,
            "total_requests": len(recent_metrics),
            "successful_requests": len(successes),
            "failed_requests": len(recent_metrics) - len(successes),
            "success_rate": len(successes) / len(recent_metrics) if recent_metrics else 0,
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
            "min_latency_ms": min(latencies) if latencies else 0,
            "max_latency_ms": max(latencies) if latencies else 0,
            "p50_latency_ms": self._percentile(latencies, 50) if latencies else 0,
            "p95_latency_ms": self._percentile(latencies, 95) if latencies else 0,
            "p99_latency_ms": self._percentile(latencies, 99) if latencies else 0,
            "throughput_per_minute": len(recent_metrics) / period_minutes if period_minutes > 0 else 0,
            "avg_confidence": sum(confidences) / len(confidences) if confidences else 0,
            "period_start": cutoff_time.isoformat(),
            "period_end": datetime.utcnow().isoformat()
        }
        
        logger.debug("Metrics aggregated", model_name=model_name, metrics=metrics)
        return metrics
    
    async def detect_anomalies(
        self,
        model_name: str,
        model_version: str = ""
    ) -> list[dict[str, Any]]:
        """
        Detect performance anomalies.
        
        Args:
            model_name: Name of the model
            model_version: Model version
            
        Returns:
            List of detected anomalies
        """
        metrics = await self.get_metrics(model_name, model_version, period_minutes=60)
        
        anomalies = []
        
        # Check latency anomalies
        if metrics.get("avg_latency_ms", 0) > 2000:  # 2 second threshold
            anomalies.append({
                "type": "high_latency",
                "severity": "warning",
                "message": f"Average latency {metrics['avg_latency_ms']:.1f}ms exceeds threshold",
                "value": metrics["avg_latency_ms"],
                "threshold": 2000
            })
        
        # Check success rate anomalies
        if metrics.get("success_rate", 1.0) < 0.95:  # 95% threshold
            anomalies.append({
                "type": "low_success_rate",
                "severity": "critical",
                "message": f"Success rate {metrics['success_rate']:.2%} below threshold",
                "value": metrics["success_rate"],
                "threshold": 0.95
            })
        
        # Check confidence anomalies
        if metrics.get("avg_confidence", 1.0) < 0.7:  # 70% threshold
            anomalies.append({
                "type": "low_confidence",
                "severity": "warning",
                "message": f"Average confidence {metrics['avg_confidence']:.2%} below threshold",
                "value": metrics["avg_confidence"],
                "threshold": 0.7
            })
        
        if anomalies:
            logger.warning(
                "Performance anomalies detected",
                model_name=model_name,
                anomaly_count=len(anomalies)
            )
        
        return anomalies
    
    async def get_model_health_status(
        self,
        model_name: str,
        model_version: str = ""
    ) -> dict[str, Any]:
        """
        Get overall model health status.
        
        Args:
            model_name: Name of the model
            model_version: Model version
            
        Returns:
            Health status dictionary
        """
        metrics = await self.get_metrics(model_name, model_version, period_minutes=60)
        anomalies = await self.detect_anomalies(model_name, model_version)
        
        # Determine overall health
        if any(a["severity"] == "critical" for a in anomalies):
            health_status = "critical"
        elif any(a["severity"] == "warning" for a in anomalies):
            health_status = "degraded"
        elif metrics.get("total_requests", 0) == 0:
            health_status = "idle"
        else:
            health_status = "healthy"
        
        return {
            "model_name": model_name,
            "model_version": model_version,
            "health_status": health_status,
            "metrics": metrics,
            "anomalies": anomalies,
            "checked_at": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def _percentile(data: list[float], percentile: int) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    async def clear_metrics(self, model_name: str, model_version: str = "") -> None:
        """
        Clear metrics for a model.
        
        Args:
            model_name: Name of the model
            model_version: Model version
        """
        metric_key = f"{model_name}:{model_version}"
        if metric_key in self._metrics_buffer:
            self._metrics_buffer[metric_key].clear()
        
        # Clear from Redis
        pattern = f"metrics:{model_name}:{model_version}:*"
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
        
        logger.info("Metrics cleared", model_name=model_name, model_version=model_version)
