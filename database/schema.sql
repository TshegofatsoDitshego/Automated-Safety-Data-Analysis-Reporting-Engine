CREATE TABLE IF NOT EXISTS raw_events (
    id SERIAL PRIMARY KEY,
    device_id TEXT,
    event_type TEXT,
    severity INT,
    event_time TIMESTAMP,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS processed_events (
    id SERIAL PRIMARY KEY,
    device_id TEXT,
    event_type TEXT,
    severity INT,
    event_time TIMESTAMP
);

CREATE TABLE IF NOT EXISTS safety_metrics (
    device_id TEXT,
    total_events INT,
    avg_severity FLOAT
);