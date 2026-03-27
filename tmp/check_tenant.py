import sqlite3, json
conn = sqlite3.connect("borges_os.db")
c = conn.cursor()
c.execute("SELECT id, name, integrations FROM tenants")
for r in c.fetchall():
    integ = json.loads(r[2]) if r[2] else {}
    if integ.get("instagram_connected"):
        print(f"Tenant '{r[1]}' is CONNECTED! Token length: {len(integ.get('instagram_token', ''))}")
conn.close()
