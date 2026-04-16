#!/bin/bash
# ──────────────────────────────────────────────────────────────────
# SANJAYA EC2 Deployment Bootstrap Script
# ──────────────────────────────────────────────────────────────────
# Usage (from EC2 instance):
#   curl -sSL https://raw.githubusercontent.com/Yashagx/SANJAYA/main/scripts/ec2-deploy.sh | bash
# ──────────────────────────────────────────────────────────────────

set -e

echo "════════════════════════════════════════════════════════════"
echo "SANJAYA EC2 Deployment Bootstrap"
echo "════════════════════════════════════════════════════════════"

# ────────────────────────────────────────────────────────────────
# Step 1: Update system and install prerequisites
# ────────────────────────────────────────────────────────────────
echo "[1/6] Updating system packages..."
sudo yum update -y
sudo yum install -y docker git postgresql wget curl

# ────────────────────────────────────────────────────────────────
# Step 2: Start Docker daemon
# ────────────────────────────────────────────────────────────────
echo "[2/6] Starting Docker service..."
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# ────────────────────────────────────────────────────────────────
# Step 3: Install Docker Compose
# ────────────────────────────────────────────────────────────────
echo "[3/6] Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version

# ────────────────────────────────────────────────────────────────
# Step 4: Clone or update repository
# ────────────────────────────────────────────────────────────────
echo "[4/6] Cloning SANJAYA repository..."
cd /home/ec2-user
if [ -d "sanjaya" ]; then
    cd sanjaya
    git fetch origin
    git checkout main
    git pull origin main
else
    git clone https://github.com/Yashagx/SANJAYA.git sanjaya
    cd sanjaya
fi

# ────────────────────────────────────────────────────────────────
# Step 5: Initialize PostgreSQL database (if not running)
# ────────────────────────────────────────────────────────────────
echo "[5/6] Setting up PostgreSQL..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user if not exists
sudo -u postgres psql << EOPSQL
-- Create user if not exists
DO \$\$ BEGIN
    CREATE USER sanjaya_user WITH PASSWORD 'Sanjaya2026!';
EXCEPTION WHEN duplicate_object THEN
    RAISE NOTICE 'User already exists';
END \$\$;

-- Create database if not exists
SELECT 'CREATE DATABASE sanjaya_db' WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'sanjaya_db'
)\gexec;

-- Grant privileges
ALTER USER sanjaya_user CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE sanjaya_db TO sanjaya_user;
EOPSQL

# ────────────────────────────────────────────────────────────────
# Step 6: Build and start Docker container
# ────────────────────────────────────────────────────────────────
echo "[6/6] Building and starting SANJAYA container..."
docker-compose -f docker-compose.prod.yml down || true
docker-compose -f docker-compose.prod.yml up -d

# Wait for container to be ready
echo "Waiting for application to start..."
sleep 10

# Check health
if curl -sf http://localhost:8000/health > /dev/null; then
    echo "✓ Application started successfully!"
    echo "✓ SANJAYA is running at http://$(hostname -I | awk '{print $1}'):8000"
    echo "✓ Login at http://$(hostname -I | awk '{print $1}'):8000/login"
else
    echo "✗ Health check failed. Check logs:"
    docker-compose -f docker-compose.prod.yml logs sanjaya
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "Deployment Complete!"
echo "════════════════════════════════════════════════════════════"
echo "Next steps:"
echo "1. Create initial admin user:"
echo "   curl -X POST http://localhost:8000/auth/register \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"email\":\"admin@sanjaya.local\",\"password\":\"SecurePassword123!\"}'"
echo ""
echo "2. Login at: http://$(hostname -I | awk '{print $1}'):8000/login"
echo "3. View logs: docker-compose -f docker-compose.prod.yml logs -f sanjaya"
