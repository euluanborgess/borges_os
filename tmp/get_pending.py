import sqlite3
conn = sqlite3.connect('borges_os.db')
c = conn.cursor()
c.execute("SELECT id FROM ad_accounts WHERE status = 'PENDING' ORDER BY rowid DESC LIMIT 1")
row = c.fetchone()
if row:
    print(f"PENDING_ID={row[0]}")
else:
    print("No pending account found.")
conn.close()
