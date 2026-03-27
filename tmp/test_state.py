import httpx
import asyncio

async def test_state():
    url = "https://cosmicstarfish-evolution.cloudfy.live"
    apikey = "bMQLdgHiveJZOejgVQqCMEY0zUSGalNh"
    
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{url}/instance/fetchInstances",
            headers={"apikey": apikey},
            timeout=10.0
        )
        print(res.json())

if __name__ == "__main__":
    asyncio.run(test_state())
