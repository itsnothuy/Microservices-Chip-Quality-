"""Quality event producer for quality assessment and alerts."""

from typing import Dict, Any, Optional
from pathlib import Path
import json
import structlog

from events.producers.base_producer import BaseEventProducer
from events.utils.kafka_client import KafkaConfig

logger = structlog.get_logger(__name__)


class QualityEventProducer(BaseEventProducer):
    """Producer for quality-related events."""
    
    TOPIC = "chip-quality.quality.events"
    
    def __init__(self, config: Optional[KafkaConfig] = None):
        """Initialize quality event producer."""
        schema_path = Path(__file__).parent.parent / "schemas" / "quality.avsc"
        with open(schema_path, "r") as f:
            schema = json.load(f)
        
        super().__init__(
            topic=self.TOPIC,
            schema=schema,
            config=config
        )
        self.logger = logger.bind(producer="quality")
    
    async def publish_quality_assessed(
        self,
        inspection_id: str,
        batch_id: str,
        quality_score: float,
        pass_fail: bool,
        threshold: Optional[float] = None,
        defect_count: int = 0,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """Publish quality assessed event."""
        event_data = {
            "event_type": "QUALITY_ASSESSED",
            "inspection_id": inspection_id,
            "batch_id": batch_id,
            "quality_score": quality_score,
            "threshold": threshold,
            "pass_fail": pass_fail,
            "alert_level": None,
            "defect_count": defect_count,
            "metadata": metadata or {},
        }
        
        await self.publish(
            event_data,
            key=inspection_id,
            headers={"event_type": "QUALITY_ASSESSED"}
        )
        
        self.logger.info(
            "quality.assessed.event.published",
            inspection_id=inspection_id,
            quality_score=quality_score,
            pass_fail=pass_fail
        )
    
    async def publish_threshold_violated(
        self,
        inspection_id: str,
        batch_id: str,
        quality_score: float,
        threshold: float,
        alert_level: str,
        defect_count: int = 0,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """Publish threshold violated event."""
        event_data = {
            "event_type": "THRESHOLD_VIOLATED",
            "inspection_id": inspection_id,
            "batch_id": batch_id,
            "quality_score": quality_score,
            "threshold": threshold,
            "pass_fail": False,
            "alert_level": alert_level,
            "defect_count": defect_count,
            "metadata": metadata or {},
        }
        
        await self.publish(
            event_data,
            key=inspection_id,
            headers={"event_type": "THRESHOLD_VIOLATED"}
        )
        
        self.logger.warning(
            "threshold.violated.event.published",
            inspection_id=inspection_id,
            quality_score=quality_score,
            threshold=threshold,
            alert_level=alert_level
        )
    
    async def publish_alert_triggered(
        self,
        inspection_id: str,
        batch_id: str,
        quality_score: float,
        alert_level: str,
        defect_count: int = 0,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """Publish alert triggered event."""
        event_data = {
            "event_type": "ALERT_TRIGGERED",
            "inspection_id": inspection_id,
            "batch_id": batch_id,
            "quality_score": quality_score,
            "threshold": None,
            "pass_fail": False,
            "alert_level": alert_level,
            "defect_count": defect_count,
            "metadata": metadata or {},
        }
        
        await self.publish(
            event_data,
            key=inspection_id,
            headers={"event_type": "ALERT_TRIGGERED"}
        )
        
        self.logger.warning(
            "alert.triggered.event.published",
            inspection_id=inspection_id,
            alert_level=alert_level
        )
