import httpx
import asyncio

async def test_evolution():
    url = "https://cosmicstarfish-evolution.cloudfy.live"
    apikey = "bMQLdgHiveJZOejgVQqCMEY0zUSGalNh"
    
    print(f"Testing connection to {url}/instance/fetchInstances...")
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(
                f"{url}/instance/fetchInstances",
                headers={"apikey": apikey},
                timeout=10.0
            )
            print(f"Status: {res.status_code}")
            print(f"Body: {res.text[:200]}")
        except Exception as e:
            print(f"Error connecting to Evolution: {e}")

if __name__ == "__main__":
    asyncio.run(test_evolution())
