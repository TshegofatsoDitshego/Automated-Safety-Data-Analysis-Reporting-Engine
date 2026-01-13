import random
from datetime import datetime

SENSORS = [
    {"id": "S-001", "gas": "H2S", "base": 5},
    {"id": "S-002", "gas": "O2", "base": 20.9},
    {"id": "S-003", "gas": "LEL", "base": 2},
]

def generate_reading():
    sensor = random.choice(SENSORS)

    noise = random.uniform(-1.5, 1.5)
    spike = random.choice([0, 0, 0, random.uniform(5, 15)])

    value = max(sensor["base"] + noise + spike, 0)

    return {
        "sensor_id": sensor["id"],
        "gas_type": sensor["gas"],
        "value": round(value, 2),
        "timestamp": datetime.utcnow()
    }
