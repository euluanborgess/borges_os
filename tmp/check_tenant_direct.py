import sys
sys.path.append('c:\\Users\\User\\Documents\\BorgesOS_Atualizado')

from core.database import SessionLocal
from models.tenant import Tenant

def check():
    db = SessionLocal()
    tenant_id = "de634e90-df7e-4006-9f25-945ddb7442d0"
    
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if tenant:
        print(f"TENANT FOUND! ID: {tenant.id}")
    else:
        print(f"TENANT NOT FOUND!")
        all_t = db.query(Tenant).all()
        print([t.id for t in all_t])
    db.close()

if __name__ == "__main__":
    check()
