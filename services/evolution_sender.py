import httpx
from core.config import settings

async def send_whatsapp_message(instance_name: str, remote_jid: str, text: str, evolution_url: str | None = None, evolution_api_key: str | None = None) -> bool:
    """
    Envia uma mensagem de texto pela Evolution API para o número do Lead.
    :param instance_name: Nome da instância (tenant.evolution_instance_id) ex: 'empresa1'
    :param remote_jid: JID do cliente, ex: '5511999999999@s.whatsapp.net'
    :param text: Texto da mensagem a ser enviada.
    """
    base_url = (evolution_url or settings.EVOLUTION_API_URL).strip().rstrip('/')
    api_key = (evolution_api_key or settings.EVOLUTION_API_KEY).strip()

    url = f"{base_url}/message/sendText/{instance_name}"

    headers = {
        "apikey": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "number": remote_jid, # API da Evolution pode aceitar @s.whatsapp.net ou apenas números
        "text": text,
        "delay": 1200 # Pequeno delay (1.2s) para a bolinha de "digitando" ficar mais humana e não enviar com lag zero
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=15.0)
            
            if response.status_code in [200, 201]:
                print(f"[Evolution] Mensagem enviada para {remote_jid} na instância {instance_name}")
                return True
            else:
                print(f"[Evolution Erro] Falha ao enviar: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        print(f"[Evolution Exception] Erro fatal no envio para {remote_jid}: {e}")
        return False
