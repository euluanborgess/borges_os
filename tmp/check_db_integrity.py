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

print("Verificando tabelas e tenants no banco...")
print(run("docker exec borges_os-db-1 psql -U borges -d borges_os -c \"SELECT tablename FROM pg_tables WHERE schemaname = 'public';\""))
print(run("docker exec borges_os-db-1 psql -U borges -d borges_os -c \"SELECT id, name FROM tenants LIMIT 5;\""))

ssh.close()
