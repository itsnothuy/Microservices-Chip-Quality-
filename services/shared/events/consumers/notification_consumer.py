"""Notification consumer for alert and notification handling."""

import json
from pathlib import Path
from typing import Dict, Any

import structlog
from aiokafka.structs import ConsumerRecord

from events.consumers.base_consumer import BaseEventConsumer
from events.utils.kafka_client import KafkaConfig

logger = structlog.get_logger(__name__)


class NotificationConsumer(BaseEventConsumer):
    """Consumer for notification and alert processing."""
    
    def __init__(self, config: KafkaConfig = None):
        """Initialize notification consumer."""
        schema_path = Path(__file__).parent.parent / "schemas" / "quality.avsc"
        with open(schema_path, "r") as f:
            schema = json.load(f)
        
        super().__init__(
            topics=["chip-quality.quality.events"],
            group_id="notification-processor-group",
            schema=schema,
            config=config
        )
        self.logger = logger.bind(consumer="notification")
        
        # Notification tracking
        self._notifications_sent = 0
        self._alerts_triggered = 0
    
    async def process_event(
        self, 
        event_data: Dict[str, Any], 
        record: ConsumerRecord
    ) -> None:
        """Process quality event for notifications.
        
        Args:
            event_data: Deserialized event data
            record: Kafka consumer record
        """
        event_type = event_data.get("event_type")
        
        if event_type == "THRESHOLD_VIOLATED":
            await self._send_threshold_alert(event_data)
        elif event_type == "ALERT_TRIGGERED":
            await self._send_quality_alert(event_data)
        
        self.logger.info(
            "notification.event.processed",
            event_type=event_type,
            event_id=event_data.get("event_id")
        )
    
    async def _send_threshold_alert(self, event_data: Dict[str, Any]) -> None:
        """Send alert for threshold violation."""
        inspection_id = event_data.get("inspection_id")
        quality_score = event_data.get("quality_score")
        threshold = event_data.get("threshold")
        alert_level = event_data.get("alert_level")
        
        # In production, this would send actual notifications
        # (email, SMS, Slack, etc.)
        self.logger.warning(
            "notification.threshold.alert",
            inspection_id=inspection_id,
            quality_score=quality_score,
            threshold=threshold,
            alert_level=alert_level,
            message=f"Quality score {quality_score} below threshold {threshold}"
        )
        
        self._alerts_triggered += 1
        self._notifications_sent += 1
    
    async def _send_quality_alert(self, event_data: Dict[str, Any]) -> None:
        """Send quality alert notification."""
        inspection_id = event_data.get("inspection_id")
        alert_level = event_data.get("alert_level")
        defect_count = event_data.get("defect_count", 0)
        
        self.logger.warning(
            "notification.quality.alert",
            inspection_id=inspection_id,
            alert_level=alert_level,
            defect_count=defect_count,
            message=f"Quality alert: {alert_level} level with {defect_count} defects"
        )
        
        self._alerts_triggered += 1
        self._notifications_sent += 1
    
    def get_notification_metrics(self) -> Dict[str, Any]:
        """Get notification metrics."""
        return {
            "notifications_sent": self._notifications_sent,
            "alerts_triggered": self._alerts_triggered,
        }
    
    async def run(self) -> None:
        """Run the notification consumer."""
        await self.start()
        
        try:
            await self.consume_with_retry(
                handler=self.process_event,
                max_retries=3,
                retry_delay=1.0
            )
        finally:
            await self.stop()
