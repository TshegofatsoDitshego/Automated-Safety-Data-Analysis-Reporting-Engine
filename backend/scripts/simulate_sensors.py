"""
Sensor data simulator
Generates realistic sensor data for testing the platform
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timedelta
import random
import time
import requests
import numpy as np
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API endpoint
API_BASE_URL = "http://localhost:8000/api/v1"


class SensorSimulator:
    """
    Simulates realistic sensor data with anomalies
    """
    
    def __init__(self, equipment_id: str, equipment_type: str):
        self.equipment_id = equipment_id
        self.equipment_type = equipment_type
        self.baseline_values = self._get_baseline_values()
        self.time_offset = 0  # for simulating historical data
    
    def _get_baseline_values(self) -> Dict[str, float]:
        """Get typical baseline values per equipment type"""
        baselines = {
            "gas_detector": {
                "gas_concentration": 2.5,  # ppm
                "battery_level": 85.0,
                "signal_strength": -60.0
            },
            "temperature_sensor": {
                "temperature": 22.0,  # celsius
                "humidity": 45.0,
                "battery_level": 90.0
            },
            "pressure_sensor": {
                "pressure": 100.0,  # psi
                "battery_level": 88.0
            },
            "air_quality_monitor": {
                "pm25": 12.0,  # μg/m³
                "pm10": 25.0,
                "co2": 400.0,  # ppm
                "battery_level": 82.0
            }
        }
        
        return baselines.get(self.equipment_type, {"value": 50.0})
    
    def generate_reading(self, introduce_anomaly: bool = False) -> List[Dict]:
        """
        Generate a set of sensor readings
        
        Args:
            introduce_anomaly: Whether to introduce an anomalous value
        """
        readings = []
        current_time = datetime.utcnow() - timedelta(seconds=self.time_offset)
        
        for metric_name, baseline in self.baseline_values.items():
            if metric_name == "battery_level":
                # Battery slowly decreases over time
                value = baseline - (self.time_offset / 86400) * 0.1  # lose 0.1% per day
                value = max(0, min(100, value))
            elif metric_name == "signal_strength":
                # Signal strength varies slightly
                value = baseline + np.random.normal(0, 5)
            else:
                # Main metrics with realistic noise
                if introduce_anomaly and random.random() < 0.3:
                    # Introduce anomaly (spike)
                    value = baseline * random.uniform(2.5, 4.0)
                else:
                    # Normal variation with some drift
                    noise = np.random.normal(0, baseline * 0.05)
                    drift = np.sin(self.time_offset / 3600) * baseline * 0.1  # hourly pattern
                    value = baseline + noise + drift
                
                value = max(0, value)
            
            # Determine reading status
            if metric_name in ["gas_concentration", "temperature", "pressure", "pm25", "co2"]:
                threshold = baseline * 3
                if value > threshold:
                    status = "critical"
                elif value > threshold * 0.7:
                    status = "warning"
                else:
                    status = "normal"
            else:
                status = "normal"
            
            reading = {
                "equipment_id": self.equipment_id,
                "metric_name": metric_name,
                "metric_value": round(value, 2),
                "metric_unit": self._get_unit(metric_name),
                "time": current_time.isoformat() + "Z",
                "reading_status": status,
                "metadata": {
                    "sensor_id": f"{self.equipment_id}_{metric_name}",
                    "firmware_version": "2.1.3"
                }
            }
            
            readings.append(reading)
        
        return readings
    
    def _get_unit(self, metric_name: str) -> str:
        """Get the unit for a metric"""
        units = {
            "gas_concentration": "ppm",
            "temperature": "celsius",
            "humidity": "percent",
            "pressure": "psi",
            "pm25": "μg/m³",
            "pm10": "μg/m³",
            "co2": "ppm",
            "battery_level": "percent",
            "signal_strength": "dBm"
        }
        return units.get(metric_name, "unit")


def create_equipment(equipment_id: str, equipment_type: str, location: str):
    """Create equipment via API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/equipment/",
            json={
                "equipment_id": equipment_id,
                "equipment_type": equipment_type,
                "manufacturer": "MSA Safety" if "GAS" in equipment_id else "Generic Corp",
                "model": f"Model-{equipment_type[:4].upper()}",
                "serial_number": f"SN-{equipment_id}",
                "location": location,
                "metadata": {
                    "deployment_zone": location.split("-")[0],
                    "wireless": True
                }
            }
        )
        
        if response.status_code == 201:
            logger.info(f"✓ Created equipment: {equipment_id}")
            return True
        elif response.status_code == 400 and "already exists" in response.text:
            logger.info(f"✓ Equipment already exists: {equipment_id}")
            return True
        else:
            logger.error(f"✗ Failed to create {equipment_id}: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Error creating equipment {equipment_id}: {e}")
        return False


def send_readings(readings: List[Dict]):
    """Send readings to API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/ingestion/batch",
            json={"readings": readings, "source": "simulator"}
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(
                f"✓ Sent {result['total_inserted']}/{result['total_received']} readings "
                f"({result['processing_time_ms']}ms)"
            )
            return True
        else:
            logger.error(f"✗ Failed to send readings: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Error sending readings: {e}")
        return False


def simulate_historical_data(days: int = 7):
    """
    Generate historical data for the past N days
    Useful for testing analytics and reports
    """
    logger.info(f"Generating {days} days of historical data...")
    
    # Equipment configuration
    equipment_config = [
        ("GAS-001", "gas_detector", "Zone-A Production Floor"),
        ("GAS-002", "gas_detector", "Zone-B Storage Area"),
        ("TEMP-001", "temperature_sensor", "Zone-A Production Floor"),
        ("TEMP-002", "temperature_sensor", "Zone-C Office Space"),
        ("PRESS-001", "pressure_sensor", "Zone-A Production Floor"),
        ("AIR-001", "air_quality_monitor", "Zone-B Storage Area"),
    ]
    
    # Create equipment
    for equip_id, equip_type, location in equipment_config:
        create_equipment(equip_id, equip_type, location)
    
    # Generate historical readings
    simulators = [
        SensorSimulator(equip_id, equip_type) 
        for equip_id, equip_type, _ in equipment_config
    ]
    
    # Simulate readings every 5 minutes for N days
    intervals = (days * 24 * 60) // 5  # readings every 5 minutes
    
    for i in range(intervals):
        all_readings = []
        
        for simulator in simulators:
            simulator.time_offset = (intervals - i) * 300  # 5 minutes in seconds
            
            # Introduce occasional anomalies (5% chance)
            introduce_anomaly = random.random() < 0.05
            
            readings = simulator.generate_reading(introduce_anomaly)
            all_readings.extend(readings)
        
        # Send in batches
        if send_readings(all_readings):
            if (i + 1) % 100 == 0:
                logger.info(f"Progress: {i+1}/{intervals} intervals processed")
        
        # Small delay to avoid overwhelming the API
        time.sleep(0.1)
    
    logger.info(f"✓ Historical data generation complete!")


def simulate_realtime_stream(duration_minutes: int = 60):
    """
    Simulate real-time sensor data stream
    Sends new readings every 30 seconds
    """
    logger.info(f"Starting real-time simulation for {duration_minutes} minutes...")
    
    equipment_config = [
        ("GAS-001", "gas_detector", "Zone-A Production Floor"),
        ("TEMP-001", "temperature_sensor", "Zone-A Production Floor"),
        ("AIR-001", "air_quality_monitor", "Zone-B Storage Area"),
    ]
    
    # Create equipment if needed
    for equip_id, equip_type, location in equipment_config:
        create_equipment(equip_id, equip_type, location)
    
    simulators = [
        SensorSimulator(equip_id, equip_type) 
        for equip_id, equip_type, _ in equipment_config
    ]
    
    end_time = datetime.utcnow() + timedelta(minutes=duration_minutes)
    iteration = 0
    
    while datetime.utcnow() < end_time:
        all_readings = []
        
        for simulator in simulators:
            # Occasionally introduce anomalies
            introduce_anomaly = iteration % 50 == 0  # every 50 iterations
            
            readings = simulator.generate_reading(introduce_anomaly)
            all_readings.extend(readings)
        
        send_readings(all_readings)
        
        iteration += 1
        logger.info(f"Real-time stream iteration {iteration} - sleeping 30s...")
        time.sleep(30)  # Send new readings every 30 seconds
    
    logger.info("✓ Real-time simulation complete!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Sensor data simulator")
    parser.add_argument(
        "--mode",
        choices=["historical", "realtime", "both"],
        default="both",
        help="Simulation mode"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Days of historical data to generate"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Duration of real-time simulation in minutes"
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("SafetySync Sensor Data Simulator")
    logger.info("=" * 60)
    
    try:
        if args.mode in ["historical", "both"]:
            simulate_historical_data(args.days)
        
        if args.mode in ["realtime", "both"]:
            if args.mode == "both":
                logger.info("\nWaiting 5 seconds before starting real-time stream...\n")
                time.sleep(5)
            
            simulate_realtime_stream(args.duration)
    
    except KeyboardInterrupt:
        logger.info("\n\nSimulation interrupted by user")
    except Exception as e:
        logger.error(f"\n\nSimulation failed: {e}", exc_info=True)