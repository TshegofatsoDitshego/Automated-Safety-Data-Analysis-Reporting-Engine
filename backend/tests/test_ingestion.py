"""
Tests for data ingestion pipeline
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from faker import Faker

from app.models.database import Base, Equipment, SensorReading, EquipmentType
from app.services.ingestion import DataIngestionPipeline

fake = Faker()

# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(bind=engine)


@pytest.fixture
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestSessionLocal()
    
    # Create test equipment
    equipment = Equipment(
        equipment_id="TEST-001",
        equipment_type=EquipmentType.GAS_DETECTOR,
        manufacturer="Test Corp",
        model="Test Model",
        serial_number="TEST-SN-001"
    )
    session.add(equipment)
    session.commit()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=engine)


class TestDataIngestionPipeline:
    """Test suite for data ingestion pipeline"""
    
    def test_ingest_valid_readings(self, db_session):
        """Test ingestion of valid sensor readings"""
        pipeline = DataIngestionPipeline(db_session)
        
        readings = [
            {
                "equipment_id": "TEST-001",
                "metric_name": "gas_concentration",
                "metric_value": 5.2,
                "metric_unit": "ppm",
                "time": datetime.utcnow(),
                "reading_status": "normal"
            },
            {
                "equipment_id": "TEST-001",
                "metric_name": "temperature",
                "metric_value": 22.5,
                "metric_unit": "celsius",
                "time": datetime.utcnow(),
                "reading_status": "normal"
            }
        ]
        
        result = pipeline.ingest_batch(readings)
        
        assert result["success"] is True
        assert result["total_inserted"] == 2
        assert result["invalid_count"] == 0
        assert result["duplicate_count"] == 0
    
    def test_reject_invalid_readings(self, db_session):
        """Test that invalid readings are rejected"""
        pipeline = DataIngestionPipeline(db_session)
        
        readings = [
            {
                "equipment_id": "TEST-001",
                "metric_name": "gas_concentration",
                "metric_value": "not_a_number",  # Invalid: string instead of float
                "time": datetime.utcnow()
            },
            {
                "equipment_id": "NONEXISTENT",  # Invalid: equipment doesn't exist
                "metric_name": "temperature",
                "metric_value": 25.0,
                "time": datetime.utcnow()
            }
        ]
        
        result = pipeline.ingest_batch(readings)
        
        assert result["success"] is True
        assert result["total_inserted"] == 0
        assert result["invalid_count"] == 2
    
    def test_deduplicate_readings(self, db_session):
        """Test that duplicate readings are removed"""
        pipeline = DataIngestionPipeline(db_session)
        
        timestamp = datetime.utcnow()
        
        readings = [
            {
                "equipment_id": "TEST-001",
                "metric_name": "gas_concentration",
                "metric_value": 5.0,
                "time": timestamp
            },
            {
                "equipment_id": "TEST-001",
                "metric_name": "gas_concentration",
                "metric_value": 5.0,
                "time": timestamp  # Duplicate
            }
        ]
        
        result = pipeline.ingest_batch(readings)
        
        assert result["success"] is True
        assert result["total_inserted"] == 1
        assert result["duplicate_count"] == 1
    
    def test_detect_late_arrivals(self, db_session):
        """Test detection of late-arriving data"""
        pipeline = DataIngestionPipeline(db_session)
        
        readings = [
            {
                "equipment_id": "TEST-001",
                "metric_name": "temperature",
                "metric_value": 25.0,
                "time": datetime.utcnow() - timedelta(hours=2)  # 2 hours old
            }
        ]
        
        result = pipeline.ingest_batch(readings)
        
        # Should still ingest but mark as late
        assert result["success"] is True
        assert result["late_arrival_count"] == 1
    
    def test_batch_performance(self, db_session):
        """Test that batch ingestion performs well with larger datasets"""
        pipeline = DataIngestionPipeline(db_session)
        
        # Generate 1000 readings
        readings = []
        for i in range(1000):
            readings.append({
                "equipment_id": "TEST-001",
                "metric_name": "gas_concentration",
                "metric_value": fake.pyfloat(min_value=0, max_value=10),
                "time": datetime.utcnow() - timedelta(seconds=i),
                "reading_status": "normal"
            })
        
        result = pipeline.ingest_batch(readings)
        
        assert result["success"] is True
        assert result["total_inserted"] == 1000
        # Processing should be reasonably fast (less than 5 seconds for 1000 records)
        assert result["processing_time_ms"] < 5000
    
    def test_unreasonable_values_rejected(self, db_session):
        """Test that unreasonable sensor values are rejected"""
        pipeline = DataIngestionPipeline(db_session)
        
        readings = [
            {
                "equipment_id": "TEST-001",
                "metric_name": "temperature",
                "metric_value": 999999.0,  # Unreasonably high
                "time": datetime.utcnow()
            }
        ]
        
        result = pipeline.ingest_batch(readings)
        
        assert result["invalid_count"] == 1
        assert result["total_inserted"] == 0