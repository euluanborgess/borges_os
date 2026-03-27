import httpx
import asyncio

URL = "https://cosmicstarfish-evolution.cloudfy.live"
APIKEY = "bMQLdgHiveJZOejgVQqCMEY0zUSGalNh"
CF_URL = "https://bradford-wires-dist-hormone.trycloudflare.com"
WEBHOOK_URL = f"{CF_URL}/api/v1/webhooks/evolution"

async def setup_webhooks():
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{URL}/instance/fetchInstances", headers={"apikey": APIKEY})
        instances = res.json()
        
        for inst in instances:
            name = inst.get("name")
            if name and "borges_" in name:
                webhook_data = {
                    "webhook": {
                        "enabled": True,
                        "url": WEBHOOK_URL,
                        "byEvents": False,
                        "base64": False,
                        "events": [
                            "MESSAGES_UPSERT",
                            "CONNECTION_UPDATE",
                            "PRESENCE_UPDATE",
                            "CONTACTS_UPSERT"
                        ]
                    }
                }
                wh_res = await client.post(f"{URL}/webhook/set/{name}", headers={"apikey": APIKEY, "Content-Type": "application/json"}, json=webhook_data)
                print(f"Result for {name}: {wh_res.status_code}")

if __name__ == "__main__":
    asyncio.run(setup_webhooks())
