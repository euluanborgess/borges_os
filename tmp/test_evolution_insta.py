import httpx
import asyncio

EVOLUTION_API_URL = "https://cosmicstarfish-evolution.cloudfy.live"
EVOLUTION_API_KEY = "bMQLdgHiveJZOejgVQqCMEY0zUSGalNh"

async def test_insta():
    async with httpx.AsyncClient() as client:
        # Pega integrações da API v2 ou docs
        res = await client.get(
            f"{EVOLUTION_API_URL}/instance/fetchInstances", # just generic request
            headers={"apikey": EVOLUTION_API_KEY}
        )
        print("Instances:", res.status_code)
        
        # Test creation with different names maybe META, INSTAGRAM_BUSINESS?
        for ig_name in ["INSTAGRAM", "INSTAGRAM-BUSINESS", "META"]:
            res = await client.post(
                f"{EVOLUTION_API_URL}/instance/create",
                headers={"apikey": EVOLUTION_API_KEY},
                json={"instanceName": f"test_insta_{ig_name}", "integration": ig_name}
            )
            print(ig_name, res.status_code, res.text)
            
asyncio.run(test_insta())
