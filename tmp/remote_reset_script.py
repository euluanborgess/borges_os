import sqlite3
import json
import os

db_path = "/var/www/borges_os/borges_os.db"
if not os.path.exists(db_path):
    print(f"Error: DB not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
c = conn.cursor()

email = "atendimentocapitaojack@gmail.com"
c.execute("SELECT tenant_id FROM users WHERE email = ?", (email,))
res = c.fetchone()

if res:
    tid = res[0]
    c.execute("SELECT integrations FROM tenants WHERE id = ?", (tid,))
    row = c.fetchone()
    if row:
        integ_str = row[0]
        integ = json.loads(integ_str) if integ_str else {}
        
        # Clear Instagram
        integ['instagram_token'] = None
        integ['instagram_business_account_id'] = None
        integ['instagram_connected'] = False
        
        c.execute("UPDATE tenants SET integrations = ? WHERE id = ?", (json.dumps(integ), tid))
        conn.commit()
        print(f"Successfully disconnected Instagram for user {email} (Tenant: {tid})")
    else:
        print(f"No integration record for tenant {tid}")
else:
    print(f"User {email} not found")

conn.close()
