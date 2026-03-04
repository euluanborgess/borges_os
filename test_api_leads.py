import httpx
import asyncio

async def test():
    try:
        async with httpx.AsyncClient() as c:
            login = await c.post("http://localhost:8000/api/v1/auth/login", data={"username": "admin@borges.com", "password": "admin123"})
            token = login.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            
            res = await c.get("http://localhost:8000/api/v1/ws/inbox/leads", headers=headers)
            data = res.json()
            for lead in data.get("data", []):
                has_lma = "last_message_at" in lead
                has_pd = "profile_data" in lead
                has_ua = "updated_at" in lead
                lma_val = lead.get("last_message_at", "MISSING")
                pd_val = lead.get("profile_data", "MISSING")
                ua_val = lead.get("updated_at", "MISSING")
                print(f"LEAD: {lead['name']}")
                print(f"  has_last_message_at={has_lma} val={lma_val}")
                print(f"  has_profile_data={has_pd} val={pd_val}")
                print(f"  has_updated_at={has_ua} val={ua_val}")
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(test())
