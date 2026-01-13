def generate_advice(alert):
    return {
        "disclaimer": (
            "This AI-generated recommendation is advisory only "
            "and must not be used as a compliance decision."
        ),
        "recommendation": (
            f"For {alert.gas_type} alert ({alert.severity}), "
            "evacuate affected area and verify with calibrated detectors."
        )
    }
