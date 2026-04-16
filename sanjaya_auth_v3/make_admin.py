#!/usr/bin/env python3
"""
Run this once after first deploy to promote a user to admin.
Usage: python3 make_admin.py <username>
"""
import sys
import os

# Load env
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
from app.database import SessionLocal, engine
from app.models import Base, User

Base.metadata.create_all(bind=engine)

if len(sys.argv) < 2:
    print("Usage: python3 make_admin.py <username>")
    sys.exit(1)

username = sys.argv[1]
db = SessionLocal()
user = db.query(User).filter(User.username == username).first()
if not user:
    print(f"❌  User '{username}' not found. Register first via the web UI.")
    sys.exit(1)

user.role = "admin"
db.commit()
print(f"✅  '{username}' is now an admin.")
db.close()
