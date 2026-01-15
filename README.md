# Safety Event Data Pipeline

## Overview
This project is a production-style **junior data engineering / software engineering** project that simulates the ingestion,
validation, and exposure of safety-related sensor data.

It is designed to demonstrate how real-world data systems are structured, even at a junior level.

## Problem Statement
Many organizations collect safety or sensor data but struggle to:
- Validate incoming data
- Store it reliably
- Expose it in a usable way for applications and analytics

This project solves that by implementing a simple but realistic data pipeline.

## Architecture
Sensor Event → Ingestion → Validation → API Access

## Features
- Modular Python project structure
- Event ingestion layer
- Schema validation
- REST API using FastAPI
- Unit testing with Pytest
- Clear separation of concerns

## Tech Stack
- Python
- FastAPI
- Pydantic
- Pytest

## Skills Demonstrated
- Data pipeline design
- Backend API development
- Data validation and error handling
- Clean code and project structuring
- Writing testable Python code

## How to Run
```bash
pip install -r requirements.txt
uvicorn src.api.app:app --reload
```

Visit: http://127.0.0.1:8000

## Why This Project Matters
This project is intentionally simple but structured to reflect production engineering practices.
It shows readiness for junior roles where maintainability and clarity matter more than complexity.