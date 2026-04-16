import sys
import os
import uuid
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
from app.database import SessionLocal, engine
from app.models import Base, User, AuditLog
from app.security import hash_password, encrypt_pii, hash_email

def seed():
    db = SessionLocal()
    
    # 1. Dummy Users
    dummy_users = [
        {"user": "alex.chen", "role": "manager", "ip": "192.168.1.144"},
        {"user": "sarah.admin", "role": "admin", "ip": "10.0.4.55"},
        {"user": "d.roberts", "role": "user", "ip": "172.16.2.11"},
        {"user": "j.smith", "role": "user", "ip": "192.168.1.180"},
    ]
    
    for d in dummy_users:
        u = d["user"]
        # Check if exists
        e = db.query(User).filter(User.username == u).first()
        if not e:
            nu = User(
                username=u,
                email_encrypted=encrypt_pii(f"{u}@sanjaya-logistics.com"),
                email_hash=hash_email(f"{u}@sanjaya-logistics.com"),
                password_hash=hash_password("dummyPass123"),
                role=d["role"],
                mfa_enabled=False,
                is_active=True
            )
            db.add(nu)
    
    db.commit()
    
    # 2. Dummy Logs 
    actions = [
        ("login", "success", "Authenticated successfully"),
        ("mfa_verify", "success", "MFA validated (token matched)"),
        ("login", "failure", "Invalid credentials supplied"),
        ("admin_change_role", "success", "Role promoted by admin"),
        ("token_refresh", "success", "Session extended automatically"),
        ("login", "failure", "Rate limited / suspicious activity"),
        ("admin_create_user", "success", "Provisioned via RBAC control panel")
    ]
    
    # Seed 30 realistic entries looking backwards
    base_time = datetime.utcnow() - timedelta(hours=3)
    
    for i in range(30):
        act, stat, det = random.choice(actions)
        user_choice = random.choice(dummy_users + [{"user": "admin", "role": "admin", "ip": "10.22.40.1"}, {"user": "unknown", "role": "user", "ip": "45.201.12.9"}])
        
        base_time += timedelta(minutes=random.randint(1, 8))
        if base_time > datetime.utcnow():
            break
            
        port = "8000" if random.random() > 0.4 else "8001"
            
        log = AuditLog(
            id=str(uuid.uuid4()),
            timestamp=base_time,
            username=user_choice["user"],
            action=act,
            status=stat,
            detail=det,
            ip_address=f"{user_choice['ip']} (Port: {port})"
        )
        db.add(log)
        
    db.commit()
    db.close()
    print("Dummy telemetry & simulated users securely injected!")

if __name__ == "__main__":
    seed()
