-- Database initialization script
-- This script is automatically executed when the PostgreSQL container starts

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create custom UUID generation function (PostgreSQL 14+ alternative)
CREATE OR REPLACE FUNCTION gen_random_uuid() RETURNS uuid AS $$
SELECT uuid_generate_v4();
$$ LANGUAGE SQL;

-- Create database user if not exists (handled by environment variables in docker-compose)
-- The database and user are already created by PostgreSQL container initialization

-- Set timezone
SET timezone = 'Asia/Shanghai';

-- Create schemas if needed (optional)
-- CREATE SCHEMA IF NOT EXISTS headhunter;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE headhunter_platform TO headhunter_user;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Database initialization completed successfully';
END
$$;