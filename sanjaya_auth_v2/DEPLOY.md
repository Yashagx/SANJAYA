# SANJAYA Auth — EC2 Deployment Guide

No Docker. No Postgres. Just Python + SQLite running as a systemd service.

---

## What's included

| Feature | Detail |
|---|---|
| MFA | Email OTP via Gmail SMTP |
| RBAC | admin / manager / user roles |
| Admin panel | Manage users, view audit logs, stats |
| Manager panel | Read-only team view |
| After login | Redirects to `http://16.112.128.251:8000/dashboard#` |
| Database | SQLite (zero setup) — swap to Postgres via `.env` |

---

## Step 1 — Copy files to EC2

```bash
# From your local machine:
scp -i sanjaya-key.pem -r sanjaya_auth_v2/ ec2-user@18.61.252.222:~/
```

---

## Step 2 — SSH in and deploy

```bash
ssh -i sanjaya-key.pem ec2-user@18.61.252.222
cd ~/sanjaya_auth_v2
chmod +x deploy.sh
bash deploy.sh
```

This will:
- Install Python packages into a virtual environment
- Register and start a **systemd service** on port **8001**
- Auto-restart on crash/reboot

---

## Step 3 — Open port 8001 in AWS Security Group

In the EC2 console → Security Groups → Inbound rules → Add:
- Type: Custom TCP
- Port: 8001
- Source: 0.0.0.0/0

---

## Step 4 — Create your first admin

```bash
cd ~/sanjaya_auth_v2
source .venv/bin/activate

# First: register via the web UI at http://18.61.252.222:8001
# Then promote yourself to admin:
python3 make_admin.py YOUR_USERNAME
```

---

## Access

| URL | Purpose |
|---|---|
| `http://18.61.252.222:8001` | Login portal |
| `http://18.61.252.222:8001/docs` | Swagger API docs |
| `http://18.61.252.222:8001/health` | Health check |

---

## Service management

```bash
sudo systemctl status sanjaya-auth
sudo systemctl restart sanjaya-auth
sudo journalctl -u sanjaya-auth -f        # live logs
```

---

## RBAC Summary

| Role | Capabilities |
|---|---|
| **user** | Login, view own profile, redirect to app |
| **manager** | + Read-only view of all team members |
| **admin** | + Change roles, activate/deactivate users, view all audit logs |

---

## SMTP / MFA

Already configured in `.env` with your Gmail credentials.
If MFA emails don't arrive, set `DEBUG_OTP_IN_RESPONSE=true` in `.env`
to see the OTP in the API response (dev only, revert in production).

---

## Switch to Postgres (optional)

```bash
# Install postgres
sudo apt-get install -y postgresql postgresql-contrib
sudo -u postgres psql -c "CREATE USER sanjaya WITH PASSWORD 'yourpassword';"
sudo -u postgres psql -c "CREATE DATABASE sanjaya_auth OWNER sanjaya;"

# Update .env
AUTH_DATABASE_URL=postgresql://sanjaya:yourpassword@localhost:5432/sanjaya_auth

sudo systemctl restart sanjaya-auth
```
