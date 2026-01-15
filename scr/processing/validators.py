def validate_event(event: dict) -> dict:
    required_fields = ["type", "severity"]
    for field in required_fields:
        if field not in event:
            raise ValueError(f"Missing field: {field}")
    return event
