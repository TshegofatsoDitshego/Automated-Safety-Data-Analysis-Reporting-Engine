"""
Reports API endpoints
Handles compliance report generation and retrieval
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import logging
import os

from app.core.database import get_db
from app.models.database import ComplianceReport
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class ReportRequest(BaseModel):
    """Schema for report generation request"""
    report_type: str
    period_start: datetime
    period_end: datetime
    equipment_ids: Optional[List[str]] = None
    include_charts: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "report_type": "compliance_summary",
                "period_start": "2024-01-01T00:00:00Z",
                "period_end": "2024-01-31T23:59:59Z",
                "equipment_ids": ["GAS-001", "TEMP-001"],
                "include_charts": True
            }
        }


class ReportResponse(BaseModel):
    """Schema for report information"""
    report_id: int
    report_type: str
    period_start: datetime
    period_end: datetime
    generated_at: datetime
    file_path: Optional[str]
    summary: dict
    
    class Config:
        from_attributes = True


@router.post("/generate", response_model=ReportResponse, status_code=202)
async def generate_report(
    request: ReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generate a compliance report
    
    Report generation happens in background
    Returns immediately with report_id to check status
    
    - **report_type**: Type of report (compliance_summary, equipment_performance, alert_summary)
    - **period_start**: Start of reporting period
    - **period_end**: End of reporting period
    - **equipment_ids**: Optional list of specific equipment to include
    """
    try:
        # Validate date range
        if request.period_end <= request.period_start:
            raise HTTPException(
                status_code=400,
                detail="period_end must be after period_start"
            )
        
        # Create report record
        report = ComplianceReport(
            report_type=request.report_type,
            period_start=request.period_start,
            period_end=request.period_end,
            summary={"status": "pending"}
        )
        
        db.add(report)
        db.commit()
        db.refresh(report)
        
        # Queue report generation as background task
        background_tasks.add_task(
            generate_report_task,
            report.report_id,
            request.model_dump()
        )
        
        logger.info(f"Queued report generation: {report.report_id}")
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report generation request error: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[ReportResponse])
async def list_reports(
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List generated reports
    
    Returns metadata about available reports
    Use the download endpoint to get actual report files
    """
    try:
        query = db.query(ComplianceReport)
        
        if report_type:
            query = query.filter(ComplianceReport.report_type == report_type)
        
        reports = query.order_by(
            ComplianceReport.generated_at.desc()
        ).offset(skip).limit(limit).all()
        
        return reports
        
    except Exception as e:
        logger.error(f"Report list error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    db: Session = Depends(get_db)
):
    """
    Get report metadata by ID
    """
    report = db.query(ComplianceReport).filter(
        ComplianceReport.report_id == report_id
    ).first()
    
    if not report:
        raise HTTPException(
            status_code=404,
            detail=f"Report {report_id} not found"
        )
    
    return report


@router.get("/{report_id}/download")
async def download_report(
    report_id: int,
    db: Session = Depends(get_db)
):
    """
    Download the generated report file
    
    Returns PDF file for download
    """
    report = db.query(ComplianceReport).filter(
        ComplianceReport.report_id == report_id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if not report.file_path:
        raise HTTPException(
            status_code=404,
            detail="Report file not available yet. Check report status."
        )
    
    file_path = os.path.join(settings.REPORTS_OUTPUT_DIR, report.file_path)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail="Report file not found on disk"
        )
    
    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type="application/pdf"
    )


@router.delete("/{report_id}")
async def delete_report(
    report_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a report and its associated file
    """
    try:
        report = db.query(ComplianceReport).filter(
            ComplianceReport.report_id == report_id
        ).first()
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Delete file if exists
        if report.file_path:
            file_path = os.path.join(settings.REPORTS_OUTPUT_DIR, report.file_path)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Delete database record
        db.delete(report)
        db.commit()
        
        logger.info(f"Deleted report: {report_id}")
        
        return {"message": f"Report {report_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report deletion error: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


def generate_report_task(report_id: int, request_data: dict):
    """
    Background task to generate PDF report
    This is a simplified version - production would be more comprehensive
    """
    from app.core.database import get_db_context
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from sqlalchemy import text
    import json
    
    try:
        with get_db_context() as db:
            # Get report record
            report = db.query(ComplianceReport).filter(
                ComplianceReport.report_id == report_id
            ).first()
            
            if not report:
                logger.error(f"Report {report_id} not found")
                return
            
            # Ensure output directory exists
            os.makedirs(settings.REPORTS_OUTPUT_DIR, exist_ok=True)
            
            # Generate filename
            filename = f"report_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            file_path = os.path.join(settings.REPORTS_OUTPUT_DIR, filename)
            
            # Create PDF
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()
            
            # Title
            title = Paragraph(f"<b>{request_data['report_type'].replace('_', ' ').title()}</b>", styles['Title'])
            elements.append(title)
            elements.append(Spacer(1, 12))
            
            # Report period
            period_text = f"Period: {request_data['period_start']} to {request_data['period_end']}"
            elements.append(Paragraph(period_text, styles['Normal']))
            elements.append(Spacer(1, 12))
            
            # Get data from database
            query = text("""
                SELECT 
                    e.equipment_id,
                    e.equipment_type,
                    COUNT(sr.time) as reading_count,
                    COUNT(DISTINCT DATE(sr.time)) as active_days,
                    AVG(sr.metric_value) as avg_value
                FROM equipment e
                LEFT JOIN sensor_readings sr ON e.equipment_id = sr.equipment_id
                WHERE sr.time BETWEEN :start_date AND :end_date
                GROUP BY e.equipment_id, e.equipment_type
                ORDER BY reading_count DESC
                LIMIT 20
            """)
            
            result = db.execute(
                query,
                {
                    "start_date": request_data['period_start'],
                    "end_date": request_data['period_end']
                }
            )
            
            data = [["Equipment ID", "Type", "Readings", "Active Days", "Avg Value"]]
            total_readings = 0
            
            for row in result:
                data.append([
                    row.equipment_id,
                    row.equipment_type,
                    str(row.reading_count),
                    str(row.active_days),
                    f"{row.avg_value:.2f}" if row.avg_value else "N/A"
                ])
                total_readings += row.reading_count
            
            # Create table
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 24))
            
            # Summary
            summary_text = f"<b>Summary:</b><br/>Total Readings: {total_readings}<br/>Equipment Monitored: {len(data)-1}"
            elements.append(Paragraph(summary_text, styles['Normal']))
            
            # Build PDF
            doc.build(elements)
            
            # Update report record
            report.file_path = filename
            report.summary = {
                "status": "completed",
                "total_readings": total_readings,
                "equipment_count": len(data) - 1
            }
            db.commit()
            
            logger.info(f"Report {report_id} generated successfully: {filename}")
            
    except Exception as e:
        logger.error(f"Report generation task failed: {e}", exc_info=True)
        
        # Update report status to failed
        try:
            with get_db_context() as db:
                report = db.query(ComplianceReport).filter(
                    ComplianceReport.report_id == report_id
                ).first()
                
                if report:
                    report.summary = {"status": "failed", "error": str(e)}
                    db.commit()
        except:
            pass