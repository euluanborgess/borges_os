import sqlite3

def check_registration():
    try:
        conn = sqlite3.connect('borges_os.db')
        cursor = conn.cursor()
        cursor.execute("SELECT email, role, invite_token, is_active FROM users WHERE role = 'company_admin'")
        rows = cursor.fetchall()
        print("=== Admin Users ===")
        for row in rows:
            print(f"Email: {row[0]}, Role: {row[1]}, Invite Token: {row[2]}, Active: {row[3]}")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_registration()
