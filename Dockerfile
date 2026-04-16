# ──────────────────────────────────────────────────────────────────
# SANJAYA Multi-Agent Shipment Risk Intelligence System
# Docker Image — Production & Development
# ──────────────────────────────────────────────────────────────────
# CRITICAL: This Dockerfile preserves 100% of existing FastAPI behavior
# Startup command mirrors EC2 systemd service exactly
# ──────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (layer caching optimization)
COPY sanjaya/requirements_deploy.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_deploy.txt

# Copy entire sanjaya application
COPY sanjaya/ .

# Expose port (same as EC2 deployment)
EXPOSE 8000

# Health check (validates container liveness)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ──────────────────────────────────────────────────────────────────
# STARTUP COMMAND: Identical to EC2 systemd service
# ──────────────────────────────────────────────────────────────────
# EC2 Command: /home/ec2-user/sanjaya/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
# Docker Command (below): uvicorn main:app --host 0.0.0.0 --port 8000
# ──────────────────────────────────────────────────────────────────

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
