"""
Database models using SQLAlchemy ORM
Represents the core data structures for the safety analytics platform
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, String, DateTime, Float, Integer, 
    ForeignKey, Enum as SQLEnum, JSON, Text, BigInteger
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class EquipmentType(str, enum.Enum):
    """Types of safety equipment we monitor"""
    GAS_DETECTOR = "gas_detector"
    TEMPERATURE_SENSOR = "temperature_sensor"
    PRESSURE_SENSOR = "pressure_sensor"
    LOCATION_TRACKER = "location_tracker"
    AIR_QUALITY_MONITOR = "air_quality_monitor"


class EquipmentStatus(str, enum.Enum):
    """Current operational status of equipment"""
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"
    CALIBRATION_NEEDED = "calibration_needed"


class AlertSeverity(str, enum.Enum):
    """Severity levels for alerts"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class SensorReadingStatus(str, enum.Enum):
    """Status of individual sensor readings"""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    OFFLINE = "offline"


class Equipment(Base):
    """
    Equipment registry - tracks all deployed safety devices
    """
    __tablename__ = "equipment"
    
    equipment_id = Column(String(50), primary_key=True)
    equipment_type = Column(SQLEnum(EquipmentType), nullable=False)
    manufacturer = Column(String(100))
    model = Column(String(100))
    serial_number = Column(String(100), unique=True)
    installation_date = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_calibration_date = Column(DateTime(timezone=True))
    next_calibration_due = Column(DateTime(timezone=True))
    location = Column(String(200))
    status = Column(SQLEnum(EquipmentStatus), default=EquipmentStatus.ACTIVE)
    metadata = Column(JSON)  # flexible field for device-specific data
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    readings = relationship("SensorReading", back_populates="equipment", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="equipment", cascade="all, delete-orphan")


class SensorReading(Base):
    """
    Time-series sensor data - optimized for high-frequency writes
    This table becomes a TimescaleDB hypertable for performance
    """
    __tablename__ = "sensor_readings"
    
    time = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    equipment_id = Column(String(50), ForeignKey("equipment.equipment_id"), primary_key=True, nullable=False)
    metric_name = Column(String(50), primary_key=True, nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20))
    reading_status = Column(SQLEnum(SensorReadingStatus), default=SensorReadingStatus.NORMAL)
    metadata = Column(JSON)  # additional context like GPS coords, battery level, etc
    
    # Relationships
    equipment = relationship("Equipment", back_populates="readings")


class Alert(Base):
    """
    Alerts generated from anomaly detection and threshold violations
    """
    __tablename__ = "alerts"
    
    alert_id = Column(Integer, primary_key=True, autoincrement=True)
    equipment_id = Column(String(50), ForeignKey("equipment.equipment_id"), nullable=False)
    alert_type = Column(String(100), nullable=False)
    severity = Column(SQLEnum(AlertSeverity), nullable=False)
    message = Column(Text, nullable=False)
    triggered_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    acknowledged_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    metadata = Column(JSON)
    
    # Relationships
    equipment = relationship("Equipment", back_populates="alerts")


class ComplianceReport(Base):
    """
    Generated compliance reports for regulatory requirements
    """
    __tablename__ = "compliance_reports"
    
    report_id = Column(Integer, primary_key=True, autoincrement=True)
    report_type = Column(String(50), nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    generated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    file_path = Column(String(500))
    summary = Column(JSON)  # key metrics and findings
    created_by = Column(String(100))


class DataQualityMetric(Base):
    """
    Tracks data pipeline quality and health metrics
    Used for monitoring ETL performance
    """
    __tablename__ = "data_quality_metrics"
    
    metric_id = Column(Integer, primary_key=True, autoincrement=True)
    check_timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
    total_records_processed = Column(BigInteger)
    invalid_records = Column(Integer)
    duplicate_records = Column(Integer)
    late_arriving_records = Column(Integer)
    processing_time_ms = Column(Integer)
    pipeline_stage = Column(String(50))
    metadata = Column(JSON)