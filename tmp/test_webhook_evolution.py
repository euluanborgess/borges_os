import httpx
import asyncio

async def test_webhook():
    print("Enviando payload falso de Instagram (Evolution) para a VPS...")
    url = "http://31.97.247.28:8000/api/v1/webhooks/evolution"
    
    # Payload simulando Evolution API para Instagram
    payload = {
        "event": "messages.upsert",
        "instance": "borges_BorgesOS",
        "data": {
            "key": {
                "remoteJid": "ig_1234599999@s.whatsapp.net",
                "fromMe": False,
                "id": "BAE5SIMULATED123"
            },
            "pushName": "Teste Evolution Real",
            "messageTimestamp": 1711562000,
            "message": {
                "conversation": "Mensagem de teste para puxar nome e foto"
            },
            "isInstagram": True
        }
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, timeout=10.0)
            print(f"Status: {resp.status_code}")
            print(f"Resposta: {resp.text}")
        except Exception as e:
            print(f"Erro ao chamar webhook: {e}")

asyncio.run(test_webhook())
