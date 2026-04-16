# SANJAYA Docker Quick Reference

## Start Local Development (Windows PowerShell)
```powershell
docker-compose up -d
docker-compose logs -f sanjaya
curl http://localhost:8000/health
```

## Start Production (EC2 SSH)
```bash
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml logs -f sanjaya
curl http://localhost:8000/health
```

## Stop All Services
```powershell
# Local
docker-compose down

# Production
docker-compose -f docker-compose.prod.yml down
```

## Restart Application
```powershell
# Local
docker-compose restart sanjaya

# Production
docker-compose -f docker-compose.prod.yml restart sanjaya
```

## View Logs
```powershell
docker-compose logs -f sanjaya
```

## Test Endpoints
```powershell
# Health
curl http://localhost:8000/health

# Predict
curl -X POST http://localhost:8000/predict `
  -H "Content-Type: application/json" `
  -d '{"origin":"Mumbai","destination":"Rotterdam","days_real":8,"days_scheduled":5}'

# NL Predict
curl -X POST http://localhost:8000/nlpredict `
  -H "Content-Type: application/json" `
  -d '{"text":"assess Mumbai to Rotterdam shipment"}'
```

## Check Database
```powershell
docker-compose exec postgres psql -U sanjaya_user -d sanjaya_db -c "SELECT COUNT(*) FROM risk_assessments;"
```

## Troubleshooting

**Port 8000 already in use?**
```powershell
Get-NetTCPConnection -LocalPort 8000
Stop-Process -Id <PID> -Force
```

**Container won't start?**
```powershell
docker-compose logs sanjaya
docker-compose up --build
```

**Database connection failed?**
```powershell
docker-compose ps
docker-compose restart postgres
docker-compose logs postgres
```

## Files Reference
- **Dockerfile** → Image definition (mirroring EC2 systemd startup)
- **docker-compose.yml** → Local dev with postgres
- **docker-compose.prod.yml** → EC2 production (external DB)
- **docker/.env.docker** → Dev environment template
- **docker/.env.prod.docker** → Production environment template
- **docker/README.md** → Full documentation

## Important Notes

✅ **Backward Compatible:** Existing EC2 systemd service UNCHANGED  
✅ **Port 8000:** Same as production  
✅ **Zero Regression:** All API responses identical  
✅ **Optional Layer:** Choose Docker OR systemd, not both  

For full documentation, see [docker/README.md](docker/README.md)
