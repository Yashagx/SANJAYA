#!/bin/bash
# ══════════════════════════════════════════════════════════════════
#  SANJAYA Auth — EC2 Deploy Script (no Docker required)
#  Run from inside the project directory:  bash deploy.sh
# ══════════════════════════════════════════════════════════════════
set -e
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE="sanjaya-auth"
PORT=8000

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SANJAYA Auth — EC2 Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. System packages
sudo yum update -y
sudo yum install -y python3

# 2. Python virtual environment
cd "$APP_DIR"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Write systemd service
sudo tee /etc/systemd/system/${SERVICE}.service > /dev/null <<EOF
[Unit]
Description=SANJAYA Auth Service
After=network.target

[Service]
User=$USER
WorkingDirectory=${APP_DIR}
EnvironmentFile=${APP_DIR}/.env
ExecStart=${APP_DIR}/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 4. Enable & start
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE}
sudo systemctl restart ${SERVICE}

echo ""
echo "✅  Service started!"
echo ""
echo "   Auth Portal → http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):${PORT}"
echo "   Health check → http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):${PORT}/health"
echo "   API docs     → http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):${PORT}/docs"
echo ""
echo "   Logs: sudo journalctl -u ${SERVICE} -f"
