import httpx
import asyncio
import time
import sqlite3

async def inject_insta():
    # Pega o id do primeiro tenant do DB local p injetar a msg p ele
    conn = sqlite3.connect('borges_os.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM tenants LIMIT 1')
    tenant_id = cursor.fetchone()[0]
    conn.close()

    payload = {
        "event": "messages.upsert",
        "instance": f"borges_insta_{tenant_id[0:8]}",
        "data": {
            "isInstagram": True,
            "messages": [
                {
                    "key": {"remoteJid": "ig_123456789@s.whatsapp.net", "fromMe": False},
                    "pushName": "Cliente do Insta Teste",
                    "messageTimestamp": int(time.time()),
                    "message": {"conversation": "Oi! Vi seu post no Instagram e quero mais informações!"}
                }
            ]
        }
    }
    url = "http://localhost:8000/api/v1/webhooks/evolution"
    async with httpx.AsyncClient() as client:
        res = await client.post(url, json=payload)
        print("Status", res.status_code)
        print("Body", res.text)

asyncio.run(inject_insta())
