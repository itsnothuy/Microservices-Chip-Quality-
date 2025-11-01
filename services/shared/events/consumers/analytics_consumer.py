"""Real-time analytics consumer for quality metrics processing.

This consumer processes inspection and quality events to:
- Calculate real-time quality metrics
- Monitor production line performance
- Track defect rates and trends
- Monitor inspection throughput
- Detect quality threshold violations
- Generate alerts for quality issues
"""

from typing import Dict, Any
from pathlib import Path
import json
from datetime import datetime
from aiokafka.structs import ConsumerRecord
import structlog

from events.consumers.base_consumer import BaseEventConsumer
from events.utils.kafka_client import KafkaConfig

logger = structlog.get_logger(__name__)


class AnalyticsConsumer(BaseEventConsumer):
    """Consumer for real-time analytics processing."""
    
    def __init__(self, config: KafkaConfig = None):
        """Initialize analytics consumer."""
        # Load inspection schema for processing
        schema_path = Path(__file__).parent.parent / "schemas" / "inspection.avsc"
        with open(schema_path, "r") as f:
            schema = json.load(f)
        
        super().__init__(
            topics=[
                "chip-quality.inspection.events",
                "chip-quality.quality.events"
            ],
            group_id="analytics-processor-group",
            schema=schema,
            config=config
        )
        self.logger = logger.bind(consumer="analytics")
        
        # Analytics metrics
        self._quality_scores: list[float] = []
        self._defect_counts: Dict[str, int] = {}
        self._inspection_counts: Dict[str, int] = {}
    
    async def process_event(
        self, 
        event_data: Dict[str, Any], 
        record: ConsumerRecord
    ) -> None:
        """Process an event for analytics.
        
        Args:
            event_data: Deserialized event data
            record: Kafka consumer record
        """
        event_type = event_data.get("event_type")
        
        if event_type == "INSPECTION_COMPLETED":
            await self._process_inspection_completed(event_data)
        elif event_type == "DEFECT_DETECTED":
            await self._process_defect_detected(event_data)
        elif event_type == "QUALITY_ASSESSED":
            await self._process_quality_assessed(event_data)
        
        self.logger.info(
            "analytics.event.processed",
            event_type=event_type,
            event_id=event_data.get("event_id"),
            topic=record.topic
        )
    
    async def _process_inspection_completed(
        self, 
        event_data: Dict[str, Any]
    ) -> None:
        """Process inspection completed event."""
        inspection_type = event_data.get("inspection_type")
        quality_score = event_data.get("quality_score")
        
        # Track inspection counts
        self._inspection_counts[inspection_type] = \
            self._inspection_counts.get(inspection_type, 0) + 1
        
        # Track quality scores
        if quality_score is not None:
            self._quality_scores.append(quality_score)
        
        self.logger.info(
            "analytics.inspection.completed",
            inspection_id=event_data.get("inspection_id"),
            inspection_type=inspection_type,
            quality_score=quality_score
        )
    
    async def _process_defect_detected(
        self, 
        event_data: Dict[str, Any]
    ) -> None:
        """Process defect detected event."""
        defects = event_data.get("defects", [])
        
        for defect in defects:
            defect_type = defect.get("defect_type")
            self._defect_counts[defect_type] = \
                self._defect_counts.get(defect_type, 0) + 1
        
        self.logger.warning(
            "analytics.defect.detected",
            inspection_id=event_data.get("inspection_id"),
            defect_count=len(defects),
            defect_types=[d.get("defect_type") for d in defects]
        )
    
    async def _process_quality_assessed(
        self, 
        event_data: Dict[str, Any]
    ) -> None:
        """Process quality assessed event."""
        quality_score = event_data.get("quality_score")
        pass_fail = event_data.get("pass_fail")
        threshold = event_data.get("threshold")
        
        # Track quality scores
        if quality_score is not None:
            self._quality_scores.append(quality_score)
        
        # Check for threshold violations
        if not pass_fail and threshold is not None:
            self.logger.warning(
                "analytics.threshold.violation",
                inspection_id=event_data.get("inspection_id"),
                quality_score=quality_score,
                threshold=threshold
            )
    
    def get_analytics_metrics(self) -> Dict[str, Any]:
        """Get current analytics metrics.
        
        Returns:
            Dictionary of analytics metrics
        """
        avg_quality_score = None
        if self._quality_scores:
            avg_quality_score = sum(self._quality_scores) / len(self._quality_scores)
        
        return {
            "inspection_counts": self._inspection_counts,
            "defect_counts": self._defect_counts,
            "total_quality_scores": len(self._quality_scores),
            "avg_quality_score": avg_quality_score,
            "total_defects": sum(self._defect_counts.values()),
        }
    
    async def run(self) -> None:
        """Run the analytics consumer."""
        await self.start()
        
        try:
            await self.consume_with_retry(
                handler=self.process_event,
                max_retries=3,
                retry_delay=1.0
            )
        finally:
            await self.stop()
