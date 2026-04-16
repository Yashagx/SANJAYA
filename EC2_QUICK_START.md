# 🚀 SANJAYA EC2 Deployment - Quick Start

## ⚡ TL;DR - Deploy in 2 Minutes

### From Your Windows Machine:

```powershell
cd D:\S\SANJAYA
git add -A
git commit -m "ec2 deployment"
git push origin main

# Then run:
.\deploy-to-ec2.ps1 -KeyPath "d:\SANJAYA\sanjaya-key.pem" -InstanceIP "16.112.128.251"
```

**Done!** Your app is now at: `http://16.112.128.251:8000`

---

## 📋 What Was Fixed

✅ **Created .env.prod** - Production environment configuration  
✅ **Created deploy.sh** - One-click deployment script  
✅ **Created deploy-to-ec2.ps1** - Windows PowerShell deployment  
✅ **Updated docker-compose.prod.yml** - Proper environment loading  
✅ **Added EC2_DEPLOYMENT_GUIDE.md** - Complete troubleshooting guide  
✅ **Added LOGIN_SYSTEM.md** - User registration/login documentation  

---

## 🔐 Create Your First Login Account

After deployment completes, SSH into your EC2 and create a login:

```bash
ssh -i d:\SANJAYA\sanjaya-key.pem ec2-user@16.112.128.251

# Create admin user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"YourPassword123!"}'
```

Then login at: `http://16.112.128.251:8000/login`

---

## 📚 Full Documentation

- **EC2_DEPLOYMENT_GUIDE.md** - Complete deployment & troubleshooting
- **LOGIN_SYSTEM.md** - User registration, login, and JWT tokens
- **deploy.sh** - Linux deployment script
- **deploy-to-ec2.ps1** - Windows PowerShell deployment
- **.env.prod** - Production configuration template

---

## ✅ Verify Your Deployment

```bash
# Check app is running
curl http://16.112.128.251:8000/health

# View logs
ssh -i d:\SANJAYA\sanjaya-key.pem ec2-user@16.112.128.251 \
  docker logs -f sanjaya-app-prod
```

---

## 🆘 Troubleshooting

If you encounter issues, see **EC2_DEPLOYMENT_GUIDE.md** for:
- Connection refused errors
- Database connection issues
- Docker build failures
- Permission problems

---

## 🎯 Next Steps

1. ✅ Deploy using `deploy-to-ec2.ps1`
2. ✅ Create first user via registration endpoint
3. ✅ Login at `http://16.112.128.251:8000/login`
4. ✅ Test risk assessment APIs
5. ✅ Configure API keys in `.env.prod`

**That's it! Your SANJAYA system is ready to go! 🎉**
