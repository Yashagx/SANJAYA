# SANJAYA EC2 Deployment & Troubleshooting Guide

## 🚀 Quick Start (Fastest Way)

### Option 1: From Your Windows Machine (Recommended)

```powershell
# Open PowerShell in the repo directory and run:
.\deploy-to-ec2.ps1 -KeyPath "d:\SANJAYA\sanjaya-key.pem" -InstanceIP "16.112.128.251"
```

This will:
1. Push your latest code to GitHub
2. SSH into your EC2 instance
3. Clone/update the repository
4. Install all dependencies
5. Set up PostgreSQL
6. Build and start Docker containers
7. Create login system

**That's it! Your app will be running at: `http://16.112.128.251:8000`**

---

### Option 2: Manually SSH into EC2 and Run

```bash
# 1. SSH into your EC2
ssh -i d:\SANJAYA\sanjaya-key.pem ec2-user@16.112.128.251

# 2. Clone/navigate to repo
cd /home/ec2-user/sanjaya
git pull origin main

# 3. Run deployment script
chmod +x deploy.sh
./deploy.sh
```

---

## 🔑 Creating Your First Admin User

After deployment completes, create a login account:

```bash
# SSH into EC2
ssh -i your-key.pem ec2-user@16.112.128.251

# Create admin user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"YourPassword123!"}'
```

You should see:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user_email": "admin@example.com",
  "is_admin": false
}
```

Then login at: `http://16.112.128.251:8000/login`

---

## 🆘 Troubleshooting

### Problem 1: "Connection refused" on http://IP:8000

**Solution:**
```bash
# SSH into EC2
ssh -i your-key.pem ec2-user@16.112.128.251

# Check if container is running
docker ps | grep sanjaya

# If not running, check logs
docker logs sanjaya-app-prod

# Restart the service
cd ~/sanjaya
docker-compose -f docker-compose.prod.yml restart

# Wait 10 seconds and try again
sleep 10
curl http://localhost:8000/health
```

---

### Problem 2: "Database connection error"

**Solution:**
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start PostgreSQL if needed
sudo systemctl start postgresql

# Verify database exists
sudo -u postgres psql -l | grep sanjaya_db

# If not, initialize it
sudo bash setup_postgres.sh
```

---

### Problem 3: "Docker cannot find image"

**Solution:**
```bash
# Rebuild the image
cd ~/sanjaya
docker-compose -f docker-compose.prod.yml build --no-cache

# Then restart
docker-compose -f docker-compose.prod.yml up -d
```

---

### Problem 4: "Permission denied" on .pem file

**Solution (Windows PowerShell):**
```powershell
$KeyPath = "d:\SANJAYA\sanjaya-key.pem"
icacls $KeyPath /inheritance:r
icacls $KeyPath /grant:r "$($env:USERNAME):(F)"
```

---

## 📊 Common Commands

### View Application Logs
```bash
# Real-time logs
ssh -i key.pem ec2-user@16.112.128.251 \
  docker logs -f sanjaya-app-prod

# Last 100 lines
ssh -i key.pem ec2-user@16.112.128.251 \
  docker logs --tail 100 sanjaya-app-prod
```

### Restart Application
```bash
ssh -i key.pem ec2-user@16.112.128.251 \
  'cd ~/sanjaya && docker-compose -f docker-compose.prod.yml restart'
```

### Stop Application
```bash
ssh -i key.pem ec2-user@16.112.128.251 \
  'cd ~/sanjaya && docker-compose -f docker-compose.prod.yml down'
```

### Check Health Status
```bash
ssh -i key.pem ec2-user@16.112.128.251 \
  curl -s http://localhost:8000/health
```

---

## 🔧 Manual Configuration

If you need to manually configure environment variables:

1. SSH into EC2
2. Edit `.env.prod`:
   ```bash
   nano ~/sanjaya/.env.prod
   ```
3. Update the values:
   ```env
   DATABASE_URL=postgresql://sanjaya_user:YourPassword@localhost:5432/sanjaya_db
   JWT_SECRET_KEY=your-very-secure-secret-key
   AWS_ACCESS_KEY_ID=your_aws_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret
   OPENWEATHER_API_KEY=your_weather_api_key
   NEWSCATCHER_API_KEY=your_news_api_key
   OPENAI_API_KEY=your_openai_key
   ```
4. Restart the service:
   ```bash
   cd ~/sanjaya
   docker-compose -f docker-compose.prod.yml restart
   ```

---

## ✅ Verify Deployment

After deployment, check these endpoints:

```bash
# Health check
curl http://16.112.128.251:8000/health

# Login page
curl http://16.112.128.251:8000/login

# API is ready
echo "✓ Application is running!"
```

---

## 📈 Next Steps

1. **Create a user**: Register via `/auth/register` endpoint
2. **Login**: Go to `http://IP:8000/login`
3. **Test features**: Use the risk assessment APIs
4. **Configure APIs**: Add your weather, news, and OpenAI API keys
5. **Set up monitoring**: See SECURITY_OBSERVABILITY.md for Prometheus/Grafana

---

## 🆘 Still Having Issues?

Run this diagnostic script:

```bash
ssh -i key.pem ec2-user@16.112.128.251 << 'EOF'
echo "=== System Info ==="
uname -a
echo ""
echo "=== Docker Status ==="
docker --version
docker-compose --version
echo ""
echo "=== Running Containers ==="
docker ps
echo ""
echo "=== PostgreSQL Status ==="
sudo systemctl status postgresql
echo ""
echo "=== App Logs (Last 20 lines) ==="
docker logs --tail 20 sanjaya-app-prod
echo ""
echo "=== Network Test ==="
curl -s http://localhost:8000/health | head -20
EOF
```

---

## 📞 Support

If you're still stuck:
1. Check the deployment script output for errors
2. Check `docker logs sanjaya-app-prod` for application errors
3. Verify PostgreSQL is running: `sudo systemctl status postgresql`
4. Verify DNS/networking: `curl http://localhost:8000/health`

**Good luck! Your SANJAYA system should be up and running now! 🚀**
