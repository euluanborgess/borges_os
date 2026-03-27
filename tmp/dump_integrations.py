import sqlite3

def dump():
    conn = sqlite3.connect('borges_os.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, integrations FROM tenants")
    for row in cursor.fetchall():
        print(f"--- Tenant {row[0]} ---")
        print(row[1] if row[1] else "None")
    conn.close()

if __name__ == "__main__":
    dump()
