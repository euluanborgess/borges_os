import sqlite3

def check_leads():
    try:
        conn = sqlite3.connect('borges_os.db')
        cursor = conn.cursor()
        # Find tenant_id for the admin
        cursor.execute("SELECT tenant_id FROM users WHERE email = 'atendimentocapitaojack@gmail.com'")
        tenant_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM leads WHERE tenant_id = ?", (tenant_id,))
        count = cursor.fetchone()[0]
        print(f"Total leads for tenant {tenant_id}: {count}")
        
        if count > 0:
            cursor.execute("SELECT name, status, created_at FROM leads WHERE tenant_id = ? LIMIT 5", (tenant_id,))
            leads = cursor.fetchall()
            print("=== Recent Leads ===")
            for lead in leads:
                print(f"Name: {lead[0]}, Status: {lead[1]}, Created: {lead[2]}")
                
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_leads()
