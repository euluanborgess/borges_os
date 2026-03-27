import sqlite3
import pandas as pd

def check_tenants():
    conn = sqlite3.connect('borges.db')
    query_tenants = "SELECT id, name FROM tenants"
    df_tenants = pd.read_sql_query(query_tenants, conn)
    print("=== Tenants ===")
    print(df_tenants)
    
    query_users = "SELECT id, email, role, invite_token, tenant_id FROM users WHERE role = 'company_admin'"
    df_users = pd.read_sql_query(query_users, conn)
    print("\n=== Company Admins ===")
    print(df_users)
    conn.close()

if __name__ == "__main__":
    check_tenants()
