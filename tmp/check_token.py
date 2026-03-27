import sqlite3
import json

conn = sqlite3.connect('borges_os.db')
cursor = conn.cursor()
cursor.execute("SELECT id, integrations FROM tenants")
for row in cursor.fetchall():
    integrations = json.loads(row[1]) if row[1] else {}
    print(f"Tenant {row[0]}: Connected: {integrations.get('instagram_connected')}, Token Length: {len(integrations.get('instagram_token', '')) if integrations.get('instagram_token') else 'None'}")
conn.close()
