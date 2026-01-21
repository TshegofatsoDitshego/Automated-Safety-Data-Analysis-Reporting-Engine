-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create enum types for better data integrity
CREATE TYPE equipment_type AS ENUM ('gas_detector', 'temperature_sensor', 'pressure_sensor', 'location_tracker', 'air_quality_monitor');
CREATE TYPE equipment_status AS ENUM ('active', 'maintenance', 'retired', 'calibration_needed');
CREATE TYPE alert_severity AS ENUM ('info', 'warning', 'critical', 'emergency');
CREATE TYPE sensor_reading_status AS ENUM ('normal', 'warning', 'critical', 'offline');

-- Equipment registry table
CREATE TABLE IF NOT EXISTS equipment (
    equipment_id VARCHAR(50) PRIMARY KEY,
    equipment_type equipment_type NOT NULL,
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    serial_number VARCHAR(100) UNIQUE,
    installation_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_calibration_date TIMESTAMP WITH TIME ZONE,
    next_calibration_due TIMESTAMP WITH TIME ZONE,
    location VARCHAR(200),
    status equipment_status DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Time-series sensor readings table (will be converted to hypertable)
CREATE TABLE IF NOT EXISTS sensor_readings (
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    equipment_id VARCHAR(50) NOT NULL,
    metric_name VARCHAR(50) NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    metric_unit VARCHAR(20),
    reading_status sensor_reading_status DEFAULT 'normal',
    metadata JSONB,
    FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id) ON DELETE CASCADE
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('sensor_readings', 'time', if_not_exists => TRUE);

-- Create composite index for faster queries
CREATE INDEX IF NOT EXISTS idx_sensor_readings_equipment_time 
    ON sensor_readings (equipment_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_sensor_readings_metric 
    ON sensor_readings (metric_name, time DESC);
CREATE INDEX IF NOT EXISTS idx_sensor_readings_status 
    ON sensor_readings (reading_status, time DESC) WHERE reading_status != 'normal';

-- Enable compression for older data (after 7 days)
ALTER TABLE sensor_readings SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'equipment_id, metric_name'
);

SELECT add_compression_policy('sensor_readings', INTERVAL '7 days');

-- Alerts table for anomaly detection
CREATE TABLE IF NOT EXISTS alerts (
    alert_id SERIAL PRIMARY KEY,
    equipment_id VARCHAR(50) NOT NULL,
    alert_type VARCHAR(100) NOT NULL,
    severity alert_severity NOT NULL,
    message TEXT NOT NULL,
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_alerts_equipment_id ON alerts(equipment_id);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity, triggered_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_unresolved ON alerts(triggered_at DESC) WHERE resolved_at IS NULL;

-- Compliance reports table
CREATE TABLE IF NOT EXISTS compliance_reports (
    report_id SERIAL PRIMARY KEY,
    report_type VARCHAR(50) NOT NULL,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    file_path VARCHAR(500),
    summary JSONB,
    created_by VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_reports_period ON compliance_reports(period_start, period_end);

-- Data quality metrics table for monitoring pipeline health
CREATE TABLE IF NOT EXISTS data_quality_metrics (
    metric_id SERIAL PRIMARY KEY,
    check_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_records_processed BIGINT,
    invalid_records INTEGER,
    duplicate_records INTEGER,
    late_arriving_records INTEGER,
    processing_time_ms INTEGER,
    pipeline_stage VARCHAR(50),
    metadata JSONB
);

-- Materialized view for equipment health summary (updated periodically)
CREATE MATERIALIZED VIEW IF NOT EXISTS equipment_health_summary AS
SELECT 
    e.equipment_id,
    e.equipment_type,
    e.status,
    e.location,
    COUNT(DISTINCT DATE(sr.time)) as days_active_last_30,
    AVG(CASE WHEN sr.reading_status = 'critical' THEN 1 ELSE 0 END) as critical_rate,
    MAX(sr.time) as last_reading_time,
    COUNT(a.alert_id) as alert_count_last_30
FROM equipment e
LEFT JOIN sensor_readings sr ON e.equipment_id = sr.equipment_id 
    AND sr.time > NOW() - INTERVAL '30 days'
LEFT JOIN alerts a ON e.equipment_id = a.equipment_id 
    AND a.triggered_at > NOW() - INTERVAL '30 days'
GROUP BY e.equipment_id, e.equipment_type, e.status, e.location;

CREATE UNIQUE INDEX ON equipment_health_summary(equipment_id);

-- Continuous aggregate for hourly metrics (auto-refreshing)
CREATE MATERIALIZED VIEW sensor_readings_hourly
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', time) AS bucket,
    equipment_id,
    metric_name,
    AVG(metric_value) as avg_value,
    MIN(metric_value) as min_value,
    MAX(metric_value) as max_value,
    STDDEV(metric_value) as stddev_value,
    COUNT(*) as reading_count
FROM sensor_readings
GROUP BY bucket, equipment_id, metric_name;

-- Auto-refresh policy for continuous aggregate
SELECT add_continuous_aggregate_policy('sensor_readings_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

-- Data retention policy: keep raw data for 90 days
SELECT add_retention_policy('sensor_readings', INTERVAL '90 days');

-- Function to automatically update equipment updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_equipment_updated_at BEFORE UPDATE ON equipment
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();