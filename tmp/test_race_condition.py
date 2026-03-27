import httpx
import asyncio
import time

async def simulate_race_condition():
    print("Enviando pacote simulado da API META (que vai falhar ao baixar foto e salvar como 'Lead IG 9999')")
    meta_url = "http://31.97.247.28:8000/api/v1/webhooks/meta"
    evolution_url = "http://31.97.247.28:8000/api/v1/webhooks/evolution"
    
    meta_payload = {
        "object": "instagram",
        "entry": [
            {
                "id": "123456789",
                "time": 1711562000,
                "messaging": [
                    {
                        "sender": {"id": "9999"},
                        "recipient": {"id": "123456789"},
                        "timestamp": 1711562000,
                        "message": {
                            "mid": "mid.12345",
                            "text": "Teste de Mensagem"
                        }
                    }
                ]
            }
        ]
    }
    
    evolution_payload = {
        "event": "messages.upsert",
        "instance": "borges_BorgesOS",
        "data": {
            "key": {
                "remoteJid": "ig_9999@s.whatsapp.net",
                "fromMe": False,
                "id": "BAE5SIMULATED123"
            },
            "pushName": "Nome Real do Instagram",
            "messageTimestamp": 1711562002,
            "message": {
                "conversation": "Teste de Mensagem"
            },
            "isInstagram": True
        }
    }
    
    async with httpx.AsyncClient() as client:
        print("-> Disparando Meta Webhook...")
        try:
            r1 = await client.post(meta_url, json=meta_payload, timeout=10.0)
            print("Meta OK:", r1.status_code)
        except Exception as e: print(e)
        
        time.sleep(2)
        
        print("-> Disparando Evolution Webhook...")
        try:
            r2 = await client.post(evolution_url, json=evolution_payload, timeout=10.0)
            print("Evolution OK:", r2.status_code)
        except Exception as e: print(e)

asyncio.run(simulate_race_condition())
