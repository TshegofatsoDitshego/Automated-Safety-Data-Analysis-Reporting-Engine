# Setup Recommendations

## For 8GB RAM Systems
Use the lightweight setup:
```bash
pip install -r requirements.lite.txt
cp .env.lite .env
uvicorn app.main:app --reload
```

## For 16GB+ RAM Systems
Use the full Docker setup:
```bash
docker-compose up -d
```
