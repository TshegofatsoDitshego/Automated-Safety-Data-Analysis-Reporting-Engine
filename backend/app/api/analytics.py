"""
Analytics API endpoints
Provides access to anomaly detection, trend analysis, and predictive insights
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import logging

from app.core.database import get_db
from app.services.analytics import AnalyticsEngine

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/anomalies/{equipment_id}")
async def detect_anomalies(
    equipment_id: str,
    metric_name: str = Query(..., description="Metric to analyze"),
    lookback_hours: int = Query(24, ge=1, le=168, description="Hours of data to analyze (1-168)"),
    db: Session = Depends(get_db)
):
    """
    Detect anomalies in sensor readings using ML
    
    Uses Isolation Forest algorithm to identify unusual patterns
    Returns detected anomalies with severity scores
    
    - **equipment_id**: Equipment to analyze
    - **metric_name**: Specific metric to check (e.g., 'gas_concentration')
    - **lookback_hours**: How many hours of historical data to analyze
    """
    try:
        analytics = AnalyticsEngine(db)
        anomalies = analytics.detect_anomalies(
            equipment_id=equipment_id,
            metric_name=metric_name,
            lookback_hours=lookback_hours
        )
        
        return {
            "equipment_id": equipment_id,
            "metric_name": metric_name,
            "lookback_hours": lookback_hours,
            "anomalies_detected": len(anomalies),
            "anomalies": anomalies
        }
        
    except Exception as e:
        logger.error(f"Anomaly detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/thresholds/{equipment_id}")
async def check_thresholds(
    equipment_id: str,
    lookback_minutes: int = Query(30, ge=1, le=1440, description="Minutes to check (1-1440)"),
    db: Session = Depends(get_db)
):
    """
    Check for threshold violations
    
    Faster than ML-based anomaly detection
    Good for real-time monitoring
    
    - **equipment_id**: Equipment to check
    - **lookback_minutes**: Recent time window to check
    """
    try:
        analytics = AnalyticsEngine(db)
        violations = analytics.check_thresholds(
            equipment_id=equipment_id,
            lookback_minutes=lookback_minutes
        )
        
        return {
            "equipment_id": equipment_id,
            "lookback_minutes": lookback_minutes,
            "violations_detected": len(violations),
            "violations": violations
        }
        
    except Exception as e:
        logger.error(f"Threshold check error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/{equipment_id}")
async def analyze_trends(
    equipment_id: str,
    metric_name: str = Query(..., description="Metric to analyze"),
    period_days: int = Query(30, ge=1, le=365, description="Days of data to analyze (1-365)"),
    db: Session = Depends(get_db)
):
    """
    Analyze historical trends
    
    Identifies patterns, volatility, and changes over time
    Useful for understanding equipment behavior
    
    - **equipment_id**: Equipment to analyze
    - **metric_name**: Specific metric to analyze
    - **period_days**: Historical period to analyze
    """
    try:
        analytics = AnalyticsEngine(db)
        trends = analytics.analyze_trends(
            equipment_id=equipment_id,
            metric_name=metric_name,
            period_days=period_days
        )
        
        if "error" in trends:
            raise HTTPException(status_code=400, detail=trends["error"])
        
        return trends
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trend analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/maintenance/{equipment_id}")
async def predict_maintenance(
    equipment_id: str,
    db: Session = Depends(get_db)
):
    """
    Predict maintenance needs
    
    Analyzes equipment usage, alerts, and calibration history
    to predict when maintenance might be needed
    
    - **equipment_id**: Equipment to analyze
    """
    try:
        analytics = AnalyticsEngine(db)
        prediction = analytics.predict_maintenance(equipment_id)
        
        if "error" in prediction:
            raise HTTPException(status_code=400, detail=prediction["error"])
        
        return prediction
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Maintenance prediction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/{equipment_id}")
async def get_dashboard_data(
    equipment_id: str,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive dashboard data for equipment
    
    Combines multiple analytics endpoints into single response
    Optimized for dashboard views
    
    - **equipment_id**: Equipment to get data for
    """
    try:
        from sqlalchemy import text
        from datetime import timedelta, datetime
        
        analytics = AnalyticsEngine(db)
        
        # Get recent readings summary
        query = text("""
            SELECT 
                metric_name,
                COUNT(*) as reading_count,
                AVG(metric_value) as avg_value,
                MIN(metric_value) as min_value,
                MAX(metric_value) as max_value,
                MAX(time) as last_reading_time
            FROM sensor_readings
            WHERE equipment_id = :equipment_id
              AND time > :cutoff_time
            GROUP BY metric_name
        """)
        
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        result = db.execute(query, {"equipment_id": equipment_id, "cutoff_time": cutoff_time})
        
        readings_summary = [
            {
                "metric_name": row.metric_name,
                "reading_count": row.reading_count,
                "avg_value": float(row.avg_value),
                "min_value": float(row.min_value),
                "max_value": float(row.max_value),
                "last_reading_time": row.last_reading_time
            }
            for row in result
        ]
        
        # Get recent alerts
        from app.models.database import Alert
        recent_alerts = db.query(Alert).filter(
            Alert.equipment_id == equipment_id,
            Alert.triggered_at > cutoff_time
        ).order_by(Alert.triggered_at.desc()).limit(10).all()
        
        alerts_data = [
            {
                "alert_id": alert.alert_id,
                "alert_type": alert.alert_type,
                "severity": alert.severity.value,
                "message": alert.message,
                "triggered_at": alert.triggered_at,
                "resolved_at": alert.resolved_at
            }
            for alert in recent_alerts
        ]
        
        # Get maintenance prediction
        maintenance = analytics.predict_maintenance(equipment_id)
        
        return {
            "equipment_id": equipment_id,
            "readings_summary": readings_summary,
            "recent_alerts": alerts_data,
            "maintenance_prediction": maintenance,
            "generated_at": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Dashboard data error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))