"""Inspection event producer for quality inspection lifecycle events.

This module provides event publishing for:
- Inspection lifecycle events (created, started, completed)
- Quality assessment results and scoring
- Defect detection and classification events
- ML inference completion and results
- Manual review and approval events
- Error and failure condition events
"""

from typing import Dict, Any, Optional
from pathlib import Path
import json
import structlog

from events.producers.base_producer import BaseEventProducer
from events.utils.kafka_client import KafkaConfig

logger = structlog.get_logger(__name__)


class InspectionEventProducer(BaseEventProducer):
    """Producer for inspection-related events."""
    
    TOPIC = "chip-quality.inspection.events"
    
    def __init__(self, config: Optional[KafkaConfig] = None):
        """Initialize inspection event producer.
        
        Args:
            config: Kafka configuration
        """
        # Load inspection schema
        schema_path = Path(__file__).parent.parent / "schemas" / "inspection.avsc"
        with open(schema_path, "r") as f:
            schema = json.load(f)
        
        super().__init__(
            topic=self.TOPIC,
            schema=schema,
            config=config
        )
        self.logger = logger.bind(producer="inspection")
    
    async def publish_inspection_created(
        self,
        inspection_id: str,
        batch_id: str,
        chip_id: str,
        inspection_type: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """Publish inspection created event.
        
        Args:
            inspection_id: Unique inspection identifier
            batch_id: Batch identifier
            chip_id: Chip identifier
            inspection_type: Type of inspection
            metadata: Optional metadata
        """
        event_data = {
            "event_type": "INSPECTION_CREATED",
            "inspection_id": inspection_id,
            "batch_id": batch_id,
            "chip_id": chip_id,
            "inspection_type": inspection_type,
            "status": "pending",
            "quality_score": None,
            "defects": [],
            "metadata": metadata or {},
        }
        
        await self.publish(
            event_data,
            key=inspection_id,
            headers={"event_type": "INSPECTION_CREATED"}
        )
        
        self.logger.info(
            "inspection.created.event.published",
            inspection_id=inspection_id,
            batch_id=batch_id
        )
    
    async def publish_inspection_started(
        self,
        inspection_id: str,
        batch_id: str,
        chip_id: str,
        inspection_type: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """Publish inspection started event.
        
        Args:
            inspection_id: Unique inspection identifier
            batch_id: Batch identifier
            chip_id: Chip identifier
            inspection_type: Type of inspection
            metadata: Optional metadata
        """
        event_data = {
            "event_type": "INSPECTION_STARTED",
            "inspection_id": inspection_id,
            "batch_id": batch_id,
            "chip_id": chip_id,
            "inspection_type": inspection_type,
            "status": "in_progress",
            "quality_score": None,
            "defects": [],
            "metadata": metadata or {},
        }
        
        await self.publish(
            event_data,
            key=inspection_id,
            headers={"event_type": "INSPECTION_STARTED"}
        )
        
        self.logger.info(
            "inspection.started.event.published",
            inspection_id=inspection_id
        )
    
    async def publish_inspection_completed(
        self,
        inspection_id: str,
        batch_id: str,
        chip_id: str,
        inspection_type: str,
        quality_score: Optional[float] = None,
        defects: Optional[list[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """Publish inspection completed event.
        
        Args:
            inspection_id: Unique inspection identifier
            batch_id: Batch identifier
            chip_id: Chip identifier
            inspection_type: Type of inspection
            quality_score: Quality score
            defects: List of detected defects
            metadata: Optional metadata
        """
        event_data = {
            "event_type": "INSPECTION_COMPLETED",
            "inspection_id": inspection_id,
            "batch_id": batch_id,
            "chip_id": chip_id,
            "inspection_type": inspection_type,
            "status": "completed",
            "quality_score": quality_score,
            "defects": defects or [],
            "metadata": metadata or {},
        }
        
        await self.publish(
            event_data,
            key=inspection_id,
            headers={"event_type": "INSPECTION_COMPLETED"}
        )
        
        self.logger.info(
            "inspection.completed.event.published",
            inspection_id=inspection_id,
            quality_score=quality_score,
            defect_count=len(defects) if defects else 0
        )
    
    async def publish_inspection_failed(
        self,
        inspection_id: str,
        batch_id: str,
        chip_id: str,
        inspection_type: str,
        error_message: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """Publish inspection failed event.
        
        Args:
            inspection_id: Unique inspection identifier
            batch_id: Batch identifier
            chip_id: Chip identifier
            inspection_type: Type of inspection
            error_message: Error message
            metadata: Optional metadata
        """
        event_data = {
            "event_type": "INSPECTION_FAILED",
            "inspection_id": inspection_id,
            "batch_id": batch_id,
            "chip_id": chip_id,
            "inspection_type": inspection_type,
            "status": "failed",
            "quality_score": None,
            "defects": [],
            "metadata": {
                **(metadata or {}),
                "error_message": error_message
            },
        }
        
        await self.publish(
            event_data,
            key=inspection_id,
            headers={"event_type": "INSPECTION_FAILED"}
        )
        
        self.logger.error(
            "inspection.failed.event.published",
            inspection_id=inspection_id,
            error=error_message
        )
    
    async def publish_defect_detected(
        self,
        inspection_id: str,
        batch_id: str,
        chip_id: str,
        inspection_type: str,
        defects: list[Dict[str, Any]],
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """Publish defect detected event.
        
        Args:
            inspection_id: Unique inspection identifier
            batch_id: Batch identifier
            chip_id: Chip identifier
            inspection_type: Type of inspection
            defects: List of detected defects
            metadata: Optional metadata
        """
        event_data = {
            "event_type": "DEFECT_DETECTED",
            "inspection_id": inspection_id,
            "batch_id": batch_id,
            "chip_id": chip_id,
            "inspection_type": inspection_type,
            "status": "defect_detected",
            "quality_score": None,
            "defects": defects,
            "metadata": metadata or {},
        }
        
        await self.publish(
            event_data,
            key=inspection_id,
            headers={"event_type": "DEFECT_DETECTED"}
        )
        
        self.logger.warning(
            "defect.detected.event.published",
            inspection_id=inspection_id,
            defect_count=len(defects)
        )
    
    async def publish_quality_assessed(
        self,
        inspection_id: str,
        batch_id: str,
        chip_id: str,
        inspection_type: str,
        quality_score: float,
        defects: Optional[list[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """Publish quality assessed event.
        
        Args:
            inspection_id: Unique inspection identifier
            batch_id: Batch identifier
            chip_id: Chip identifier
            inspection_type: Type of inspection
            quality_score: Quality assessment score
            defects: Optional list of defects
            metadata: Optional metadata
        """
        event_data = {
            "event_type": "QUALITY_ASSESSED",
            "inspection_id": inspection_id,
            "batch_id": batch_id,
            "chip_id": chip_id,
            "inspection_type": inspection_type,
            "status": "assessed",
            "quality_score": quality_score,
            "defects": defects or [],
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
            quality_score=quality_score
        )
