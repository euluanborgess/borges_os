import sqlite3
import json

conn = sqlite3.connect('borges_os.db')
cursor = conn.cursor()

new_integrations = json.dumps({"instagram_connected": False})
cursor.execute("UPDATE tenants SET integrations = ?", (new_integrations,))
conn.commit()
conn.close()

print("Integrations limpas e resetadas com sucesso!")
