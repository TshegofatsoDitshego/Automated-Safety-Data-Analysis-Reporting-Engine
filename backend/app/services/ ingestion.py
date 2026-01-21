"""
Data ingestion pipeline - handles high-volume sensor data intake
Implements batch processing, validation, and quality checks
"""
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
import pandas as pd
import numpy as np
import logging
import time

from app.models.database import SensorReading, DataQualityMetric, Equipment
from app.core.config import settings

logger = logging.getLogger(__name__)


class DataIngestionPipeline:
    """
    Main ingestion pipeline for sensor readings
    Handles validation, deduplication, and batch insertion
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.buffer: List[Dict[str, Any]] = []
        self.stats = {
            "total_processed": 0,
            "invalid": 0,
            "duplicates": 0,
            "late_arrivals": 0,
        }
    
    def ingest_batch(self, readings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Main entry point for batch ingestion
        
        Args:
            readings: List of sensor reading dictionaries
            
        Returns:
            Dictionary with ingestion stats and any errors
        """
        start_time = time.time()
        
        try:
            # Step 1: Validate and clean data
            validated_readings = self._validate_readings(readings)
            
            # Step 2: Check for duplicates
            unique_readings = self._deduplicate(validated_readings)
            
            # Step 3: Detect late-arriving data
            on_time, late = self._check_timeliness(unique_readings)
            self.stats["late_arrivals"] += len(late)
            
            # Step 4: Batch insert into database
            if on_time:
                self._bulk_insert(on_time)
            
            # Step 5: Record data quality metrics
            processing_time = int((time.time() - start_time) * 1000)
            self._record_quality_metrics(processing_time)
            
            return {
                "success": True,
                "total_received": len(readings),
                "total_inserted": len(on_time),
                "invalid_count": self.stats["invalid"],
                "duplicate_count": self.stats["duplicates"],
                "late_arrival_count": self.stats["late_arrivals"],
                "processing_time_ms": processing_time
            }
            
        except Exception as e:
            logger.error(f"Ingestion batch failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "total_received": len(readings)
            }
    
    def _validate_readings(self, readings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate incoming sensor readings
        Checks for required fields, data types, and value ranges
        """
        validated = []
        
        for reading in readings:
            try:
                # Required fields check
                required_fields = ["equipment_id", "metric_name", "metric_value", "time"]
                if not all(field in reading for field in required_fields):
                    self.stats["invalid"] += 1
                    logger.warning(f"Missing required fields: {reading}")
                    continue
                
                # Data type validation
                metric_value = float(reading["metric_value"])
                
                # Parse timestamp
                if isinstance(reading["time"], str):
                    timestamp = datetime.fromisoformat(reading["time"].replace("Z", "+00:00"))
                else:
                    timestamp = reading["time"]
                
                # Sanity check on values (adjust per metric type)
                if not self._is_value_reasonable(reading["metric_name"], metric_value):
                    self.stats["invalid"] += 1
                    logger.warning(f"Unreasonable value: {reading}")
                    continue
                
                # Equipment exists check (could cache this for performance)
                equipment_exists = self.db.query(Equipment).filter(
                    Equipment.equipment_id == reading["equipment_id"]
                ).first()
                
                if not equipment_exists:
                    self.stats["invalid"] += 1
                    logger.warning(f"Equipment not found: {reading['equipment_id']}")
                    continue
                
                validated.append({
                    "time": timestamp,
                    "equipment_id": reading["equipment_id"],
                    "metric_name": reading["metric_name"],
                    "metric_value": metric_value,
                    "metric_unit": reading.get("metric_unit"),
                    "reading_status": reading.get("reading_status", "normal"),
                    "metadata": reading.get("metadata", {})
                })
                
            except (ValueError, TypeError, KeyError) as e:
                self.stats["invalid"] += 1
                logger.warning(f"Validation failed for reading: {e}")
                continue
        
        self.stats["total_processed"] += len(readings)
        return validated
    
    def _is_value_reasonable(self, metric_name: str, value: float) -> bool:
        """
        Sanity check on sensor values
        Prevents obviously wrong data from entering system
        """
        # Define reasonable ranges per metric type
        ranges = {
            "gas_concentration": (-0.1, 10000),  # ppm
            "temperature": (-50, 200),  # celsius
            "pressure": (0, 1000),  # psi
            "humidity": (0, 100),  # percentage
            "battery_level": (0, 100),  # percentage
        }
        
        # Default range if metric not in predefined list
        min_val, max_val = ranges.get(metric_name, (-1e6, 1e6))
        
        return min_val <= value <= max_val and not np.isnan(value) and not np.isinf(value)
    
    def _deduplicate(self, readings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate readings using pandas for efficiency
        Duplicates are identified by (equipment_id, metric_name, time)
        """
        if not readings:
            return []
        
        df = pd.DataFrame(readings)
        
        # Identify duplicates
        initial_count = len(df)
        df_unique = df.drop_duplicates(
            subset=["equipment_id", "metric_name", "time"],
            keep="first"
        )
        
        duplicates_removed = initial_count - len(df_unique)
        self.stats["duplicates"] += duplicates_removed
        
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate readings")
        
        return df_unique.to_dict("records")
    
    def _check_timeliness(self, readings: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict]]:
        """
        Separate on-time vs late-arriving data
        Late data might indicate network issues or device problems
        """
        if not readings:
            return [], []
        
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=settings.MAX_LATE_ARRIVAL_MINUTES)
        
        on_time = [r for r in readings if r["time"] >= cutoff]
        late = [r for r in readings if r["time"] < cutoff]
        
        if late:
            logger.warning(f"Received {len(late)} late-arriving readings")
        
        return on_time, late
    
    def _bulk_insert(self, readings: List[Dict[str, Any]]):
        """
        Efficient bulk insert using SQLAlchemy Core
        Much faster than ORM for large batches
        """
        if not readings:
            return
        
        try:
            # Use raw SQL for maximum performance
            # TimescaleDB handles this very efficiently
            insert_stmt = text("""
                INSERT INTO sensor_readings 
                (time, equipment_id, metric_name, metric_value, metric_unit, reading_status, metadata)
                VALUES (:time, :equipment_id, :metric_name, :metric_value, :metric_unit, :reading_status, :metadata)
                ON CONFLICT DO NOTHING
            """)
            
            # Batch the inserts for better performance
            batch_size = settings.MAX_BATCH_SIZE
            for i in range(0, len(readings), batch_size):
                batch = readings[i:i + batch_size]
                self.db.execute(insert_stmt, batch)
                self.db.commit()
            
            logger.info(f"Successfully inserted {len(readings)} readings")
            
        except Exception as e:
            logger.error(f"Bulk insert failed: {e}", exc_info=True)
            self.db.rollback()
            raise
    
    def _record_quality_metrics(self, processing_time_ms: int):
        """
        Record data quality metrics for monitoring
        Helps identify pipeline issues early
        """
        try:
            metric = DataQualityMetric(
                total_records_processed=self.stats["total_processed"],
                invalid_records=self.stats["invalid"],
                duplicate_records=self.stats["duplicates"],
                late_arriving_records=self.stats["late_arrivals"],
                processing_time_ms=processing_time_ms,
                pipeline_stage="ingestion",
                metadata={
                    "duplicate_rate": self.stats["duplicates"] / max(self.stats["total_processed"], 1),
                    "invalid_rate": self.stats["invalid"] / max(self.stats["total_processed"], 1)
                }
            )
            
            self.db.add(metric)
            self.db.commit()
            
            # Check if quality thresholds are breached
            self._check_quality_thresholds()
            
        except Exception as e:
            logger.error(f"Failed to record quality metrics: {e}")
    
    def _check_quality_thresholds(self):
        """
        Alert if data quality falls below acceptable thresholds
        """
        total = max(self.stats["total_processed"], 1)
        duplicate_rate = self.stats["duplicates"] / total
        invalid_rate = self.stats["invalid"] / total
        
        if duplicate_rate > settings.MAX_DUPLICATE_RATE:
            logger.error(f"High duplicate rate: {duplicate_rate:.2%}")
            # In production, trigger alert to ops team
        
        if invalid_rate > settings.MAX_INVALID_RATE:
            logger.error(f"High invalid record rate: {invalid_rate:.2%}")
            # In production, trigger alert to ops team