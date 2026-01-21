"""
Database initialization script
Sets up database schema and optionally loads sample data
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import init_db, engine
from app.models.database import Equipment, EquipmentType, EquipmentStatus
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_equipment(db: Session):
    """
    Create sample equipment for testing
    """
    logger.info("Creating sample equipment...")
    
    sample_equipment = [
        {
            "equipment_id": "GAS-001",
            "equipment_type": EquipmentType.GAS_DETECTOR,
            "manufacturer": "MSA Safety",
            "model": "Altair 5X",
            "serial_number": "MSA-001-2024",
            "location": "Zone A - Production Floor",
            "installation_date": datetime.utcnow() - timedelta(days=180),
            "last_calibration_date": datetime.utcnow() - timedelta(days=30),
            "next_calibration_due": datetime.utcnow() + timedelta(days=60),
            "status": EquipmentStatus.ACTIVE,
            "metadata": {
                "sensor_types": ["O2", "CO", "H2S", "LEL"],
                "wireless": True,
                "bluetooth_enabled": True
            }
        },
        {
            "equipment_id": "GAS-002",
            "equipment_type": EquipmentType.GAS_DETECTOR,
            "manufacturer": "MSA Safety",
            "model": "Altair 4X",
            "serial_number": "MSA-002-2024",
            "location": "Zone B - Storage Area",
            "installation_date": datetime.utcnow() - timedelta(days=200),
            "last_calibration_date": datetime.utcnow() - timedelta(days=45),
            "next_calibration_due": datetime.utcnow() + timedelta(days=45),
            "status": EquipmentStatus.ACTIVE,
            "metadata": {
                "sensor_types": ["O2", "CO", "H2S"],
                "wireless": True
            }
        },
        {
            "equipment_id": "TEMP-001",
            "equipment_type": EquipmentType.TEMPERATURE_SENSOR,
            "manufacturer": "Honeywell",
            "model": "T6000",
            "serial_number": "HON-TEMP-001",
            "location": "Zone A - Production Floor",
            "installation_date": datetime.utcnow() - timedelta(days=150),
            "last_calibration_date": datetime.utcnow() - timedelta(days=60),
            "next_calibration_due": datetime.utcnow() + timedelta(days=30),
            "status": EquipmentStatus.ACTIVE,
            "metadata": {
                "range": "-40 to 125°C",
                "accuracy": "±0.5°C"
            }
        },
        {
            "equipment_id": "TEMP-002",
            "equipment_type": EquipmentType.TEMPERATURE_SENSOR,
            "manufacturer": "Honeywell",
            "model": "T6000",
            "serial_number": "HON-TEMP-002",
            "location": "Zone C - Office Space",
            "installation_date": datetime.utcnow() - timedelta(days=120),
            "last_calibration_date": datetime.utcnow() - timedelta(days=20),
            "next_calibration_due": datetime.utcnow() + timedelta(days=70),
            "status": EquipmentStatus.ACTIVE,
            "metadata": {
                "range": "-40 to 125°C",
                "accuracy": "±0.5°C"
            }
        },
        {
            "equipment_id": "PRESS-001",
            "equipment_type": EquipmentType.PRESSURE_SENSOR,
            "manufacturer": "Emerson",
            "model": "Rosemount 3051",
            "serial_number": "EMR-PRESS-001",
            "location": "Zone A - Production Floor",
            "installation_date": datetime.utcnow() - timedelta(days=240),
            "last_calibration_date": datetime.utcnow() - timedelta(days=90),
            "next_calibration_due": datetime.utcnow() + timedelta(days=10),
            "status": EquipmentStatus.ACTIVE,
            "metadata": {
                "range": "0-500 psi",
                "accuracy": "±0.075%"
            }
        },
        {
            "equipment_id": "AIR-001",
            "equipment_type": EquipmentType.AIR_QUALITY_MONITOR,
            "manufacturer": "IQAir",
            "model": "AirVisual Pro",
            "serial_number": "IQ-AIR-001",
            "location": "Zone B - Storage Area",
            "installation_date": datetime.utcnow() - timedelta(days=90),
            "last_calibration_date": datetime.utcnow() - timedelta(days=15),
            "next_calibration_due": datetime.utcnow() + timedelta(days=75),
            "status": EquipmentStatus.ACTIVE,
            "metadata": {
                "sensors": ["PM2.5", "PM10", "CO2", "Temperature", "Humidity"],
                "wifi_enabled": True
            }
        },
        {
            "equipment_id": "GAS-003",
            "equipment_type": EquipmentType.GAS_DETECTOR,
            "manufacturer": "Honeywell",
            "model": "BW Solo",
            "serial_number": "HON-GAS-003",
            "location": "Zone D - Maintenance Area",
            "installation_date": datetime.utcnow() - timedelta(days=300),
            "last_calibration_date": datetime.utcnow() - timedelta(days=100),
            "next_calibration_due": datetime.utcnow() - timedelta(days=10),  # Overdue!
            "status": EquipmentStatus.CALIBRATION_NEEDED,
            "metadata": {
                "sensor_types": ["CO"],
                "wireless": False
            }
        },
        {
            "equipment_id": "TRACK-001",
            "equipment_type": EquipmentType.LOCATION_TRACKER,
            "manufacturer": "Blackline Safety",
            "model": "G7c",
            "serial_number": "BLS-TRACK-001",
            "location": "Mobile - Field Operations",
            "installation_date": datetime.utcnow() - timedelta(days=60),
            "last_calibration_date": datetime.utcnow() - timedelta(days=5),
            "next_calibration_due": datetime.utcnow() + timedelta(days=85),
            "status": EquipmentStatus.ACTIVE,
            "metadata": {
                "gps_enabled": True,
                "cellular": True,
                "fall_detection": True
            }
        }
    ]
    
    count = 0
    for equip_data in sample_equipment:
        # Check if already exists
        existing = db.query(Equipment).filter(
            Equipment.equipment_id == equip_data["equipment_id"]
        ).first()
        
        if not existing:
            equipment = Equipment(**equip_data)
            db.add(equipment)
            count += 1
            logger.info(f"  ✓ Created: {equip_data['equipment_id']}")
        else:
            logger.info(f"  - Skipped (exists): {equip_data['equipment_id']}")
    
    db.commit()
    logger.info(f"Created {count} sample equipment records")


def main():
    """
    Main initialization function
    """
    logger.info("=" * 60)
    logger.info("SafetySync Database Initialization")
    logger.info("=" * 60)
    
    try:
        # Initialize database schema
        logger.info("\n1. Initializing database schema...")
        init_db()
        logger.info("✓ Database schema initialized\n")
        
        # Create sample equipment
        logger.info("2. Creating sample equipment...")
        with Session(engine) as db:
            create_sample_equipment(db)
        logger.info("✓ Sample equipment created\n")
        
        logger.info("=" * 60)
        logger.info("Database initialization complete!")
        logger.info("=" * 60)
        logger.info("\nNext steps:")
        logger.info("1. Run the sensor simulator to generate test data:")
        logger.info("   python scripts/simulate_sensors.py --mode historical --days 7")
        logger.info("\n2. Start the API server:")
        logger.info("   uvicorn app.main:app --reload")
        logger.info("\n3. View API docs at: http://localhost:8000/docs")
        
    except Exception as e:
        logger.error(f"\n✗ Initialization failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()