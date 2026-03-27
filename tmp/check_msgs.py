import sqlite3

def check_msgs():
    conn = sqlite3.connect('borges_os.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, tenant_id, source, lead_id, role, content, created_at FROM messages ORDER BY created_at DESC LIMIT 5")
    print("--- 5 LATEST MESSAGES ---")
    for row in cursor.fetchall():
        print(row)
    conn.close()

if __name__ == "__main__":
    check_msgs()
