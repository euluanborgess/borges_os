import sqlite3

def check():
    conn = sqlite3.connect('borges_os.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, created_at, access_token FROM ad_accounts WHERE status='PENDING' ORDER BY created_at DESC LIMIT 5")
    for row in cursor.fetchall():
        print(f"ID={row[0]} | Created={row[1]} | Token={row[2][:20]}...")
    conn.close()

if __name__ == "__main__":
    check()
