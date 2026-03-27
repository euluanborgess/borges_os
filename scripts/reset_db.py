import os
import sys

# Ensure root directory is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import engine, SessionLocal
from models.base import Base
from models.user import User
from models.tenant import Tenant
import models

def reset_and_seed():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    
    print("Recreating all tables...")
    Base.metadata.create_all(bind=engine)
    
    print("Seeding super admin...")
    os.environ["DEFAULT_ADMIN_PASSWORD"] = "admin123456"
    
    from seed_admin import seed_admin
    seed_admin()
    
    print("Database reset and seeded successfully!")

if __name__ == "__main__":
    reset_and_seed()
