from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
session = Session()

antigravity_id = "8e234096-d7cc-456c-a6f9-540632e66064"

try:
    print("Iniciando limpeza...")
    session.execute(text("DELETE FROM messages WHERE tenant_id = :tid"), {"tid": antigravity_id})
    print("Messages limpas")
    
    session.execute(text("DELETE FROM leads WHERE tenant_id = :tid"), {"tid": antigravity_id})
    print("Leads limpos")
    
    session.execute(text("DELETE FROM pipeline_stages WHERE tenant_id = :tid"), {"tid": antigravity_id})
    print("Pipelines limpos")
    
    session.execute(text("DELETE FROM users WHERE tenant_id = :tid"), {"tid": antigravity_id})
    print("Users limpos")
    
    session.execute(text("DELETE FROM tenants WHERE id = :tid"), {"tid": antigravity_id})
    print("Tenant limpo")
    
    session.commit()
    print("\nAntigravity Tenant completamente limpo!")
    
except Exception as e:
    session.rollback()
    print("Erro durante o processo:", e)

# Confirmar
print("\n=== RESULTADO FINAL ===")
tenants = session.execute(text("SELECT id, name FROM tenants")).fetchall()
for t in tenants:
    print(f"Empresa: {t[1]}")
users = session.execute(text("SELECT email, role FROM users")).fetchall()
for u in users:
    print(f"User: {u[0]} | Role: {u[1]}")
