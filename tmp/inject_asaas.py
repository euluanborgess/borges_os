import sqlite3
import json

conn = sqlite3.connect('borges_os.db')
cursor = conn.cursor()

# Find the default seeded tenant (usually id: a07b3f6f-af34-4bb1-b9f8-999e71c2c6ec)
cursor.execute("SELECT id, integrations FROM tenants")
row = cursor.fetchone()

if row:
    tenant_id = row[0]
    integrations_str = row[1]
    
    if integrations_str:
        integrations = json.loads(integrations_str)
    else:
        integrations = {}
        
    integrations['asaas_api_key'] = '$aact_YTU5YTE0M2M2N2I4MTliNDgwYjFiYjI2OTRlNTc4NDI6Ojk3MjkyOmU0ZTM0MWRmLTQ4YTgtNGI4OC1iZmQ0LTI3MGEzZGVmYzdkOTo6JGFhY2hfZGM5MDljNWYtYzE4Yy00MjdhLTkxNGUtNDAwNWM3ZDdhNzgx'
    
    cursor.execute("UPDATE tenants SET integrations = ? WHERE id = ?", (json.dumps(integrations), tenant_id))
    conn.commit()
    print("API Key injetada com sucesso no Tenant:", tenant_id)
else:
    print("Nenhum tenant encontrado. Rode reset_db primeiro.")

conn.close()
