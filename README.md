# SafetyPulse – Data Engineering & Backend System

## Overview
SafetyPulse is an end-to-end safety telemetry analytics system demonstrating
**data engineering** and **backend software engineering** fundamentals.

## Architecture
Sensors / Events
    ↓
Ingestion Jobs (Python)
    ↓
PostgreSQL (raw → processed → analytics)
    ↓
FastAPI Backend
    ↓
Dashboards / Reports

## Tech Stack
- Python 3.10
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pandas

## Data Layers
- raw_events: append-only ingestion
- processed_events: cleaned & validated
- safety_metrics: aggregated analytics

## How to Run
1. Start Postgres
2. Run `python ingest_events.py`
3. Run `python transform_events.py`
4. Start API: `uvicorn api.main:app`

## Why This Project Matters
This system demonstrates:
- Real ingestion
- Schema design
- Transformations
- Analytics
- API exposure  