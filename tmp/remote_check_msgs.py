import sqlite3

db_path = "/var/www/borges_os/borges_os.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT content, sender_type, created_at FROM messages ORDER BY created_at DESC LIMIT 10")
rows = c.fetchall()

print("--- ULTIMAS MENSAGENS NO BANCO ---")
for row in rows:
    print(f"[{row[2]}] {row[1].upper()}: {row[0]}")

conn.close()
