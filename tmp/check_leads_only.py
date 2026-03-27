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

print("TODOS OS LEADS RECENTES NO BANCO:")
sql = "SELECT id, name, phone, channel FROM leads ORDER BY created_at DESC LIMIT 10;"
print(run(f"docker exec borges_os-db-1 psql -U borges -d borges_os -c \"{sql}\""))

print("\nVerificando mensagens recentes para cruzar lead_id:")
sql2 = "SELECT id, lead_id, sender_type, content, created_at FROM messages ORDER BY created_at DESC LIMIT 5;"
print(run(f"docker exec borges_os-db-1 psql -U borges -d borges_os -c \"{sql2}\""))

ssh.close()
