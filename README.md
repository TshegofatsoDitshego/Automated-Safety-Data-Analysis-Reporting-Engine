# SafetySync Analytics Platform

A real-time safety data monitoring and analysis system designed for industrial environments. This project demonstrates end-to-end data engineering and full-stack development skills by simulating IoT sensor networks and providing actionable insights through automated analysis and reporting.

## Problem Statement

Industrial safety equipment generates massive amounts of sensor data (gas detection, temperature, location tracking), but turning this raw data into actionable insights remains challenging. Safety officers need:
- Real-time monitoring of equipment status
- Automated compliance reporting
- Predictive maintenance alerts
- Historical trend analysis

This platform addresses these needs through a comprehensive data pipeline and analytics system.

## Features

### Core Functionality
- **Real-time Data Ingestion**: Accepts sensor data via REST API with validation
- **Time-Series Storage**: Optimized database schema for high-frequency sensor readings
- **Automated Analysis**: Anomaly detection, trend analysis, and threshold monitoring
- **Compliance Reporting**: Automated PDF reports with configurable schedules
- **Interactive Dashboard**: Real-time visualizations of fleet status and alerts
- **Predictive Maintenance**: ML-based equipment failure prediction

### Technical Highlights
- Handles 1000+ concurrent sensor streams
- Sub-second query performance on millions of data points
- Containerized microservices architecture
- Comprehensive test coverage (unit, integration, e2e)

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Sensors   │─────▶│  API Gateway │─────▶│   Message   │
│  (Simulated)│      │   (FastAPI)  │      │Queue (Redis)│
└─────────────┘      └──────────────┘      └─────────────┘
                                                   │
                     ┌─────────────────────────────┘
                     ▼
              ┌──────────────┐
              │  Data Engine │
              │   (Python)   │
              └──────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌─────────┐ ┌──────────┐ ┌─────────┐
   │PostgreSQL│ │ Analysis │ │ Report  │
   │+TimescaleDB│ │ Service  │ │Generator│
   └─────────┘ └──────────┘ └─────────┘
                     │
                     ▼
              ┌──────────────┐
              │   Frontend   │
              │ (React + TS) │
              └──────────────┘
```

## Tech Stack

**Backend**
- FastAPI (Python 3.11+)
- PostgreSQL with TimescaleDB extension
- Redis for task queuing and caching
- Celery for background jobs
- Pandas, NumPy, scikit-learn for data analysis

**Frontend**
- React 18 with TypeScript
- Recharts for data visualization
- TanStack Query for data fetching
- Tailwind CSS for styling

**Infrastructure**
- Docker & Docker Compose
- pytest for testing
- GitHub Actions for CI/CD

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)

### Quick Start

1. Clone the repository
```bash
git clone https://github.com/TshegofatsoDitshego/safety-analytics.git
cd safety-analytics
```

2. Start all services with Docker Compose
```bash
docker-compose up -d
```

3. Initialize the database
```bash
docker-compose exec api python scripts/init_db.py
```

4. Run sensor simulator
```bash
docker-compose exec api python scripts/simulate_sensors.py
```

5. Access the application
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Grafana Dashboard: http://localhost:3001

## Development

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Configuration and utilities
│   │   ├── models/        # Database models
│   │   ├── services/      # Business logic
│   │   └── main.py
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── types/
│   └── package.json
├── scripts/               # Utilities and simulators
├── docker-compose.yml
└── README.md
```

## Roadmap

- [x] Core data ingestion pipeline
- [x] Time-series database setup
- [x] Basic analytics engine
- [x] REST API implementation
- [ ] Advanced anomaly detection algorithms
- [ ] Real-time WebSocket updates
- [ ] Mobile-responsive dashboard improvements
- [ ] Export functionality for raw data
- [ ] Multi-tenancy support

## Why This Project?

I built this to explore the intersection of IoT data engineering and industrial safety—a space where data-driven insights can literally save lives. The project demonstrates my ability to:
- Design scalable data pipelines
- Build production-ready APIs
- Create intuitive user interfaces
- Apply ML for predictive analytics
- Write maintainable, tested code

Inspired by companies like Safety.io and MSA Safety that are modernizing industrial safety through connected devices and cloud analytics.

## License

MIT License - feel free to use this project for learning or as a portfolio piece.

## Contact

Questions or feedback? Open an issue or reach out at tditshego70@gmail.com