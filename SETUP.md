# Setup Guide

## Prerequisites
- Python 3.11+
- Docker & Docker Compose (for containerized setup)
- PostgreSQL 14+ with TimescaleDB (for local setup)
- Redis (for local setup)

## Quick Start with Docker (Recommended)

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/automated-safety-analysis.git
cd automated-safety-analysis
```

2. **Copy environment file**
```bash
cp .env.example .env
# Edit .env if needed (default values work with Docker)
```

3. **Start all services**
```bash
docker-compose up -d
```

4. **Check service health**
```bash
docker-compose ps
```

5. **Run database migrations**
```bash
docker-compose exec api alembic upgrade head
```

6. **Access the application**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Flower (Celery Monitor): http://localhost:5555

7. **Generate sample data (optional)**
```bash
docker-compose exec api python scripts/generate_sample_data.py --sensors 50 --days 7
```

## Local Development Setup (Without Docker)

1. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

3. **Install and setup PostgreSQL with TimescaleDB**
```bash
# On macOS with Homebrew
brew install timescaledb

# On Ubuntu
sudo add-apt-repository ppa:timescale/timescaledb-ppa
sudo apt update
sudo apt install timescaledb-postgresql-14

# Initialize TimescaleDB
sudo timescaledb-tune

# Create database
createdb safety_db
psql -d safety_db -c "CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"
```

4. **Install and start Redis**
```bash
# On macOS
brew install redis
brew services start redis

# On Ubuntu
sudo apt install redis-server
sudo systemctl start redis
```

5. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your local database credentials
```

6. **Run migrations**
```bash
alembic upgrade head
```

7. **Start the application**

Terminal 1 - API Server:
```bash
uvicorn app.main:app --reload
```

Terminal 2 - Celery Worker:
```bash
celery -A app.core.celery_app worker --loglevel=info
```

Terminal 3 - Celery Beat (scheduled tasks):
```bash
celery -A app.core.celery_app beat --loglevel=info
```

## Verify Installation

```bash
# Check API health
curl http://localhost:8000/health

# View API documentation
open http://localhost:8000/docs
```

## Common Issues

### Docker port conflicts
If ports 5432, 6379, or 8000 are already in use:
```bash
# Stop the conflicting services or modify ports in docker-compose.yml
```

### Database connection errors
```bash
# Check PostgreSQL is running
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

### Celery worker not processing tasks
```bash
# Check Redis connection
docker-compose logs redis

# Restart worker
docker-compose restart celery_worker
```

## Next Steps

Once setup is complete:
1. Review the API documentation at `/docs`
2. Generate sample data for testing
3. Explore the example requests in `examples/`
4. Run the test suite: `pytest`

## Development Workflow

```bash
# Make code changes
# ...

# Format code
black app/ tests/
isort app/ tests/

# Run linters
flake8 app/ tests/
mypy app/

# Run tests
pytest

# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```