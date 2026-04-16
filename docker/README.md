# SANJAYA Docker Deployment Guide

## Overview

This Docker setup adds an **optional containerized deployment layer** to SANJAYA while preserving 100% of the existing EC2 IP-based deployment. The Docker configuration mirrors the current production setup exactly.

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- Docker & Docker Compose installed
- `.env` file with credentials (copy from `docker/.env.docker`)

### Start Everything
```powershell
# Copy template
Copy-Item docker\.env.docker .env

# Edit .env with your credentials (if needed)
# notepad .env

# Start services
docker-compose up -d

# Watch logs
docker-compose logs -f sanjaya
```

### Verify Health
```powershell
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status":"ok","system":"SANJAYA","version":"2.0.0","brahma":true}
```

### Stop Services
```powershell
docker-compose down
```

---

## 📋 Configuration Reference

### Local Development (`docker-compose.yml`)

| Service | Port | Purpose |
|---------|------|---------|
| `sanjaya` | 8000 | FastAPI application |
| `postgres` | 5432 | PostgreSQL database (optional) |

**Environment Variables:**
- `DATABASE_URL` → postgres:5432 (internal service DNS)
- `AWS_REGION` → ap-south-2
- All API keys from `.env` file

**Database:**
- Auto-initializes using `setup_postgres.sh`
- Persists in `postgres_data` volume
- Schema: `risk_assessments`, `rerouting_options`

---

## 🏭 Production Deployment (EC2)

### Prerequisites
- EC2 instance with Docker & Docker Compose
- PostgreSQL running (on EC2 or AWS RDS)
- EC2 IAM role with Bedrock access (`sanjaya-ec2-role`)

### Option A: Use Existing PostgreSQL (Recommended)

If PostgreSQL is already running on EC2 at localhost:5432:

```bash
# SSH into EC2
ssh -i d:\SANJAYA\sanjaya-key.pem -o StrictHostKeyChecking=no ec2-user@16.112.128.251

# Create .env from template
cp /path/to/docker/.env.prod.docker .env

# Edit .env (set DATABASE_URL if needed)
nano .env

# Start container
docker-compose -f docker-compose.prod.yml up -d

# Verify
curl http://localhost:8000/health
docker-compose -f docker-compose.prod.yml logs -f sanjaya
```

### Option B: Connection String for AWS RDS

If using AWS RDS instead of local PostgreSQL:

```bash
# In .env:
DATABASE_URL=postgresql://user:password@prod-db-instance.ap-south-2.rds.amazonaws.com:5432/sanjaya_db

# Then start:
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🔄 Comparison: Current vs Docker

### EC2 Systemd Service (No Changes)
```bash
# Current: Systemd service still works
sudo systemctl restart sanjaya
sudo journalctl -u sanjaya -f
```

### Docker Alternative (Optional)
```bash
# New: Docker deployment alongside systemd
docker-compose -f docker-compose.prod.yml restart sanjaya
docker-compose -f docker-compose.prod.yml logs -f sanjaya
```

**BOTH can coexist.** The systemd service on port 8000 does NOT conflict with Docker on port 8000 once you choose deployment method.

---

## 🧪 Regression Validation Tests

After starting services, run these to ensure zero regression:

### 1. Health Check
```powershell
curl -X GET http://localhost:8000/health
# Expected: {"status":"ok","system":"SANJAYA","version":"2.0.0","brahma":true}
```

### 2. Predict Endpoint
```powershell
curl -X POST http://localhost:8000/predict `
  -H "Content-Type: application/json" `
  -d @"
{
  "origin": "Mumbai",
  "destination": "Rotterdam",
  "vessel_id": "TEST-VESSEL",
  "days_real": 8,
  "days_scheduled": 5
}
"@
# Expected: Full risk_score, risk_level, breakdown{}, evidence{}
```

### 3. Database Persistence
```powershell
# Check that prediction was saved
docker-compose exec postgres psql -U sanjaya_user -d sanjaya_db -c "SELECT COUNT(*) FROM risk_assessments;"
# Expected: New row inserted
```

### 4. NL Predict (BRAHMA)
```powershell
curl -X POST http://localhost:8000/nlpredict `
  -H "Content-Type: application/json" `
  -d '{"text":"assess shipment from Mumbai to Rotterdam"}'
# Expected: Same risk structure with narrative analysis
```

---

## 🛠️ Common Operations

### View Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs sanjaya

# Live tail
docker-compose logs -f sanjaya

# Last 50 lines
docker-compose logs --tail=50 sanjaya
```

### Restart Services
```bash
# All services
docker-compose restart

# Specific service
docker-compose restart sanjaya

# Force rebuild
docker-compose up -d --build
```

### Execute Commands in Container
```bash
# Run shell
docker-compose exec sanjaya bash

# Run Python
docker-compose exec sanjaya python -c "import sanjaya; print(sanjaya.__version__)"

# Check database connection
docker-compose exec sanjaya python -c "from database import engine; print(engine.url)"
```

### View Container Status
```bash
docker-compose ps

# Output:
# NAME                    STATUS              PORTS
# sanjaya-app            Up 2 minutes         0.0.0.0:8000->8000/tcp
# sanjaya-postgres-dev   Up 2 minutes         0.0.0.0:5432->5432/tcp
```

### Database Operations
```bash
# Connect to postgres
docker-compose exec postgres psql -U sanjaya_user -d sanjaya_db

# Backup database
docker-compose exec postgres pg_dump -U sanjaya_user sanjaya_db > backup.sql

# Restore database
docker-compose exec postgres psql -U sanjaya_user sanjaya_db < backup.sql

# Truncate tables
docker-compose exec postgres psql -U sanjaya_user -d sanjaya_db -c "TRUNCATE risk_assessments CASCADE;"
```

---

## 🚨 Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose logs sanjaya

# Common issues:
# - Port 8000 already in use: docker-compose down && docker-compose up
# - Database connection failed: wait for postgres healthcheck
# - Missing dependencies: docker-compose up --build
```

### Database Connection Failed
```bash
# Test DB connectivity
docker-compose exec sanjaya python -c "
from database import engine
try:
    with engine.connect() as conn:
        print('✓ Database connected')
except Exception as e:
    print(f'✗ Connection failed: {e}')
"
```

### Port 8000 Already In Use
```bash
# Find what's using port 8000
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess

# Kill process (if safe to do so)
Stop-Process -Id <PID> -Force

# Or use different port in docker-compose.yml
# Change "8000:8000" to "8001:8000"
```

### API Gateway Routing (Production)

If using AWS API Gateway to frontend Docker on EC2:

1. **Ensure security group allows inbound on port 8000 from API Gateway**
   ```bash
   # On EC2 security group: Allow 8000 from API Gateway security group
   ```

2. **API Gateway mapping remains unchanged:**
   ```
   https://nxvg8lbkrh.execute-api.ap-south-2.amazonaws.com/prod
   → http://16.112.128.251:8000
   ```

3. **Systemd service OR Docker (choose one):**
   ```bash
   # Systemd (original)
   sudo systemctl restart sanjaya
   
   # OR Docker (new)
   docker-compose -f docker-compose.prod.yml restart
   ```

---

## 📊 File Structure

```
d:\S\SANJAYA\
├── Dockerfile                    # Production/dev image definition
├── docker-compose.yml            # Local dev (with postgres service)
├── docker-compose.prod.yml       # EC2 production (external DB)
├── .dockerignore                 # Build optimization
├── docker/
│   ├── .env.docker              # Dev environment template
│   └── .env.prod.docker         # Prod environment template
└── sanjaya/
    ├── main.py                   # FastAPI app (unchanged)
    ├── requirements_deploy.txt   # Dependencies (unchanged)
    ├── database.py               # PostgreSQL ORM (unchanged)
    ├── sanjaya.service           # Systemd file (unchanged)
    └── agents/                   # Agent modules (unchanged)
```

---

## ✅ Backward Compatibility Checklist

- ✅ Existing systemd service continues working
- ✅ Port 8000 unchanged
- ✅ Database schema preserved
- ✅ API response formats identical
- ✅ All endpoints functional
- ✅ Agent logic untouched
- ✅ AWS IAM role authentication preserved
- ✅ No breaking changes to codebase

---

## 🔐 Security Considerations

### Local Development
- `.env` contains credentials: **ADD TO .gitignore** (already done)
- postgres service runs on localhost:5432 only

### Production (EC2)
- Use **EC2 IAM role** for AWS credentials (recommended)
- Store `.env` securely with restricted permissions:
  ```bash
  chmod 600 .env
  ```
- Use **AWS Secrets Manager** for sensitive data (optional upgrade)
- Database credentials should be strong and managed securely

### Secrets Management
For production, consider:
1. AWS Secrets Manager
2. HashiCorp Vault
3. Environment-only (no .env file)

---

## 📈 Performance Tuning

### Resource Limits (docker-compose.prod.yml)
```yaml
# Adjust for your EC2 instance size:
# t3.micro (1GB RAM): 256m memory limit
# t3.small (2GB RAM): 512m memory limit
# t3.medium (4GB RAM): 1G memory limit (default)
```

### Database Optimization
```bash
# Check query performance
docker-compose exec postgres psql -U sanjaya_user -d sanjaya_db -c "
SELECT COUNT(*) FROM risk_assessments;
SELECT * FROM risk_assessments ORDER BY timestamp DESC LIMIT 5;
"
```

---

## 📞 Support & Common Questions

**Q: Can I run both systemd AND Docker?**
A: No — choose one. They both need port 8000. Stop systemd before Docker: `sudo systemctl stop sanjaya`

**Q: How do I migrate from systemd to Docker?**
A: 1. Stop systemd: `sudo systemctl stop sanjaya`
   2. Run docker: `docker-compose -f docker-compose.prod.yml up -d`
   3. Verify health check passes

**Q: What if the database is on AWS RDS?**
A: Set `DATABASE_URL` to RDS endpoint in `.env` and start docker-compose

**Q: How do I backup the database?**
A: `docker-compose exec postgres pg_dump -U sanjaya_user sanjaya_db > backup.sql`

**Q: Can I deploy to Kubernetes later?**
A: Yes — this Docker setup is Kubernetes-compatible. The Dockerfile and docker-compose serve as the foundation.

---

## 🎯 Next Steps

1. **Local Testing:** Start with `docker-compose up` on your machine
2. **Regression Tests:** Run curl tests above to validate
3. **Production Roll-out:** Move to docker-compose.prod.yml on EC2
4. **Monitoring:** Integrate with CloudWatch or similar
5. **CI/CD:** Push Docker images to ECR or DockerHub

---

## 📝 Changelog

| Date | Change |
|------|--------|
| 2026-04-16 | Initial Docker setup — Phase 2 Implementation |
| | Added Dockerfile, docker-compose.yml/.prod.yml |
| | Added .dockerignore, env templates |
| | Preserved 100% backward compatibility |

---

**Last Updated:** April 16, 2026  
**Status:** ✅ Production Ready
