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

# Criar colunas que faltam manualmente
print("Adicionando colunas ausentes no banco PostgreSQL...")
sql = """
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS quick_replies JSON DEFAULT '{}';
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS meta_pixel_id VARCHAR;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS meta_capi_token VARCHAR;
"""

print(run(f"docker exec borges_os-db-1 psql -U borges -d borges_os -c \"{sql}\""))

print("Restaurando versão original do alembic (para não quebrar no futuro)...")
# Obter a versão real
head_file = run("ls /root/borges_os/alembic/versions/ | sort -r | head -1").strip()
if "_" in head_file:
    # Marcar a head como aplicada, pois acabamos de rodar a DDL faltante
    head_rev = head_file.split("_")[0]
    run("docker exec borges_os-db-1 psql -U borges -d borges_os -c \"DELETE FROM alembic_version;\"")
    run(f"docker exec borges_os-db-1 psql -U borges -d borges_os -c \"INSERT INTO alembic_version (version_num) VALUES ('{head_rev}');\"")
    print(f"Alembic version set to: {head_rev}")

# Reiniciar o serviço
print("\nReiniciando container da API...")
print(run("docker restart borges_os-api-1"))

ssh.close()
