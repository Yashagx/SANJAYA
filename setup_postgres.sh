#!/bin/bash
set -e

echo "=== PHASE 1: Create SANJAYA database and user ==="

# Create user and database
sudo -u postgres psql <<'EOSQL'
CREATE USER sanjaya_user WITH PASSWORD 'Sanjaya2026!';
CREATE DATABASE sanjaya_db OWNER sanjaya_user;
\c sanjaya_db
GRANT ALL PRIVILEGES ON DATABASE sanjaya_db TO sanjaya_user;
EOSQL

echo "=== User and DB created ==="

# Allow password authentication
sudo sed -i 's/ident/md5/g' /var/lib/pgsql/data/pg_hba.conf
sudo sed -i 's/peer/md5/g' /var/lib/pgsql/data/pg_hba.conf
sudo systemctl restart postgresql

echo "=== Authentication updated, PostgreSQL restarted ==="

# Test connection
PGPASSWORD='Sanjaya2026!' psql -U sanjaya_user -d sanjaya_db -c "SELECT version();"

echo "=== PHASE 2: Create schema ==="

PGPASSWORD='Sanjaya2026!' psql -U sanjaya_user -d sanjaya_db <<'EOSQL'

-- Main risk assessments table
CREATE TABLE IF NOT EXISTS risk_assessments (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    vessel_id VARCHAR(100),
    origin VARCHAR(200),
    destination VARCHAR(200),
    route VARCHAR(400),
    risk_score DECIMAL(5,2),
    risk_level VARCHAR(20),
    recommendation TEXT,
    p_delay DECIMAL(6,4),
    s_weather DECIMAL(6,4),
    s_geo DECIMAL(6,4),
    c_port DECIMAL(6,4),
    customs_risk DECIMAL(6,4),
    weather_condition VARCHAR(200),
    geo_headline TEXT,
    days_real INTEGER,
    days_scheduled INTEGER,
    transport_mode VARCHAR(50) DEFAULT 'sea',
    shap_top_factor VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Rerouting options table
CREATE TABLE IF NOT EXISTS rerouting_options (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER REFERENCES risk_assessments(id),
    route_name VARCHAR(200),
    extra_days INTEGER,
    on_time_probability VARCHAR(10),
    extra_cost VARCHAR(50),
    verdict VARCHAR(100)
);

-- Index for fast risk level queries
CREATE INDEX IF NOT EXISTS idx_risk_level ON risk_assessments(risk_level);
CREATE INDEX IF NOT EXISTS idx_timestamp ON risk_assessments(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_route ON risk_assessments(origin, destination);

-- Verify tables created
\dt

EOSQL

echo "=== Schema created ==="

# Add DATABASE_URL to .env
grep -q "DATABASE_URL" /home/ec2-user/sanjaya/.env 2>/dev/null || echo "DATABASE_URL=postgresql://sanjaya_user:Sanjaya2026!@localhost:5432/sanjaya_db" >> /home/ec2-user/sanjaya/.env
echo "=== .env updated ==="

# Install Python dependencies
source /home/ec2-user/sanjaya/venv/bin/activate
pip install psycopg2-binary sqlalchemy
echo "=== Python deps installed ==="

echo "=== ALL PHASES COMPLETE ==="
