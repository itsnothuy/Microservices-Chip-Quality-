"""
Notification service for alerts and updates.

Handles notifications for quality alerts, inspection updates, and stakeholder communications.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
import uuid
from datetime import datetime

import structlog


logger = structlog.get_logger()


class NotificationType(str, Enum):
    """Types of notifications"""
    INSPECTION_CREATED = "inspection_created"
    INSPECTION_COMPLETED = "inspection_completed"
    INSPECTION_FAILED = "inspection_failed"
    QUALITY_ALERT = "quality_alert"
    DEFECT_DETECTED = "defect_detected"
    CRITICAL_DEFECT = "critical_defect"
    THRESHOLD_VIOLATION = "threshold_violation"
    REVIEW_REQUIRED = "review_required"


class NotificationPriority(str, Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class Notification:
    """Notification data structure"""
    
    def __init__(
        self,
        notification_type: NotificationType,
        priority: NotificationPriority,
        title: str,
        message: str,
        data: Dict[str, Any],
        recipients: Optional[List[str]] = None
    ):
        self.id = uuid.uuid4()
        self.notification_type = notification_type
        self.priority = priority
        self.title = title
        self.message = message
        self.data = data
        self.recipients = recipients or []
        self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "type": self.notification_type.value,
            "priority": self.priority.value,
            "title": self.title,
            "message": self.message,
            "data": self.data,
            "recipients": self.recipients,
            "created_at": self.created_at.isoformat()
        }


class NotificationService:
    """
    Notification and alert service.
    
    Features:
    - Quality alert generation
    - Inspection status notifications
    - Email/SMS/webhook integration
    - Alert escalation
    - Notification history
    """
    
    def __init__(self):
        self._notifications: List[Notification] = []
    
    async def send_inspection_created(
        self,
        inspection_id: uuid.UUID,
        lot_id: uuid.UUID,
        inspection_type: str,
        recipients: Optional[List[str]] = None
    ) -> Notification:
        """
        Send notification for new inspection.
        
        Args:
            inspection_id: Inspection UUID
            lot_id: Lot UUID
            inspection_type: Type of inspection
            recipients: Optional recipient list
            
        Returns:
            Created notification
        """
        notification = Notification(
            notification_type=NotificationType.INSPECTION_CREATED,
            priority=NotificationPriority.NORMAL,
            title="New Inspection Created",
            message=f"Inspection {inspection_id} created for lot {lot_id}",
            data={
                "inspection_id": str(inspection_id),
                "lot_id": str(lot_id),
                "inspection_type": inspection_type
            },
            recipients=recipients
        )
        
        await self._send(notification)
        return notification
    
    async def send_inspection_completed(
        self,
        inspection_id: uuid.UUID,
        quality_score: float,
        passed: bool,
        recipients: Optional[List[str]] = None
    ) -> Notification:
        """
        Send notification for completed inspection.
        
        Args:
            inspection_id: Inspection UUID
            quality_score: Quality score
            passed: Pass/fail status
            recipients: Optional recipient list
            
        Returns:
            Created notification
        """
        priority = NotificationPriority.NORMAL if passed else NotificationPriority.HIGH
        
        notification = Notification(
            notification_type=NotificationType.INSPECTION_COMPLETED,
            priority=priority,
            title=f"Inspection {'Passed' if passed else 'Failed'}",
            message=f"Inspection {inspection_id} completed with score {quality_score:.2f}",
            data={
                "inspection_id": str(inspection_id),
                "quality_score": quality_score,
                "passed": passed
            },
            recipients=recipients
        )
        
        await self._send(notification)
        return notification
    
    async def send_quality_alert(
        self,
        inspection_id: uuid.UUID,
        alert_type: str,
        details: Dict[str, Any],
        recipients: Optional[List[str]] = None
    ) -> Notification:
        """
        Send quality alert notification.
        
        Args:
            inspection_id: Inspection UUID
            alert_type: Type of alert
            details: Alert details
            recipients: Optional recipient list
            
        Returns:
            Created notification
        """
        notification = Notification(
            notification_type=NotificationType.QUALITY_ALERT,
            priority=NotificationPriority.HIGH,
            title=f"Quality Alert: {alert_type}",
            message=f"Quality issue detected in inspection {inspection_id}",
            data={
                "inspection_id": str(inspection_id),
                "alert_type": alert_type,
                "details": details
            },
            recipients=recipients
        )
        
        await self._send(notification)
        return notification
    
    async def send_critical_defect_alert(
        self,
        inspection_id: uuid.UUID,
        defect_id: uuid.UUID,
        defect_type: str,
        recipients: Optional[List[str]] = None
    ) -> Notification:
        """
        Send critical defect alert.
        
        Args:
            inspection_id: Inspection UUID
            defect_id: Defect UUID
            defect_type: Type of defect
            recipients: Optional recipient list
            
        Returns:
            Created notification
        """
        notification = Notification(
            notification_type=NotificationType.CRITICAL_DEFECT,
            priority=NotificationPriority.CRITICAL,
            title="Critical Defect Detected",
            message=f"Critical {defect_type} defect detected in inspection {inspection_id}",
            data={
                "inspection_id": str(inspection_id),
                "defect_id": str(defect_id),
                "defect_type": defect_type
            },
            recipients=recipients
        )
        
        await self._send(notification)
        return notification
    
    async def send_review_required(
        self,
        inspection_id: uuid.UUID,
        reason: str,
        recipients: Optional[List[str]] = None
    ) -> Notification:
        """
        Send review required notification.
        
        Args:
            inspection_id: Inspection UUID
            reason: Reason for review
            recipients: Optional recipient list
            
        Returns:
            Created notification
        """
        notification = Notification(
            notification_type=NotificationType.REVIEW_REQUIRED,
            priority=NotificationPriority.HIGH,
            title="Manual Review Required",
            message=f"Inspection {inspection_id} requires manual review: {reason}",
            data={
                "inspection_id": str(inspection_id),
                "reason": reason
            },
            recipients=recipients
        )
        
        await self._send(notification)
        return notification
    
    async def _send(self, notification: Notification) -> None:
        """
        Send notification through configured channels.
        
        In production, this would integrate with:
        - Email service (SendGrid, SES, etc.)
        - SMS service (Twilio, SNS, etc.)
        - Webhook delivery
        - Kafka event publishing
        - In-app notification system
        """
        self._notifications.append(notification)
        
        logger.info(
            "Notification sent",
            notification_id=str(notification.id),
            type=notification.notification_type.value,
            priority=notification.priority.value,
            recipients=notification.recipients
        )
    
    def get_recent_notifications(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent notifications"""
        return [n.to_dict() for n in self._notifications[-limit:]]
