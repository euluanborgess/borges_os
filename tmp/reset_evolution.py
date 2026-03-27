import httpx
import asyncio

async def reset_instance():
    url = "https://cosmicstarfish-evolution.cloudfy.live"
    apikey = "bMQLdgHiveJZOejgVQqCMEY0zUSGalNh"
    instance_name = "borges_de634e90"
    
    async with httpx.AsyncClient() as client:
        print(f"Logging out {instance_name}...")
        res1 = await client.delete(
            f"{url}/instance/logout/{instance_name}",
            headers={"apikey": apikey},
            timeout=10.0
        )
        print(f"Logout status: {res1.status_code}")
        
        print(f"Deleting {instance_name}...")
        res2 = await client.delete(
            f"{url}/instance/delete/{instance_name}",
            headers={"apikey": apikey},
            timeout=10.0
        )
        print(f"Delete status: {res2.status_code}")

if __name__ == "__main__":
    asyncio.run(reset_instance())
