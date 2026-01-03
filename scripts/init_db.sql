-- Initialize TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Create schemas for organization
CREATE SCHEMA IF NOT EXISTS sensor_data;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS reports;

-- Set search path
SET search_path TO public, sensor_data, analytics, reports;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA sensor_data TO safety_user;
GRANT ALL PRIVILEGES ON SCHEMA analytics TO safety_user;
GRANT ALL PRIVILEGES ON SCHEMA reports TO safety_user;

-- Create custom types
DO $$ BEGIN
    CREATE TYPE sensor_status AS ENUM ('active', 'inactive', 'maintenance', 'fault');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE alert_severity AS ENUM ('low', 'medium', 'high', 'critical');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Initial database setup complete
SELECT 'Database initialization complete' AS status;