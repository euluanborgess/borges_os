import httpx
import asyncio

async def test():
    payload = {
        "event": "messages.upsert",
        "instance": "borges_os",
        "data": {
            "messages": [
                {
                    "key": {"remoteJid": "5511999999999@s.whatsapp.net", "fromMe": False},
                    "pushName": "Teste Cloudflare",
                    "messageTimestamp": 1711000000,
                    "message": {"conversation": "Mensagem Teste via Cloudflare"}
                }
            ]
        }
    }
    url = "https://bradford-wires-dist-hormone.trycloudflare.com/api/v1/webhooks/evolution"
    async with httpx.AsyncClient() as client:
        res = await client.post(url, json=payload)
        print("Status", res.status_code)
        print("Body", res.text)

asyncio.run(test())
