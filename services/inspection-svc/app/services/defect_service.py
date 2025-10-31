"""
Defect detection and management service.

Handles defect creation, classification, review, and tracking.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import structlog
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from services.shared.database.enums import (
    DefectSeverityEnum,
    DefectTypeEnum,
    DetectionMethodEnum,
)
from services.shared.models.inspection import Defect, Inspection

from ..core.exceptions import (
    DefectNotFoundError,
    InspectionNotFoundError,
    ValidationError,
)

logger = structlog.get_logger()


class DefectService:
    """
    Defect detection and classification service.
    
    Features:
    - Defect creation from ML inference
    - Manual defect entry
    - Defect review and validation
    - False positive marking
    - Defect pattern analysis
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create_defect(
        self,
        inspection_id: uuid.UUID,
        defect_type: DefectTypeEnum,
        severity: DefectSeverityEnum,
        confidence: Decimal,
        location: Dict[str, Any],
        detection_method: DetectionMethodEnum = DetectionMethodEnum.ML_AUTOMATED,
        description: Optional[str] = None,
        characteristics: Optional[Dict[str, Any]] = None,
        dimensions: Optional[Dict[str, Any]] = None
    ) -> Defect:
        """
        Create a new defect record.
        
        Args:
            inspection_id: Parent inspection UUID
            defect_type: Type of defect
            severity: Severity level
            confidence: ML confidence score (0-1)
            location: Spatial location data (x, y, width, height)
            detection_method: How defect was detected
            description: Optional description
            characteristics: Additional characteristics
            dimensions: Defect dimensions
            
        Returns:
            Created defect instance
            
        Raises:
            InspectionNotFoundError: If inspection not found
            ValidationError: If validation fails
        """
        logger.info(
            "Creating defect",
            inspection_id=str(inspection_id),
            defect_type=defect_type.value,
            severity=severity.value,
            confidence=float(confidence)
        )
        
        # Validate inspection exists
        await self._validate_inspection_exists(inspection_id)
        
        # Validate confidence score
        if not 0 <= confidence <= 1:
            raise ValidationError("Confidence must be between 0 and 1", {"confidence": float(confidence)})
        
        # Validate location data
        self._validate_location(location)
        
        # Generate defect ID
        defect_id = self._generate_defect_id(defect_type)
        
        # Calculate affected area
        affected_area = self._calculate_affected_area(location, dimensions)
        
        # Create defect
        defect = Defect(
            defect_id=defect_id,
            inspection_id=inspection_id,
            defect_type=defect_type,
            severity=severity,
            detection_method=detection_method,
            confidence_score=confidence,
            location_data=location,
            characteristics=characteristics or {},
            dimensions=dimensions,
            affected_area=affected_area,
            is_confirmed=False,
            is_false_positive=False
        )
        
        self.db.add(defect)
        await self.db.commit()
        await self.db.refresh(defect)
        
        logger.info(
            "Defect created",
            defect_id=defect.defect_id,
            id=str(defect.id),
            inspection_id=str(inspection_id)
        )
        
        return defect
    
    async def get_defect(self, defect_id: uuid.UUID) -> Defect:
        """
        Get defect by ID.
        
        Args:
            defect_id: Defect UUID
            
        Returns:
            Defect instance
            
        Raises:
            DefectNotFoundError: If defect not found
        """
        query = select(Defect).where(Defect.id == defect_id)
        result = await self.db.execute(query)
        defect = result.scalar_one_or_none()
        
        if not defect:
            raise DefectNotFoundError(str(defect_id))
        
        return defect
    
    async def list_defects(
        self,
        inspection_id: Optional[uuid.UUID] = None,
        severity: Optional[DefectSeverityEnum] = None,
        defect_type: Optional[DefectTypeEnum] = None,
        is_confirmed: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Defect]:
        """
        List defects with filtering.
        
        Args:
            inspection_id: Filter by inspection
            severity: Filter by severity
            defect_type: Filter by type
            is_confirmed: Filter by confirmation status
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of defects
        """
        query = select(Defect)
        
        filters = []
        if inspection_id:
            filters.append(Defect.inspection_id == inspection_id)
        if severity:
            filters.append(Defect.severity == severity)
        if defect_type:
            filters.append(Defect.defect_type == defect_type)
        if is_confirmed is not None:
            filters.append(Defect.is_confirmed == is_confirmed)
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.order_by(Defect.created_at.desc()).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def confirm_defect(
        self,
        defect_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        notes: Optional[str] = None
    ) -> Defect:
        """
        Confirm a defect (human review).
        
        Args:
            defect_id: Defect UUID
            reviewer_id: Reviewer user ID
            notes: Optional review notes
            
        Returns:
            Updated defect
        """
        defect = await self.get_defect(defect_id)
        
        defect.is_confirmed = True
        defect.reviewed_by = reviewer_id
        defect.reviewed_at = datetime.utcnow()
        
        if notes:
            defect.review_notes = notes
        
        await self.db.commit()
        await self.db.refresh(defect)
        
        logger.info(
            "Defect confirmed",
            defect_id=defect.defect_id,
            reviewer_id=str(reviewer_id)
        )
        
        return defect
    
    async def mark_false_positive(
        self,
        defect_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        notes: Optional[str] = None
    ) -> Defect:
        """
        Mark defect as false positive.
        
        Args:
            defect_id: Defect UUID
            reviewer_id: Reviewer user ID
            notes: Optional notes explaining why
            
        Returns:
            Updated defect
        """
        defect = await self.get_defect(defect_id)
        
        defect.is_false_positive = True
        defect.reviewed_by = reviewer_id
        defect.reviewed_at = datetime.utcnow()
        
        if notes:
            defect.review_notes = notes
        
        await self.db.commit()
        await self.db.refresh(defect)
        
        logger.info(
            "Defect marked as false positive",
            defect_id=defect.defect_id,
            reviewer_id=str(reviewer_id)
        )
        
        return defect
    
    async def get_defect_statistics(
        self,
        inspection_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """
        Get defect statistics.
        
        Args:
            inspection_id: Optional inspection ID to filter by
            
        Returns:
            Statistics dictionary
        """
        defects = await self.list_defects(inspection_id=inspection_id, limit=1000)
        
        stats = {
            "total_defects": len(defects),
            "by_severity": {},
            "by_type": {},
            "by_detection_method": {},
            "confirmed_count": sum(1 for d in defects if d.is_confirmed),
            "false_positive_count": sum(1 for d in defects if d.is_false_positive),
            "avg_confidence": float(sum(d.confidence_score for d in defects if d.confidence_score) / len(defects)) if defects else 0.0
        }
        
        # Count by severity
        for defect in defects:
            severity_key = defect.severity.value
            stats["by_severity"][severity_key] = stats["by_severity"].get(severity_key, 0) + 1
            
            type_key = defect.defect_type.value
            stats["by_type"][type_key] = stats["by_type"].get(type_key, 0) + 1
            
            method_key = defect.detection_method.value
            stats["by_detection_method"][method_key] = stats["by_detection_method"].get(method_key, 0) + 1
        
        return stats
    
    def _generate_defect_id(self, defect_type: DefectTypeEnum) -> str:
        """Generate unique defect ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        type_prefix = defect_type.value[:3].upper()
        return f"DEF-{type_prefix}-{timestamp}-{uuid.uuid4().hex[:6]}"
    
    def _validate_location(self, location: Dict[str, Any]) -> None:
        """Validate location data has required fields"""
        required_fields = ['x', 'y', 'width', 'height']
        
        for field in required_fields:
            if field not in location:
                raise ValidationError(
                    f"Location must contain '{field}' field",
                    {"missing_field": field}
                )
    
    def _calculate_affected_area(
        self,
        location: Dict[str, Any],
        dimensions: Optional[Dict[str, Any]]
    ) -> Optional[Decimal]:
        """Calculate affected area from location and dimensions"""
        try:
            width = location.get('width', 0)
            height = location.get('height', 0)
            
            if width and height:
                return Decimal(str(width * height))
        except (ValueError, TypeError):
            pass
        
        return None
    
    async def _validate_inspection_exists(self, inspection_id: uuid.UUID) -> None:
        """Validate that inspection exists"""
        query = select(Inspection).where(Inspection.id == inspection_id)
        result = await self.db.execute(query)
        inspection = result.scalar_one_or_none()
        
        if not inspection:
            raise InspectionNotFoundError(str(inspection_id))
