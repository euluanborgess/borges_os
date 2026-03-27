# Identity Manager - Auto Sync
# Runs every 30 min to ensure environment stability
import uvicorn
import requests
import time
import os

BASE_URL = "http://localhost:8000"

def check_health():
    try:
        r = requests.get(f"{BASE_URL}/static/index.html", timeout=5)
        if r.status_code == 200:
            print("[Guardian] Health OK")
            return True
    except:
        pass
    print("[Guardian] System down. Restarting...")
    return False

if __name__ == "__main__":
    while True:
        if not check_health():
            os.system("fuser -k 8000/tcp || true")
            # Restart logic is handled by the main execution session in OpenClaw
        time.sleep(600)
