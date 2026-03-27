import sqlite3

def get_tenant_id():
    conn = sqlite3.connect('borges_os.db')
    cursor = conn.cursor()
    cursor.execute("SELECT tenant_id FROM users WHERE email='atendimentocapitaojack@gmail.com'")
    res = cursor.fetchone()
    if res:
        print(res[0])
    conn.close()

if __name__ == "__main__":
    get_tenant_id()
