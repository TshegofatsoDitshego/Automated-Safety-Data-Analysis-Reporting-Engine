from fastapi import FastAPI
from src.ingestion.sensor_simulator import generate_event
from src.ingestion.ingest_events import ingest_event

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ingest")
def ingest():
    event = generate_event()
    ingest_event(event)
    return {"message": "event ingested", "event": event}
