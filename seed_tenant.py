from core.database import SessionLocal
from models import Tenant

def seed_tenant():
    db = SessionLocal()
    try:
        t = db.query(Tenant).filter_by(evolution_instance_id='antigravity').first()
        if not t:
            t = Tenant(name='Antigravity', evolution_instance_id='antigravity')
            db.add(t)
            db.commit()
            print(f"✅ Sucesso! Tenant 'Antigravity' cadastrado com o ID: {t.id}")
        else:
            print(f"ℹ️ Tenant 'Antigravity' já existia com o ID: {t.id}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_tenant()
