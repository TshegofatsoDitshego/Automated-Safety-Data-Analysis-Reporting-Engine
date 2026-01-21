"""
Data ingestion API endpoints
Handles incoming sensor data from IoT devices
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from app.core.database import get_db
from app.services.ingestion import DataIngestionPipeline

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic schemas for request validation
class SensorReadingInput(BaseModel):
    """Schema for a single sensor reading"""
    equipment_id: str = Field(..., description="Unique equipment identifier")
    metric_name: str = Field(..., description="Name of the metric being measured")
    metric_value: float = Field(..., description="Measured value")
    metric_unit: str = Field(None, description="Unit of measurement")
    time: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of reading")
    reading_status: str = Field(default="normal", description="Status: normal, warning, critical, offline")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "equipment_id": "GAS-001",
                "metric_name": "gas_concentration",
                "metric_value": 8.5,
                "metric_unit": "ppm",
                "time": "2024-01-20T10:30:00Z",
                "reading_status": "normal",
                "metadata": {
                    "battery_level": 85,
                    "signal_strength": -65
                }
            }
        }


class BatchIngestionRequest(BaseModel):
    """Schema for batch ingestion"""
    readings: List[SensorReadingInput] = Field(..., description="List of sensor readings")
    source: str = Field(default="api", description="Data source identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "readings": [
                    {
                        "equipment_id": "GAS-001",
                        "metric_name": "gas_concentration",
                        "metric_value": 8.5,
                        "metric_unit": "ppm",
                        "time": "2024-01-20T10:30:00Z"
                    },
                    {
                        "equipment_id": "TEMP-001",
                        "metric_name": "temperature",
                        "metric_value": 42.3,
                        "metric_unit": "celsius",
                        "time": "2024-01-20T10:30:00Z"
                    }
                ],
                "source": "sensor_gateway_01"
            }
        }


class IngestionResponse(BaseModel):
    """Response schema for ingestion operations"""
    success: bool
    total_received: int
    total_inserted: int
    invalid_count: int
    duplicate_count: int
    late_arrival_count: int
    processing_time_ms: int
    message: str


@router.post("/batch", response_model=IngestionResponse)
async def ingest_batch(
    request: BatchIngestionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Ingest a batch of sensor readings
    
    This is the main endpoint for IoT devices to send data
    Handles validation, deduplication, and quality checks
    
    - **readings**: List of sensor readings to ingest
    - **source**: Optional identifier for the data source
    """
    try:
        # Convert Pydantic models to dicts for processing
        readings_data = [reading.model_dump() for reading in request.readings]
        
        # Initialize ingestion pipeline
        pipeline = DataIngestionPipeline(db)
        
        # Process the batch
        result = pipeline.ingest_batch(readings_data)
        
        # Add background task to check for alerts if needed
        if result.get("success"):
            background_tasks.add_task(
                check_threshold_violations,
                db,
                readings_data
            )
        
        # Prepare response
        if result.get("success"):
            return IngestionResponse(
                success=True,
                total_received=result["total_received"],
                total_inserted=result["total_inserted"],
                invalid_count=result["invalid_count"],
                duplicate_count=result["duplicate_count"],
                late_arrival_count=result["late_arrival_count"],
                processing_time_ms=result["processing_time_ms"],
                message=f"Successfully processed {result['total_inserted']} readings"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Ingestion failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        logger.error(f"Ingestion endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/single")
async def ingest_single(
    reading: SensorReadingInput,
    db: Session = Depends(get_db)
):
    """
    Ingest a single sensor reading
    
    Convenience endpoint for testing or low-frequency sensors
    For high-volume ingestion, use the batch endpoint
    """
    try:
        pipeline = DataIngestionPipeline(db)
        result = pipeline.ingest_batch([reading.model_dump()])
        
        if result.get("success"):
            return {
                "success": True,
                "message": "Reading ingested successfully",
                "processing_time_ms": result["processing_time_ms"]
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Ingestion failed")
            )
            
    except Exception as e:
        logger.error(f"Single ingestion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_ingestion_stats(
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """
    Get ingestion pipeline statistics
    
    Returns data quality metrics for the specified time period
    Useful for monitoring pipeline health
    """
    try:
        from datetime import timedelta
        from sqlalchemy import func, text
        from app.models.database import DataQualityMetric
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Get quality metrics from the last N hours
        metrics = db.query(DataQualityMetric).filter(
            DataQualityMetric.check_timestamp > cutoff_time
        ).all()
        
        if not metrics:
            return {
                "period_hours": hours,
                "total_records": 0,
                "message": "No data available for this period"
            }
        
        # Aggregate statistics
        total_processed = sum(m.total_records_processed for m in metrics)
        total_invalid = sum(m.invalid_records for m in metrics)
        total_duplicates = sum(m.duplicate_records for m in metrics)
        total_late = sum(m.late_arriving_records for m in metrics)
        avg_processing_time = sum(m.processing_time_ms for m in metrics) / len(metrics)
        
        return {
            "period_hours": hours,
            "total_records_processed": total_processed,
            "invalid_records": total_invalid,
            "duplicate_records": total_duplicates,
            "late_arrivals": total_late,
            "invalid_rate": total_invalid / max(total_processed, 1),
            "duplicate_rate": total_duplicates / max(total_processed, 1),
            "average_processing_time_ms": avg_processing_time,
            "data_quality_score": calculate_quality_score(
                total_invalid, total_duplicates, total_processed
            )
        }
        
    except Exception as e:
        logger.error(f"Stats endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def check_threshold_violations(db: Session, readings: List[Dict]):
    """
    Background task to check for threshold violations
    Generates alerts if needed
    """
    try:
        from app.services.analytics import AnalyticsEngine
        from app.models.database import Alert, AlertSeverity
        
        analytics = AnalyticsEngine(db)
        
        # Get unique equipment IDs from batch
        equipment_ids = set(r["equipment_id"] for r in readings)
        
        for equipment_id in equipment_ids:
            # Check thresholds
            violations = analytics.check_thresholds(equipment_id, lookback_minutes=5)
            
            # Create alerts for violations
            for violation in violations:
                alert = Alert(
                    equipment_id=equipment_id,
                    alert_type="threshold_violation",
                    severity=violation["severity"],
                    message=f"{violation['metric_name']} exceeded threshold: "
                           f"{violation['metric_value']} {violation.get('metric_unit', '')} "
                           f"(threshold: {violation['threshold']})",
                    metadata=violation
                )
                db.add(alert)
            
        db.commit()
        logger.info(f"Checked thresholds for {len(equipment_ids)} equipment")
        
    except Exception as e:
        logger.error(f"Threshold check task failed: {e}", exc_info=True)
        db.rollback()


def calculate_quality_score(invalid: int, duplicates: int, total: int) -> float:
    """
    Calculate overall data quality score (0-100)
    Higher is better
    """
    if total == 0:
        return 0.0
    
    invalid_rate = invalid / total
    duplicate_rate = duplicates / total
    
    # Penalize invalid and duplicate data
    score = 100 - (invalid_rate * 50) - (duplicate_rate * 30)
    
    return max(0.0, min(100.0, score))