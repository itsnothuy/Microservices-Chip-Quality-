"""User event producer for authentication and audit trail."""

from typing import Dict, Any, Optional
from pathlib import Path
import json
import structlog

from events.producers.base_producer import BaseEventProducer
from events.utils.kafka_client import KafkaConfig

logger = structlog.get_logger(__name__)


class UserEventProducer(BaseEventProducer):
    """Producer for user activity events."""
    
    TOPIC = "chip-quality.user.events"
    
    def __init__(self, config: Optional[KafkaConfig] = None):
        """Initialize user event producer."""
        schema_path = Path(__file__).parent.parent / "schemas" / "user.avsc"
        with open(schema_path, "r") as f:
            schema = json.load(f)
        
        super().__init__(
            topic=self.TOPIC,
            schema=schema,
            config=config
        )
        self.logger = logger.bind(producer="user")
    
    async def publish_user_login(
        self,
        user_id: str,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """Publish user login event."""
        event_data = {
            "event_type": "USER_LOGIN",
            "user_id": user_id,
            "username": username,
            "action": "login",
            "resource": None,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "success": success,
            "metadata": metadata or {},
        }
        
        await self.publish(
            event_data,
            key=user_id,
            headers={"event_type": "USER_LOGIN"}
        )
        
        self.logger.info(
            "user.login.event.published",
            user_id=user_id,
            success=success
        )
    
    async def publish_audit_action(
        self,
        user_id: str,
        action: str,
        resource: Optional[str] = None,
        ip_address: Optional[str] = None,
        success: bool = True,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """Publish audit action event."""
        event_data = {
            "event_type": "AUDIT_ACTION",
            "user_id": user_id,
            "username": None,
            "action": action,
            "resource": resource,
            "ip_address": ip_address,
            "user_agent": None,
            "success": success,
            "metadata": metadata or {},
        }
        
        await self.publish(
            event_data,
            key=user_id,
            headers={"event_type": "AUDIT_ACTION"}
        )
        
        self.logger.info(
            "audit.action.event.published",
            user_id=user_id,
            action=action,
            resource=resource
        )
