"""Report endpoints - proxy to report service"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import structlog

from app.core.auth import User, get_current_user, require_report_read
from app.core.http_client import get_report_client
from app.core.rate_limiting import get_limiter


logger = structlog.get_logger()
router = APIRouter()
limiter = get_limiter()


class ReportRequest(BaseModel):
    """Report generation request"""
    report_type: str = Field(..., description="Type of report (batch_summary, quality_trends, etc.)")
    date_range: Dict[str, date] = Field(..., description="Date range for report")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Additional filters")
    format: str = Field(default="pdf", description="Output format (pdf, excel, csv)")
    include_charts: bool = Field(default=True, description="Include charts and visualizations")


class ReportResponse(BaseModel):
    """Report response model"""
    id: str
    report_type: str
    status: str
    date_range: Dict[str, date]
    filters: Dict[str, Any]
    format: str
    file_size: Optional[int]
    download_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    expires_at: Optional[datetime]


class ReportTemplate(BaseModel):
    """Report template information"""
    name: str
    description: str
    report_type: str
    supported_formats: List[str]
    parameters: Dict[str, Any]
    sample_filters: Dict[str, Any]


@router.post("/", response_model=ReportResponse)
@limiter.limit("10/minute")
async def create_report(
    request: Request,
    report_request: ReportRequest,
    current_user: User = Depends(require_report_read),
    report_client = Depends(get_report_client)
):
    """Generate new report"""
    
    try:
        # Forward request to report service
        response = await report_client.post(
            "/api/v1/reports",
            json=report_request.model_dump(),
            headers={
                "X-User-ID": current_user.id,
                "X-User-Scopes": ",".join(current_user.scopes)
            }
        )
        
        if response.status_code == 201:
            logger.info(
                "Report generation started",
                report_id=response.json().get("id"),
                report_type=report_request.report_type,
                format=report_request.format,
                user_id=current_user.id
            )
            return response.json()
        else:
            logger.error(
                "Failed to create report",
                status_code=response.status_code,
                response=response.text,
                report_type=report_request.report_type
            )
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to create report: {response.text}"
            )
            
    except Exception as e:
        logger.error(
            "Error creating report",
            error=str(e),
            report_type=report_request.report_type,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while creating report"
        )


@router.get("/", response_model=List[ReportResponse])
@limiter.limit("30/minute")
async def list_reports(
    request: Request,
    limit: int = Query(default=50, le=100, description="Number of reports to return"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    status: Optional[str] = Query(None, description="Filter by status"),
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    format: Optional[str] = Query(None, description="Filter by format"),
    current_user: User = Depends(require_report_read),
    report_client = Depends(get_report_client)
):
    """List reports with filtering and pagination"""
    
    try:
        # Build query parameters
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if status:
            params["status"] = status
        if report_type:
            params["report_type"] = report_type
        if format:
            params["format"] = format
        
        # Forward request to report service
        response = await report_client.get(
            "/api/v1/reports",
            params=params,
            headers={
                "X-User-ID": current_user.id,
                "X-User-Scopes": ",".join(current_user.scopes)
            }
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to list reports: {response.text}"
            )
            
    except Exception as e:
        logger.error("Error listing reports", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=500,
            detail="Internal server error while listing reports"
        )


@router.get("/{report_id}", response_model=ReportResponse)
@limiter.limit("60/minute")
async def get_report(
    report_id: str,
    current_user: User = Depends(require_report_read),
    report_client = Depends(get_report_client)
):
    """Get specific report by ID"""
    
    try:
        response = await report_client.get(
            f"/api/v1/reports/{report_id}",
            headers={
                "X-User-ID": current_user.id,
                "X-User-Scopes": ",".join(current_user.scopes)
            }
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise HTTPException(status_code=404, detail="Report not found")
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to get report: {response.text}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting report",
            report_id=report_id,
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting report"
        )


@router.get("/{report_id}/download")
@limiter.limit("20/minute")
async def download_report(
    report_id: str,
    current_user: User = Depends(require_report_read),
    report_client = Depends(get_report_client)
):
    """Download generated report file"""
    
    try:
        response = await report_client.get(
            f"/api/v1/reports/{report_id}/download",
            headers={
                "X-User-ID": current_user.id,
                "X-User-Scopes": ",".join(current_user.scopes)
            }
        )
        
        if response.status_code == 200:
            # Stream the file content
            async def generate():
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    yield chunk
            
            headers = {
                "Content-Disposition": response.headers.get("Content-Disposition", ""),
                "Content-Type": response.headers.get("Content-Type", "application/octet-stream"),
                "Content-Length": response.headers.get("Content-Length", "")
            }
            
            logger.info(
                "Report downloaded",
                report_id=report_id,
                user_id=current_user.id
            )
            
            return StreamingResponse(
                generate(),
                headers=headers,
                media_type=response.headers.get("Content-Type", "application/octet-stream")
            )
        elif response.status_code == 404:
            raise HTTPException(status_code=404, detail="Report not found")
        elif response.status_code == 409:
            raise HTTPException(status_code=409, detail="Report not ready for download")
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to download report: {response.text}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error downloading report",
            report_id=report_id,
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while downloading report"
        )


@router.delete("/{report_id}")
@limiter.limit("10/minute")
async def delete_report(
    report_id: str,
    current_user: User = Depends(require_report_read),
    report_client = Depends(get_report_client)
):
    """Delete report"""
    
    try:
        response = await report_client.delete(
            f"/api/v1/reports/{report_id}",
            headers={
                "X-User-ID": current_user.id,
                "X-User-Scopes": ",".join(current_user.scopes)
            }
        )
        
        if response.status_code == 204:
            logger.info(
                "Report deleted successfully",
                report_id=report_id,
                user_id=current_user.id
            )
            return {"message": "Report deleted successfully"}
        elif response.status_code == 404:
            raise HTTPException(status_code=404, detail="Report not found")
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to delete report: {response.text}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error deleting report",
            report_id=report_id,
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while deleting report"
        )


@router.get("/templates/", response_model=List[ReportTemplate])
@limiter.limit("30/minute")
async def list_report_templates(
    current_user: User = Depends(require_report_read),
    report_client = Depends(get_report_client)
):
    """List available report templates"""
    
    try:
        response = await report_client.get(
            "/api/v1/templates",
            headers={
                "X-User-ID": current_user.id,
                "X-User-Scopes": ",".join(current_user.scopes)
            }
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to list report templates: {response.text}"
            )
            
    except Exception as e:
        logger.error("Error listing report templates", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=500,
            detail="Internal server error while listing report templates"
        )


@router.get("/templates/{template_name}", response_model=ReportTemplate)
@limiter.limit("60/minute")
async def get_report_template(
    template_name: str,
    current_user: User = Depends(require_report_read),
    report_client = Depends(get_report_client)
):
    """Get report template details"""
    
    try:
        response = await report_client.get(
            f"/api/v1/templates/{template_name}",
            headers={
                "X-User-ID": current_user.id,
                "X-User-Scopes": ",".join(current_user.scopes)
            }
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise HTTPException(status_code=404, detail="Report template not found")
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to get report template: {response.text}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting report template",
            template_name=template_name,
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting report template"
        )