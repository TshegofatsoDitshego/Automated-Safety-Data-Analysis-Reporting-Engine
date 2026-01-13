SAFETY_LIMITS = {
    "H2S": {"warning": 10, "critical": 20, "unit": "ppm"},
    "O2": {"warning": 19.5, "critical": 16, "unit": "%"},
    "LEL": {"warning": 10, "critical": 20, "unit": "%LEL"},
}

def evaluate_reading(sensor_id, gas_type, value):
    limits = SAFETY_LIMITS.get(gas_type)
    if not limits:
        return None

    if gas_type == "O2":
        if value <= limits["critical"]:
            return ("CRITICAL", "Oxygen-deficient atmosphere")
        elif value <= limits["warning"]:
            return ("WARNING", "Oxygen level approaching unsafe range")
    else:
        if value >= limits["critical"]:
            return ("CRITICAL", f"{gas_type} concentration is dangerous")
        elif value >= limits["warning"]:
            return ("WARNING", f"{gas_type} concentration elevated")

    return None
