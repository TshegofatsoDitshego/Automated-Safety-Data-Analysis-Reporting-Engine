"""
Analytics engine for safety data processing
Implements anomaly detection, trend analysis, and predictive maintenance
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text, func
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import logging

from app.models.database import (
    SensorReading, Equipment, Alert, AlertSeverity, 
    SensorReadingStatus
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """
    Core analytics engine for processing sensor data
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.scaler = StandardScaler()
    
    def detect_anomalies(
        self, 
        equipment_id: str, 
        metric_name: str,
        lookback_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in sensor readings using Isolation Forest
        
        Args:
            equipment_id: Equipment to analyze
            metric_name: Specific metric to analyze
            lookback_hours: How far back to look for patterns
            
        Returns:
            List of detected anomalies with timestamps and scores
        """
        try:
            # Fetch recent readings
            cutoff_time = datetime.utcnow() - timedelta(hours=lookback_hours)
            
            query = text("""
                SELECT time, metric_value, reading_status
                FROM sensor_readings
                WHERE equipment_id = :equipment_id
                  AND metric_name = :metric_name
                  AND time > :cutoff_time
                ORDER BY time ASC
            """)
            
            result = self.db.execute(
                query,
                {
                    "equipment_id": equipment_id,
                    "metric_name": metric_name,
                    "cutoff_time": cutoff_time
                }
            )
            
            df = pd.DataFrame(result.fetchall(), columns=["time", "metric_value", "reading_status"])
            
            if len(df) < 50:  # need enough data for meaningful analysis
                logger.warning(f"Insufficient data for anomaly detection: {len(df)} points")
                return []
            
            # Prepare features for anomaly detection
            # Using rolling statistics to capture temporal patterns
            df["rolling_mean"] = df["metric_value"].rolling(window=10, min_periods=1).mean()
            df["rolling_std"] = df["metric_value"].rolling(window=10, min_periods=1).std()
            df["rate_of_change"] = df["metric_value"].diff()
            
            # Fill NaN values
            df = df.fillna(method="bfill").fillna(method="ffill")
            
            # Select features for model
            features = df[["metric_value", "rolling_mean", "rolling_std", "rate_of_change"]].values
            
            # Train Isolation Forest
            iso_forest = IsolationForest(
                contamination=0.05,  # expect 5% anomalies
                random_state=42,
                n_estimators=100
            )
            
            predictions = iso_forest.fit_predict(features)
            anomaly_scores = iso_forest.score_samples(features)
            
            # Identify anomalies (prediction == -1)
            anomalies = []
            for idx, (pred, score) in enumerate(zip(predictions, anomaly_scores)):
                if pred == -1:
                    anomalies.append({
                        "time": df.iloc[idx]["time"],
                        "metric_value": df.iloc[idx]["metric_value"],
                        "anomaly_score": float(score),
                        "severity": self._calculate_severity(score)
                    })
            
            logger.info(f"Detected {len(anomalies)} anomalies for {equipment_id}/{metric_name}")
            return anomalies
            
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}", exc_info=True)
            return []
    
    def _calculate_severity(self, anomaly_score: float) -> AlertSeverity:
        """
        Map anomaly score to alert severity
        More negative scores = more anomalous
        """
        if anomaly_score < -0.5:
            return AlertSeverity.CRITICAL
        elif anomaly_score < -0.3:
            return AlertSeverity.WARNING
        else:
            return AlertSeverity.INFO
    
    def check_thresholds(
        self, 
        equipment_id: str,
        lookback_minutes: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Check if any recent readings exceeded safety thresholds
        This is simpler but faster than ML-based anomaly detection
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=lookback_minutes)
            
            # Get equipment info to determine thresholds
            equipment = self.db.query(Equipment).filter(
                Equipment.equipment_id == equipment_id
            ).first()
            
            if not equipment:
                return []
            
            # Define thresholds based on equipment type
            thresholds = self._get_thresholds(equipment.equipment_type.value)
            
            violations = []
            
            for metric_name, threshold in thresholds.items():
                query = text("""
                    SELECT time, metric_value, metric_unit
                    FROM sensor_readings
                    WHERE equipment_id = :equipment_id
                      AND metric_name = :metric_name
                      AND time > :cutoff_time
                      AND metric_value > :threshold
                    ORDER BY time DESC
                    LIMIT 10
                """)
                
                result = self.db.execute(
                    query,
                    {
                        "equipment_id": equipment_id,
                        "metric_name": metric_name,
                        "cutoff_time": cutoff_time,
                        "threshold": threshold
                    }
                )
                
                for row in result:
                    violations.append({
                        "time": row.time,
                        "metric_name": metric_name,
                        "metric_value": row.metric_value,
                        "metric_unit": row.metric_unit,
                        "threshold": threshold,
                        "severity": self._threshold_severity(row.metric_value, threshold)
                    })
            
            return violations
            
        except Exception as e:
            logger.error(f"Threshold check failed: {e}", exc_info=True)
            return []
    
    def _get_thresholds(self, equipment_type: str) -> Dict[str, float]:
        """
        Get safety thresholds for each equipment type
        In production, these would be configurable per device
        """
        threshold_map = {
            "gas_detector": {
                "gas_concentration": settings.GAS_DETECTION_THRESHOLD
            },
            "temperature_sensor": {
                "temperature": settings.TEMPERATURE_THRESHOLD
            },
            "pressure_sensor": {
                "pressure": settings.PRESSURE_THRESHOLD
            },
            "air_quality_monitor": {
                "pm25": 35.0,  # EPA standard
                "pm10": 150.0,
                "co2": 1000.0  # ppm
            }
        }
        
        return threshold_map.get(equipment_type, {})
    
    def _threshold_severity(self, value: float, threshold: float) -> AlertSeverity:
        """
        Determine severity based on how much threshold is exceeded
        """
        ratio = value / threshold
        
        if ratio > 2.0:
            return AlertSeverity.EMERGENCY
        elif ratio > 1.5:
            return AlertSeverity.CRITICAL
        elif ratio > 1.2:
            return AlertSeverity.WARNING
        else:
            return AlertSeverity.INFO
    
    def analyze_trends(
        self,
        equipment_id: str,
        metric_name: str,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze trends over time to identify patterns
        Useful for predictive maintenance
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=period_days)
            
            # Use the continuous aggregate for better performance
            query = text("""
                SELECT 
                    bucket as time,
                    avg_value,
                    min_value,
                    max_value,
                    stddev_value
                FROM sensor_readings_hourly
                WHERE equipment_id = :equipment_id
                  AND metric_name = :metric_name
                  AND bucket > :cutoff_time
                ORDER BY bucket ASC
            """)
            
            result = self.db.execute(
                query,
                {
                    "equipment_id": equipment_id,
                    "metric_name": metric_name,
                    "cutoff_time": cutoff_time
                }
            )
            
            df = pd.DataFrame(
                result.fetchall(), 
                columns=["time", "avg_value", "min_value", "max_value", "stddev_value"]
            )
            
            if len(df) < 24:  # need at least 24 hours of data
                return {"error": "Insufficient data for trend analysis"}
            
            # Calculate trend statistics
            values = df["avg_value"].values
            
            # Linear regression for trend direction
            x = np.arange(len(values))
            slope, intercept = np.polyfit(x, values, 1)
            
            # Volatility (coefficient of variation)
            volatility = df["stddev_value"].mean() / df["avg_value"].mean() if df["avg_value"].mean() != 0 else 0
            
            # Recent vs historical comparison
            recent_avg = df.tail(24)["avg_value"].mean()
            historical_avg = df["avg_value"].mean()
            percent_change = ((recent_avg - historical_avg) / historical_avg * 100) if historical_avg != 0 else 0
            
            return {
                "equipment_id": equipment_id,
                "metric_name": metric_name,
                "period_days": period_days,
                "trend_direction": "increasing" if slope > 0 else "decreasing",
                "trend_slope": float(slope),
                "average_value": float(df["avg_value"].mean()),
                "recent_average": float(recent_avg),
                "percent_change": float(percent_change),
                "volatility": float(volatility),
                "min_value": float(df["min_value"].min()),
                "max_value": float(df["max_value"].max()),
                "data_points": len(df)
            }
            
        except Exception as e:
            logger.error(f"Trend analysis failed: {e}", exc_info=True)
            return {"error": str(e)}
    
    def predict_maintenance(self, equipment_id: str) -> Dict[str, Any]:
        """
        Predict when equipment might need maintenance
        Based on usage patterns and historical data
        
        This is a simplified version - production would use more sophisticated ML
        """
        try:
            # Get equipment info
            equipment = self.db.query(Equipment).filter(
                Equipment.equipment_id == equipment_id
            ).first()
            
            if not equipment:
                return {"error": "Equipment not found"}
            
            # Calculate days since last calibration
            if equipment.last_calibration_date:
                days_since_calibration = (datetime.utcnow() - equipment.last_calibration_date).days
            else:
                days_since_calibration = None
            
            # Get recent alert count
            recent_alerts = self.db.query(func.count(Alert.alert_id)).filter(
                Alert.equipment_id == equipment_id,
                Alert.triggered_at > datetime.utcnow() - timedelta(days=30)
            ).scalar()
            
            # Get reading count (proxy for usage)
            reading_count = self.db.query(func.count()).filter(
                SensorReading.equipment_id == equipment_id,
                SensorReading.time > datetime.utcnow() - timedelta(days=30)
            ).scalar()
            
            # Simple scoring system
            # In production, this would be a trained ML model
            risk_score = 0
            
            if days_since_calibration and days_since_calibration > 180:
                risk_score += 40
            
            if recent_alerts > 10:
                risk_score += 30
            
            if reading_count > 10000:  # heavy usage
                risk_score += 20
            
            # Determine risk level
            if risk_score > 70:
                risk_level = "high"
                recommendation = "Schedule maintenance within 1 week"
            elif risk_score > 40:
                risk_level = "medium"
                recommendation = "Schedule maintenance within 1 month"
            else:
                risk_level = "low"
                recommendation = "Normal operations, routine checks"
            
            return {
                "equipment_id": equipment_id,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "recommendation": recommendation,
                "days_since_calibration": days_since_calibration,
                "recent_alerts": recent_alerts,
                "usage_intensity": "high" if reading_count > 10000 else "normal"
            }
            
        except Exception as e:
            logger.error(f"Maintenance prediction failed: {e}", exc_info=True)
            return {"error": str(e)}