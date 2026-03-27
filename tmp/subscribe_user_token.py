import requests
from dotenv import load_dotenv
import os
import sqlite3
import json

load_dotenv("c:\\Users\\User\\Documents\\BorgesOS_Atualizado\\.env")
app_id = os.environ.get("META_APP_ID")
app_secret = os.environ.get("META_APP_SECRET")

def force_subscribe():
    with open("tmp/meta_token.txt", "r") as f:
        token = f.read().strip()
        
    url = f"https://graph.facebook.com/debug_token?input_token={token}&access_token={app_id}|{app_secret}"
    res = requests.get(url).json()
    
    ig_id = None
    page_id = None
    
    for scope_obj in res.get("data", {}).get("granular_scopes", []):
        if scope_obj["scope"] == "instagram_manage_messages":
            ig_id = scope_obj.get("target_ids", [None])[0]
        elif scope_obj["scope"] == "pages_show_list":
            page_id = scope_obj.get("target_ids", [None])[0]
            
    print(f"Bypassed Graph API! IG ID: {ig_id}, Page ID: {page_id}")
    
    if not ig_id:
        print("Failed to extract IG ID")
        return
        
    # Subscribe using user token
    if page_id:
        print("Subscribing Page...")
        sub_res = requests.post(f"https://graph.facebook.com/v19.0/{page_id}/subscribed_apps", params={
            "subscribed_fields": "messages,messaging_postbacks",
            "access_token": token
        })
        print("Sub Response:", sub_res.status_code, sub_res.text)
        
    # Inject into SQLite
    conn = sqlite3.connect('borges_os.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, integrations FROM tenants")
    for row in cursor.fetchall():
        t_id = row[0]
        if "de634e90" not in t_id:
            continue
        integrations = json.loads(row[1]) if row[1] else {}
        integrations["instagram_connected"] = True
        integrations["instagram_token"] = token
        integrations["instagram_business_account_id"] = ig_id
        
        new_json = json.dumps(integrations)
        cursor.execute("UPDATE tenants SET integrations = ? WHERE id = ?", (new_json, t_id))
        print(f"Force Injected IG {ig_id} to Tenant {t_id}")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    force_subscribe()
