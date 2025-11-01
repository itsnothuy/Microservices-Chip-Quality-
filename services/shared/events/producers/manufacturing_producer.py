"""Manufacturing event producer for batch and lot processing events."""

from typing import Dict, Any, Optional
from pathlib import Path
import json
import structlog

from events.producers.base_producer import BaseEventProducer
from events.utils.kafka_client import KafkaConfig

logger = structlog.get_logger(__name__)


class ManufacturingEventProducer(BaseEventProducer):
    """Producer for manufacturing-related events."""
    
    TOPIC = "chip-quality.manufacturing.events"
    
    def __init__(self, config: Optional[KafkaConfig] = None):
        """Initialize manufacturing event producer."""
        schema_path = Path(__file__).parent.parent / "schemas" / "manufacturing.avsc"
        with open(schema_path, "r") as f:
            schema = json.load(f)
        
        super().__init__(
            topic=self.TOPIC,
            schema=schema,
            config=config
        )
        self.logger = logger.bind(producer="manufacturing")
    
    async def publish_batch_created(
        self,
        batch_id: str,
        part_number: str,
        quantity: int,
        lot_id: Optional[str] = None,
        station_id: Optional[str] = None,
        operator_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """Publish batch created event."""
        event_data = {
            "event_type": "BATCH_CREATED",
            "batch_id": batch_id,
            "lot_id": lot_id,
            "part_number": part_number,
            "quantity": quantity,
            "status": "created",
            "station_id": station_id,
            "operator_id": operator_id,
            "metadata": metadata or {},
        }
        
        await self.publish(
            event_data,
            key=batch_id,
            headers={"event_type": "BATCH_CREATED"}
        )
        
        self.logger.info(
            "batch.created.event.published",
            batch_id=batch_id,
            part_number=part_number,
            quantity=quantity
        )
    
    async def publish_lot_created(
        self,
        batch_id: str,
        lot_id: str,
        part_number: str,
        quantity: int,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """Publish lot created event."""
        event_data = {
            "event_type": "LOT_CREATED",
            "batch_id": batch_id,
            "lot_id": lot_id,
            "part_number": part_number,
            "quantity": quantity,
            "status": "created",
            "station_id": None,
            "operator_id": None,
            "metadata": metadata or {},
        }
        
        await self.publish(
            event_data,
            key=lot_id,
            headers={"event_type": "LOT_CREATED"}
        )
        
        self.logger.info(
            "lot.created.event.published",
            batch_id=batch_id,
            lot_id=lot_id
        )
