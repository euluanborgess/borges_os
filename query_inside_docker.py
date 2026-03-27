
import os
import sys
sys.path.append("/app")
from core.database import SessionLocal
from models.lead import Lead

db = SessionLocal()
leads = db.query(Lead).order_by(Lead.created_at.desc()).limit(10).all()
print("LEADS NA API (via SQLAlchemy):")
for L in leads:
    print(f"ID={L.id} Name='{L.name}' Phone='{L.phone}' Channel='{L.channel}'")
