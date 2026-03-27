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

print("Leads recentes (todos os canais) para entender como estao sendo salvos:")
sql = "SELECT id, name, phone, channel, profile_data FROM leads ORDER BY created_at DESC LIMIT 10;"
print(run(f"docker exec borges_os-db-1 psql -U borges -d borges_os -c \"{sql}\""))

print("\nLogs recentes do container:")
print(run("docker logs borges_os-api-1 | grep -i 'webhook\|lead' | tail -20"))

ssh.close()
