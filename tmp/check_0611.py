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

print("Logs da API para o Lead 0611...")
print(run("docker logs borges_os-api-1 2>&1 | grep -C 5 '1260748858050611'"))

print("\nVerificando o banco de dados:")
sql = "SELECT id, name, phone, channel, profile_data FROM leads WHERE phone LIKE '%1260748858050611%';"
print(run(f"docker exec borges_os-db-1 psql -U borges -d borges_os -c \"{sql}\""))

ssh.close()
