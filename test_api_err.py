import httpx
import asyncio

LOGIN_URL = "http://localhost:8000/api/v1/auth/token"
EVENTS_URL = "http://localhost:8000/api/v1/calendar/events"

async def run_test():
    async with httpx.AsyncClient() as client:
        # Login
        resp = await client.post(LOGIN_URL, data={"username": "admin@borges.com", "password": "123"})
        if resp.status_code != 200:
            print("Login failed:", resp.text)
            return
        token = resp.json().get("access_token")
        
        # Get events
        headers = {"Authorization": f"Bearer {token}"}
        r = await client.get(EVENTS_URL, headers=headers)
        print("STATUS:", r.status_code)
        print("RESPONSE:", r.text)

if __name__ == "__main__":
    asyncio.run(run_test())
