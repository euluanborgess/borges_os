import paramiko

HOST = "31.97.247.28"
USER = "root"
PASSWORD = "Borges35133@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

def run(cmd):
    _, out, err = ssh.exec_command(cmd)
    return (out.read() + err.read()).decode("utf-8", errors="replace")

print("Adicionando colunas faltantes na tabela leads...")
sql = """
ALTER TABLE leads ADD COLUMN IF NOT EXISTS assigned_user_id UUID;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS internal_notes TEXT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS utm_source VARCHAR;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS utm_medium VARCHAR;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS utm_campaign VARCHAR;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS utm_content VARCHAR;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS ad_creative_id VARCHAR;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS ad_source VARCHAR;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS ad_campaign_name VARCHAR;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS ad_creative_url VARCHAR;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS last_message JSON;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS last_message_at TIMESTAMP;
"""

print(run(f"docker exec borges_os-db-1 psql -U borges -d borges_os -c \"{sql}\""))

print("Reiniciando container...")
print(run("docker restart borges_os-api-1"))

ssh.close()
