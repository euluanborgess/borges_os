import httpx
import asyncio

async def trigger_connect():
    url = "http://localhost:8000/api/v1/super/whatsapp/connect"
    tenant_id = "de634e90-df7e-4006-9f25-945ddb7442d0"
    
    print(f"Calling {url} for tenant {tenant_id}...")
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(
                url,
                json={"tenant_id": tenant_id},
                timeout=30.0
            )
            print(f"Status: {res.status_code}")
            print(f"Body: {res.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(trigger_connect())
