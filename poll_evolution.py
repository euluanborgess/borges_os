import httpx
import time
import os
import sys
from datetime import datetime, timedelta

# Ensure root dir is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import SessionLocal
from models import Tenant

EVOLUTION_API_URL = "https://cosmicstarfish-evolution.cloudfy.live"
EVOLUTION_API_KEY = "bMQLdgHiveJZOejgVQqCMEY0zUSGalNh"
WEBHOOK_INTERNAL_URL = "http://localhost:8000/api/v1/webhooks/evolution"

last_checked_msg_id = None

def poll_messages():
    global last_checked_msg_id
    db = SessionLocal()
    try:
        tenants = db.query(Tenant).filter(Tenant.evolution_instance_id != None).all()
        for tenant in tenants:
            instance = tenant.evolution_instance_id
            try:
                # Use POST findMessages for Evolution V2
                response = httpx.post(
                    f"{EVOLUTION_API_URL}/chat/findMessages/{instance}",
                    headers={"apikey": EVOLUTION_API_KEY, "Content-Type": "application/json"},
                    json={"count": 20},
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    messages = data.get("messages", {}).get("records", [])
                    if messages and isinstance(messages, list):
                        for msg in reversed(messages):
                            key = msg.get("key", {})
                            if key.get("fromMe"):
                                continue
                            
                            msg_id = key.get("id")
                            # Fetch message ids from Message table to check existence
                            from models import Message
                            import json
                            
                            # SQLite specific check for nested JSON or just pull all IDs for this instance once
                            # To be safe and fast for SQLite, we'll check if the ID string exists in metadata_json
                            # or just use a simple query
                            all_msgs = db.query(Message.id).filter(Message.metadata_json.like(f"%{msg_id}%")).first()
                            
                            if not all_msgs:
                                # REMOVED: msg_ts check to allow OLD messages to sync into the system
                                # If it's not in our DB, we want it, regardless of how old it is.

                                print(f"🚀 New message detected via polling: {msg_id}")
                                webhook_res = httpx.post(
                                    WEBHOOK_INTERNAL_URL,
                                    json={
                                        "event": "messages.upsert",
                                        "instance": instance,
                                        "data": {
                                            "messages": [msg],
                                            "instance": instance,
                                            "event": "messages.upsert",
                                            "pushName": msg.get("pushName", "Desconhecido")
                                        }
                                    }
                                )
                                print(f"[DEBUG Polling] Webhook response: {webhook_res.status_code}")
                else:
                    print(f"[DEBUG Polling] API Error {response.status_code}: {response.text}")
            except Exception as e:
                print(f"Error polling instance {instance}: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🕵️ Borges OS Polling Service Started...", flush=True)
    while True:
        print(f"[{datetime.now()}] Polling messages...", flush=True)
        try:
            poll_messages()
        except Exception as e:
            print(f"Polling loop error: {e}", flush=True)
        time.sleep(10) # Poll every 10 seconds
