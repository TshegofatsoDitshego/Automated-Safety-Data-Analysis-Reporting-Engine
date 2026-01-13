from sqlalchemy import Column, Integer, Float, String, DateTime
from datetime import datetime
from database import Base

class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String, index=True)
    gas_type = Column(String)
    value = Column(Float)
    unit = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)


class SafetyAlert(Base):
    __tablename__ = "safety_alerts"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String)
    gas_type = Column(String)
    severity = Column(String)   # INFO / WARNING / CRITICAL
    message = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
