import os
import json
import sqlite3

def patch_file(path, old, new):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if old in content:
        new_content = content.replace(old, new)
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Patched {path}")
    else:
        print(f"Pattern not found in {path}")

# 1. Fix message_buffer.py
mb_path = "/var/www/borges_os/services/message_buffer.py"
patch_file(mb_path, "integ.get('instagram_page_token')", "integ.get('instagram_token')")
patch_file(mb_path, "page_token = integ.get('instagram_page_token')", "page_token = integ.get('instagram_token')")

# 2. Add Debug Logs to webhooks.py
wh_path = "/var/www/borges_os/api/routes/webhooks.py"
with open(wh_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    new_lines.append(line)
    if "recipient_id = event.get" in line:
        new_lines.append("            print(f'[WEBHOOK IG] Recipient: {recipient_id}, Sender: {sender_id}')\n")
    if "tenant = t" in line:
        new_lines.append("                    print(f'[WEBHOOK IG] Tenant encontrado: {t.id}')\n")
    if "handle_incoming_message(" in line:
        new_lines.append("                print(f'[WEBHOOK IG] Chamando handle_incoming_message para {lead.id}')\n")

with open(wh_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)
print(f"Updated {wh_path} with logs")

# 3. Check current Tenant Integrations for David
db_path = "/var/www/borges_os/borges_os.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT integrations FROM tenants WHERE id = 'de634e90-df7e-4006-9f25-945ddb7442d0'")
row = c.fetchone()
if row:
    integ = json.loads(row[0]) if row[0] else {}
    print("--- TENANT INTEGRATIONS ---")
    print(f"Token present: {'Yes' if integ.get('instagram_token') else 'No'}")
    print(f"Business ID: {integ.get('instagram_business_account_id')}")
conn.close()
