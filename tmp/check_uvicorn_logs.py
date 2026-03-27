import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HOST = "187.77.253.67"
USER = "root"
PASSWORD = "Borges35133@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

def run(cmd):
    _, out, err = ssh.exec_command(cmd)
    return (out.read() + err.read()).decode("utf-8", errors="replace")

print("Últimos 150 erros do Uvicorn no journalctl:")
print(run("journalctl -u borges.service -n 150 --no-pager | grep -v 'GET /api/v1/dashboard/metrics' | tail -100"))

ssh.close()
