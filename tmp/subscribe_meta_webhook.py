import sqlite3
import requests
import json
import os

def subscribe_webhooks():
    conn = sqlite3.connect('borges_os.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, integrations FROM tenants")
    rows = cursor.fetchall()
    conn.close()
    
    for row in rows:
        tenant_id = row[0]
        integrations = json.loads(row[1]) if row[1] else {}
        user_token = integrations.get("instagram_token")
        
        if not user_token:
            continue
            
        print(f"Tenant {tenant_id} - Fetching Pages...")
        pages_res = requests.get(f"https://graph.facebook.com/v19.0/me/accounts?fields=id,name,instagram_business_account,access_token&access_token={user_token}")
        if pages_res.status_code != 200:
            print("Failed to fetch pages:", pages_res.text)
            continue
            
        for page in pages_res.json().get("data", []):
            if "instagram_business_account" in page:
                page_id = page["id"]
                page_token = page["access_token"]
                ig_id = page["instagram_business_account"]["id"]
                
                print(f"Found Page {page['name']} with IG {ig_id}")
                
                sub_res = requests.post(
                    f"https://graph.facebook.com/v19.0/{page_id}/subscribed_apps",
                    params={
                        "subscribed_fields": "messages,messaging_postbacks,messaging_optins",
                        "access_token": page_token
                    }
                )
                print(f"Subscribe response: {sub_res.status_code} - {sub_res.text}")

if __name__ == "__main__":
    subscribe_webhooks()
