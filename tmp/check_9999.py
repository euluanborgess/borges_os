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

print("Consultando o banco de dados para a simulação de race condition...")
sql = "SELECT id, name, phone, profile_data FROM leads WHERE phone = 'ig_9999@s.whatsapp.net';"
print(run(f"docker exec borges_os-db-1 psql -U borges -d borges_os -c \"{sql}\""))

print("\nLogs recentes:")
print(run("docker logs borges_os-api-1 --tail 15 2>&1"))

ssh.close()
