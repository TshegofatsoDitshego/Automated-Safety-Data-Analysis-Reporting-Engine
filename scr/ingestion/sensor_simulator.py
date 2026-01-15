import random

def generate_event() -> dict:
    return {
        "type": random.choice(["FIRE", "ACCIDENT", "INTRUSION"]),
        "severity": random.randint(1, 5),
    }
