import sqlite3
import requests
import json
import os

def fix_and_subscribe():
    # 1. Read token
    try:
        with open("tmp/meta_token.txt", "r") as f:
            token = f.read().strip()
    except Exception:
        print("Token file not found.")
        return
        
    print(f"Using token: {token[:20]}...")
    
    # 2. Fetch pages
    print("Fetching Pages...")
    pages_res = requests.get(f"https://graph.facebook.com/v19.0/me/accounts?fields=id,name,instagram_business_account,access_token&access_token={token}")
    if pages_res.status_code != 200:
        print("Failed to fetch pages:", pages_res.text)
        return
        
    ig_biz_id = None
    
    for page in pages_res.json().get("data", []):
        if "instagram_business_account" in page:
            page_id = page["id"]
            page_name = page["name"]
            page_token = page["access_token"]
            ig_id = page["instagram_business_account"]["id"]
            
            print(f"Found Page '{page_name}' with IG {ig_id}")
            
            # Save the first IG id we find
            if not ig_biz_id:
                ig_biz_id = ig_id
            
            # SUbscribe!
            sub_res = requests.post(
                f"https://graph.facebook.com/v19.0/{page_id}/subscribed_apps",
                params={
                    "subscribed_fields": "messages,messaging_postbacks,messaging_optins",
                    "access_token": page_token
                }
            )
            print(f"Subscribe response for '{page_name}': {sub_res.status_code} - {sub_res.text}")

    # 3. Inject deeply into SQLite JSON via UPDATE statement
    conn = sqlite3.connect('borges_os.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, integrations FROM tenants")
    for row in cursor.fetchall():
        t_id = row[0]
        # skip ads tenant if there are multiple. Assume we want de634e90-df7e-4006-9f25-945ddb7442d0
        if "de634e90" not in t_id:
            continue
            
        integrations = json.loads(row[1]) if row[1] else {}
        integrations["instagram_connected"] = True
        integrations["instagram_token"] = token
        if ig_biz_id:
            integrations["instagram_business_account_id"] = ig_biz_id
            
        new_json = json.dumps(integrations)
        print(f"Force Updating Tenant {t_id} with new JSON length {len(new_json)}")
        cursor.execute("UPDATE tenants SET integrations = ? WHERE id = ?", (new_json, t_id))
        
    conn.commit()
    conn.close()
    print("Database patched completely!")

if __name__ == "__main__":
    fix_and_subscribe()
