import paramiko

HOST = "187.77.253.67"
USER = "root"
PASSWORD = "Borges35133@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

def run(cmd):
    print(f"#> {cmd}")
    _, out, err = ssh.exec_command(cmd)
    res = (out.read() + err.read()).decode("utf-8", errors="replace")
    print(res)
    return res

py_script = """
import sqlite3
import os

db_path = "/var/www/borges_os/borges_os.db"
if not os.path.exists(db_path):
    print(f"DB não encontrado em {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    columns_to_add = [
        "assigned_user_id VARCHAR",
        "internal_notes TEXT",
        "utm_source VARCHAR",
        "utm_medium VARCHAR",
        "utm_campaign VARCHAR",
        "utm_content VARCHAR",
        "ad_creative_id VARCHAR",
        "ad_source VARCHAR",
        "ad_campaign_name VARCHAR",
        "ad_creative_url VARCHAR",
        "last_message TEXT",
        "last_message_at DATETIME",
        "quick_replies TEXT",
        "meta_pixel_id VARCHAR",
        "meta_capi_token VARCHAR"
    ]
    
    for col in columns_to_add:
        col_name = col.split()[0]
        try:
            cur.execute(f"ALTER TABLE leads ADD COLUMN {col};")
            print(f"Coluna {col_name} adicionada a leads.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower(): pass
            else: print(f"Erro em leads {col_name}: {e}")
            
    # Tenant columns
    tenant_cols = [
        "quick_replies TEXT",
        "meta_pixel_id VARCHAR",
        "meta_capi_token VARCHAR"
    ]
    for col in tenant_cols:
        col_name = col.split()[0]
        try:
            cur.execute(f"ALTER TABLE tenants ADD COLUMN {col};")
            print(f"Coluna {col_name} adicionada a tenants.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower(): pass
            else: print(f"Erro em tenants {col_name}: {e}")

    # Tasks columns
    try:
        cur.execute("ALTER TABLE tasks ADD COLUMN assigned_to VARCHAR;")
        print("Coluna assigned_to adicionada a tasks.")
    except Exception as e:
        if "duplicate column name" not in str(e).lower(): print(e)

    conn.commit()
    conn.close()
    print("Migração SQLite manual finalizada.")
"""

sftp = ssh.open_sftp()
with sftp.file('/root/patch_sqlite.py', 'w') as f:
    f.write(py_script)
sftp.close()

run("python3 /root/patch_sqlite.py")

ssh.close()
