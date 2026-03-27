import sys
import os
from dotenv import load_dotenv

# Ensure the root directory is in PYTHONPATH so we can import 'core', 'models' etc.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
load_dotenv()

from core.database import SessionLocal
from models.tenant import Tenant
from models.user import User
from core.security import get_password_hash

def seed_admin():
    """Create a default tenant + super admin user if none exists.

    Supports env overrides:
      - DEFAULT_TENANT_NAME
      - DEFAULT_ADMIN_EMAIL
      - DEFAULT_ADMIN_PASSWORD
      - DEFAULT_ADMIN_FULL_NAME

    This is meant for first-run bootstrap (dev/staging). For production, you should
    set a strong password and/or disable auto-seeding.
    """
    db = SessionLocal()

    default_tenant_name = os.getenv("DEFAULT_TENANT_NAME", "Sede Borges OS - Admin")
    admin_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@borges.com")
    admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
    admin_full_name = os.getenv("DEFAULT_ADMIN_FULL_NAME", "Borges Super Admin")

    # Check if a tenant exists
    tenant = db.query(Tenant).first()
    if not tenant:
        print("Nenhum Tenant encontrado. Criando um Tenant Default...")
        tenant = Tenant(name=default_tenant_name)
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        print(f"Tenant criado com ID: {tenant.id}")

    # Check if admin user exists
    admin = db.query(User).filter(User.email == admin_email).first()
    if admin:
        print("Usuário Admin já existe!")
        return

    if not admin_password or len(admin_password) < 8:
        raise ValueError("DEFAULT_ADMIN_PASSWORD precisa ter pelo menos 8 caracteres")

    admin = User(
        tenant_id=tenant.id,
        full_name=admin_full_name,
        email=admin_email,
        hashed_password=get_password_hash(admin_password),
        role="super_admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    print("Usuário Admin criado com sucesso!")
    print(f"Email: {admin_email}")
    # Avoid printing custom passwords to logs; only print the default one.
    if admin_email == "admin@borges.com" and admin_password == "admin123":
        print("Senha: admin123 (DEFAULT - TROCAR)")

if __name__ == "__main__":
    seed_admin()
