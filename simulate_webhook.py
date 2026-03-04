import asyncio
import httpx
from core.database import SessionLocal
from models import Tenant

def run_simulation():
    db = SessionLocal()
    tenant = db.query(Tenant).first()
    
    if not tenant:
        print("🔴 Erro: Nenhuma empresa encontrada no banco de dados!")
        return

    # Garante que a empresa tenha um ID de instância Evolution configurado (mesmo que mockado)
    instance_id = tenant.evolution_instance_id
    if not instance_id:
        instance_id = f"borges_{str(tenant.id)[0:8]}"
        tenant.evolution_instance_id = instance_id
        db.commit()
    
    print(f"✅ Utilizando Instância Corretora: {instance_id}")

    payload = {
        "event": "messages.upsert",
        "instance": instance_id,
        "data": {
            "key": {
                "remoteJid": "5511999991234@s.whatsapp.net", 
                "fromMe": False
            },
            "message": {
                "conversation": "Olá Borges! Vi o sistema de vocês e achei muito top, tenho MUITO interesse. Preciso agendar uma call urgente. Meu nome é Carlos Henrique!"
            }
        }
    }

    try:
        response = httpx.post("http://localhost:8000/api/v1/webhooks/evolution", json=payload)
        
        if response.status_code == 200:
            print("🚀 SUCESSO! O Webhook foi disparado com perfeição!")
            print(f"Retorno do Servidor: {response.text}")
            print("\n👉 Olhe para a aba 'Conversas' no seu painel web agora! O lead Carlos acabou de chegar lá magicamente.")
            print("Pode fechar este script.")
        else:
            print(f"⚠️ Erro ao disparar ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"🔥 Erro Crítico: {e}")

if __name__ == "__main__":
    run_simulation()
