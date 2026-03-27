import sqlite3
import json

def check_all():
    conn = sqlite3.connect('borges_os.db')
    cursor = conn.cursor()
    
    print("--- TENANTS ---")
    cursor.execute("SELECT id, integrations FROM tenants")
    for row in cursor.fetchall():
        integrations = json.loads(row[1]) if row[1] else {}
        token = integrations.get("instagram_token")
        has_token = bool(token)
        print(f"Tenant {row[0]}: instagram_connected={integrations.get('instagram_connected')}, has_token={has_token}")
        
    print("\n--- AD ACCOUNTS ---")
    cursor.execute("SELECT id, tenant_id, name, status FROM ad_accounts ORDER BY id DESC LIMIT 5")
    for row in cursor.fetchall():
        print(f"AdAccount ID={row[0]}, Tenant={row[1]}, Name={row[2]}, Status={row[3]}")
    
    conn.close()

if __name__ == "__main__":
    check_all()
