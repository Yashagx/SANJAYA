#!/bin/bash
# ──────────────────────────────────────────────────────────────────
# SANJAYA Quick Deploy Script (Run on EC2 Instance)
# ──────────────────────────────────────────────────────────────────
# This script handles the complete deployment on a fresh EC2 instance
# Usage: bash deploy.sh
# ──────────────────────────────────────────────────────────────────

set -e

REPO_URL="https://github.com/Yashagx/SANJAYA.git"
APP_DIR="/home/ec2-user/sanjaya"

echo "════════════════════════════════════════════════════════════"
echo "SANJAYA EC2 Quick Deployment"
echo "════════════════════════════════════════════════════════════"

# ────────────────────────────────────────────────────────────────
# 1. Install System Dependencies
# ────────────────────────────────────────────────────────────────
echo "[1/7] Installing system dependencies..."
sudo yum update -y > /dev/null 2>&1
sudo yum install -y docker git postgresql wget curl > /dev/null 2>&1
echo "✓ System dependencies installed"

# ────────────────────────────────────────────────────────────────
# 2. Start and Enable Docker
# ────────────────────────────────────────────────────────────────
echo "[2/7] Starting Docker service..."
sudo systemctl start docker || true
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user || true
echo "✓ Docker service started"

# ────────────────────────────────────────────────────────────────
# 3. Install Docker Compose
# ────────────────────────────────────────────────────────────────
echo "[3/7] Installing Docker Compose..."
DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d'"' -f4)
sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose 2>/dev/null
sudo chmod +x /usr/local/bin/docker-compose
echo "✓ Docker Compose installed: $(docker-compose --version)"

# ────────────────────────────────────────────────────────────────
# 4. Clone/Update Repository
# ────────────────────────────────────────────────────────────────
echo "[4/7] Cloning SANJAYA repository..."
if [ -d "$APP_DIR" ]; then
    echo "Repository exists, updating..."
    cd "$APP_DIR"
    git fetch origin >> /dev/null 2>&1
    git checkout main >> /dev/null 2>&1
    git pull origin main >> /dev/null 2>&1
else
    echo "Cloning fresh repository..."
    git clone $REPO_URL $APP_DIR >> /dev/null 2>&1
    cd "$APP_DIR"
fi
echo "✓ Repository ready"

# ────────────────────────────────────────────────────────────────
# 5. Initialize PostgreSQL
# ────────────────────────────────────────────────────────────────
echo "[5/7] Setting up PostgreSQL database..."
sudo systemctl start postgresql >> /dev/null 2>&1 || true
sudo systemctl enable postgresql >> /dev/null 2>&1 || true

# Wait a bit for PostgreSQL to start
sleep 2

# Create database user and schema
sudo -u postgres psql << EOPSQL > /dev/null 2>&1
DO \$\$ BEGIN
    CREATE USER sanjaya_user WITH PASSWORD 'Sanjaya2026!';
EXCEPTION WHEN duplicate_object THEN
    RAISE NOTICE 'User sanjaya_user already exists';
END \$\$;

DO \$\$ BEGIN
    CREATE DATABASE sanjaya_db;
EXCEPTION WHEN duplicate_database THEN
    RAISE NOTICE 'Database sanjaya_db already exists';
END \$\$;

ALTER USER sanjaya_user CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE sanjaya_db TO sanjaya_user;
EOPSQL

echo "✓ PostgreSQL database initialized"

# ────────────────────────────────────────────────────────────────
# 6. Build Docker Image
# ────────────────────────────────────────────────────────────────
echo "[6/7] Building Docker image..."
cd "$APP_DIR"

# Stop existing containers
docker-compose -f docker-compose.prod.yml down > /dev/null 2>&1 || true

# Build new image
docker-compose -f docker-compose.prod.yml build --no-cache > /dev/null 2>&1
echo "✓ Docker image built"

# ────────────────────────────────────────────────────────────────
# 7. Start Application
# ────────────────────────────────────────────────────────────────
echo "[7/7] Starting SANJAYA application..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for startup
sleep 15

# Check health
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ Application is running!"
else
    echo "⚠ Health check pending (container may still be starting)"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✓ DEPLOYMENT COMPLETE!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📝 Next Steps:"
echo ""
echo "1️⃣  Create an admin user:"
echo "   curl -X POST http://localhost:8000/auth/register \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"email\":\"admin@example.com\",\"password\":\"YourPassword123!\"}'"
echo ""
echo "2️⃣  Login to the application:"
echo "   Open: http://$(hostname -I | awk '{print $1}'):8000/login"
echo ""
echo "3️⃣  View application logs:"
echo "   docker-compose -f docker-compose.prod.yml logs -f sanjaya"
echo ""
echo "4️⃣  Restart application:"
echo "   docker-compose -f docker-compose.prod.yml restart"
echo ""
echo "5️⃣  Stop application:"
echo "   docker-compose -f docker-compose.prod.yml down"
echo ""
echo "📊 Application Info:"
echo "   URL: http://$(hostname -I | awk '{print $1}'):8000"
echo "   Features: Risk Assessment + Login System"
echo ""
echo "🆘 Troubleshooting:"
echo "   docker logs sanjaya-app-prod          # Check container logs"
echo "   curl http://localhost:8000/health    # Check health status"
echo ""
echo "════════════════════════════════════════════════════════════"
