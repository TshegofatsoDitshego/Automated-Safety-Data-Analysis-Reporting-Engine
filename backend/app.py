from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from database import SessionLocal, engine
import models
from sensor_simulator import generate_reading
from safety_engine import evaluate_reading
from ai_advisor import generate_advice

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Safety io – Telemetry Backend")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/ingest")
def ingest_reading(db: Session = Depends(get_db)):
    reading = generate_reading()

    db_reading = models.SensorReading(**reading, unit="ppm")
    db.add(db_reading)
    db.commit()

    alert_info = evaluate_reading(
        reading["sensor_id"],
        reading["gas_type"],
        reading["value"]
    )

    response = {"reading": reading}

    if alert_info:
        severity, message = alert_info
        alert = models.SafetyAlert(
            sensor_id=reading["sensor_id"],
            gas_type=reading["gas_type"],
            severity=severity,
            message=message
        )
        db.add(alert)
        db.commit()

        response["alert"] = {
            "severity": severity,
            "message": message,
            "ai": generate_advice(alert)
        }

    return response


@app.get("/alerts")
def get_alerts(db: Session = Depends(get_db)):
    return db.query(models.SafetyAlert).order_by(
        models.SafetyAlert.timestamp.desc()
    ).limit(50).all()
