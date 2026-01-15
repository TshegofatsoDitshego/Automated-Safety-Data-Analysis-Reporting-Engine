from datetime import datetime

def enrich_event(event: dict) -> dict:
    event["timestamp"] = datetime.utcnow().isoformat()
    return event
