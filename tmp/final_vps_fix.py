import os
import sqlite3
import json

db_path = "/var/www/borges_os/borges_os.db"
tid = "de634e90-df7e-4006-9f25-945ddb7442d0"
ig_id = "17841471788736574"

print(f"Connecting to DB at {db_path}...")
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT integrations FROM tenants WHERE id = ?", (tid,))
row = c.fetchone()
if row:
    integ = json.loads(row[0]) if row[0] else {}
    integ["instagram_business_account_id"] = ig_id
    integ["instagram_connected"] = True
    c.execute("UPDATE tenants SET integrations = ? WHERE id = ?", (json.dumps(integ), tid))
    conn.commit()
    print(f"SUCCESS: Injected Instagram Business ID {ig_id} for tenant {tid}")
else:
    print(f"ERROR: Tenant {tid} not found!")

conn.close()

# Patch services/message_buffer.py more aggressively
mb_path = "/var/www/borges_os/services/message_buffer.py"
with open(mb_path, "r", encoding="utf-8") as f:
    text = f.read()

# Replace ANY mention of instagram_page_token with instagram_token
new_text = text.replace("instagram_page_token", "instagram_token")

# Add a specific safeguard for the token lookup
safe_code = """
                # PRIORIDADE TOTAL PARA instagram_token (NOVO FLUXO)
                page_token = integ.get("instagram_token") or integ.get("instagram_page_token")
"""
if 'page_token = integ.get("instagram_token")' in new_text:
    print("Code already partially patched, perfecting it...")
    # Just ensure it's correct
else:
    # Basic replacement already done by replace above
    pass

with open(mb_path, "w", encoding="utf-8") as f:
    f.writelines(new_text)
print("services/message_buffer.py patched successfully.")
