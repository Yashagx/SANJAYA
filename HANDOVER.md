# SANJAYA Project Handover Documentation

## Project Overview
SANJAYA is a multi-agent shipment risk intelligence system built with FastAPI, PostgreSQL, and Groq-powered AI integration.

- Repository: https://github.com/Yashagx/SANJAYA
- Branch: `main`
- Current deployment target: AWS EC2
- Last updated: April 16, 2026

## Credential Safety (Read First)
This handover intentionally redacts secrets.

- Do not store live credentials in tracked files.
- Keep production secrets only in untracked runtime env files (for example `/root/.env.prod` on EC2).
- Rotate any credential that was previously shared in plaintext.

## 1. AWS and EC2 Configuration

- Region: `ap-south-2` (Mumbai)
- Instance IP: `16.112.128.251`
- Recommended instance type: `t3.medium` or higher
- OS: Amazon Linux 2023
- SSH key path (local): `d:\SANJAYA\sanjaya-key.pem`

### SSH Access
```bash
ssh -i d:/SANJAYA/sanjaya-key.pem ec2-user@16.112.128.251
chmod 400 sanjaya-key.pem
```

### Required EC2 Packages
```bash
sudo yum install docker -y
sudo yum install docker-compose -y
sudo yum install postgresql -y
sudo yum install git -y
```

## 2. Database Configuration

PostgreSQL runs locally on EC2 (`localhost:5432`).

- Database: `sanjaya_db`
- Username: `sanjaya_user`
- Password: set in `.env.prod` only (redacted here)

### Initialize DB
```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE sanjaya_db;
CREATE USER sanjaya_user WITH PASSWORD '<REDACTED_DB_PASSWORD>';
ALTER ROLE sanjaya_user SET client_encoding TO 'utf8';
ALTER ROLE sanjaya_user SET default_transaction_isolation TO 'read committed';
GRANT ALL PRIVILEGES ON DATABASE sanjaya_db TO sanjaya_user;
```

### Env-style URL
```text
postgresql://sanjaya_user:<REDACTED_DB_PASSWORD>@localhost:5432/sanjaya_db
```

## 3. Environment Variables

```bash
DATABASE_URL=postgresql://sanjaya_user:<REDACTED_DB_PASSWORD>@localhost:5432/sanjaya_db
GROQ_API_KEY=<REDACTED_GROQ_KEY>
JWT_SECRET_KEY=<STRONG_RANDOM_SECRET>
ENCRYPTION_KEY=<STRONG_RANDOM_SECRET>
AWS_REGION=ap-south-2
ENVIRONMENT=docker-prod
```

Optional AWS credentials are only needed if AWS APIs are called directly.

## 4. Docker Deployment

### Build and Run
```bash
cd /home/ec2-user/sanjaya
sudo docker build -t sanjaya:prod .

sudo docker run -d \
  --name sanjaya-app \
  --network host \
  --env-file /root/.env.prod \
  sanjaya:prod
```

### Compose Alternative
```bash
sudo docker-compose -f docker-compose.prod.yml up -d
```

### Useful Commands
```bash
sudo docker logs sanjaya-app -f
sudo docker ps | grep sanjaya
sudo docker restart sanjaya-app
sudo docker stop sanjaya-app
sudo docker rm sanjaya-app
sudo docker images | grep sanjaya
```

## 5. Core File Layout

```text
sanjaya/
|- main.py
|- auth.py
|- database.py
|- logger_module.py
|- dashboard.html
|- requirements.txt
|- agents/
   |- brahma.py
   |- nidhi.py
   |- vayu.py
   |- sanchar.py
   |- darpana.py
   |- viveka.py
   |- marga.py
   |- akasha.py
   |- arjuna.py
   |- kavach.py
```

Deploy these root files too:

- `Dockerfile`
- `docker-compose.prod.yml`

## 6. Exclude from Deployment and Git

Do not deploy or commit the following:

- `sanjaya/data/*.csv`
- `sanjaya/data/archive/`
- `test_*.py`
- `test_*.csv`
- `__pycache__/`
- `*.pyc`
- `.env*`
- `*.pem`

## 7. API Endpoints

### Health
```bash
curl http://16.112.128.251:8000/health
```

### Authentication
```bash
curl -X POST http://16.112.128.251:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123!"}'

curl -X POST http://16.112.128.251:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123!"}'

curl -H "Authorization: Bearer <token>" http://16.112.128.251:8000/auth/me
```

### Prediction
```bash
curl -X POST http://16.112.128.251:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"origin":"Shanghai","destination":"Rotterdam","vessel_id":"MV-001","transport_mode":"sea"}'
```

### Chat
```bash
curl -X POST http://16.112.128.251:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What is typical delivery time from Shanghai to Rotterdam?"}'
```

### Natural Language Predict
```bash
curl -X POST http://16.112.128.251:8000/nlpredict \
  -H "Content-Type: application/json" \
  -d '{"text":"Shipment from India to US, urgent, via air. Monsoon season risk?"}'
```

## 8. Troubleshooting

### Container will not start
```bash
sudo docker logs sanjaya-app
```

Common causes:

- invalid or expired Groq key
- PostgreSQL service down
- port 8000 conflict

### Groq 401 errors
Regenerate key in Groq console, update `/root/.env.prod`, restart container.

### Database connection failure
```bash
sudo systemctl status postgresql
sudo systemctl start postgresql
PGPASSWORD='<REDACTED_DB_PASSWORD>' psql -U sanjaya_user -h localhost -d sanjaya_db -c "SELECT 1"
```

## 9. Local to EC2 Deployment Flow

```bash
cd d:/S/SANJAYA
scp -i d:/SANJAYA/sanjaya-key.pem -r sanjaya/agents ec2-user@16.112.128.251:/home/ec2-user/sanjaya/
ssh -i d:/SANJAYA/sanjaya-key.pem ec2-user@16.112.128.251 "sudo docker restart sanjaya-app"
```

For full deployment use:

- `deploy.sh`
- `deploy-to-ec2.ps1`
- `EC2_DEPLOYMENT_GUIDE.md`

## 10. Security and Operations TODO

- Rotate JWT and encryption secrets regularly.
- Add endpoint rate limiting.
- Enable HTTPS with reverse proxy (for example Nginx).
- Add automated PostgreSQL backups.
- Add Redis caching for expensive agent outputs.
- Add database indexes for frequent query paths.

## 11. Monitoring

```bash
ssh -i d:/SANJAYA/sanjaya-key.pem ec2-user@16.112.128.251 "sudo docker logs sanjaya-app -f"
ssh -i d:/SANJAYA/sanjaya-key.pem ec2-user@16.112.128.251 "sudo docker exec sanjaya-app tail -f logs/app.log"
```

Important log markers:

- `[BRAHMA]` for AI calls
- `Chat message:` for `/chat`
- `Risk assessment:` for prediction flow
- `ERROR` for failures

## 12. Quick Continuation Checklist

1. Confirm EC2 instance health and SSH access.
2. Validate `/root/.env.prod` exists and is not committed to Git.
3. Check PostgreSQL service status.
4. Rebuild and restart `sanjaya-app` after code updates.
5. Run `/health`, `/predict`, and `/chat` smoke tests.
6. Review live container logs for runtime errors.

## 13. Immediate Risk Follow-up

- Remove secrets from Git history if previously committed.
- Rotate exposed credentials (Groq key, DB password, JWT secret, encryption key).
- Replace any default or shared admin credentials.

