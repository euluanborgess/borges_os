import sys
import os

# Ensure the root directory is in PYTHONPATH so we can import 'core', 'models' etc.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import SessionLocal
from models.tenant import Tenant
from models.user import User
from core.security import get_password_hash

def seed_admin():
    db = SessionLocal()
    
    # Check if a tenant exists
    tenant = db.query(Tenant).first()
    if not tenant:
        print("Nenhum Tenant encontrado. Criando um Tenant Default...")
        tenant = Tenant(name="Sede Borges OS - Admin")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        print(f"Tenant criado com ID: {tenant.id}")
        
    # Check if admin user exists
    admin = db.query(User).filter(User.email == "admin@borges.com").first()
    if admin:
        print("Usuário Admin já existe!")
        return

    admin = User(
        tenant_id=tenant.id,
        full_name="Borges Super Admin",
        email="admin@borges.com",
        hashed_password=get_password_hash("admin123"),
        role="super_admin",
        is_active=True
    )
    db.add(admin)
    db.commit()
    print("Usuário Admin criado com sucesso!")
    print("Email: admin@borges.com | Senha: admin123")

if __name__ == "__main__":
    seed_admin()
