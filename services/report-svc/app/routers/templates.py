"""
Report template management API endpoints.
"""

from typing import Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.schemas.report import ReportTemplateSchema, ReportTemplateListResponse

logger = structlog.get_logger()
router = APIRouter()


@router.get("/", response_model=ReportTemplateListResponse)
async def list_templates(
    db: AsyncSession = Depends(get_db_session),
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    active_only: bool = Query(default=True, description="Show only active templates")
):
    """
    List available report templates.
    
    - **report_type**: Filter by report type (optional)
    - **active_only**: Show only active templates
    """
    logger.info(
        "Listing report templates",
        report_type=report_type,
        active_only=active_only
    )
    
    # For now, return mock templates
    # In production, this would query the database
    mock_templates = []
    
    return ReportTemplateListResponse(
        templates=mock_templates,
        total=len(mock_templates)
    )


@router.get("/{template_id}", response_model=ReportTemplateSchema)
async def get_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get template details by ID.
    
    - **template_id**: UUID of the template
    """
    logger.info(
        "Getting template details",
        template_id=str(template_id)
    )
    
    # For now, raise not implemented
    # In production, this would query the database
    from fastapi import HTTPException
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Template retrieval not yet implemented"
    )
