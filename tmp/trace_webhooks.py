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

print("Últimos acessos de webhooks da Evolution e Meta:")
print(run("journalctl -u borges.service -n 500 --no-pager | grep '/webhooks' | tail -15"))

print("\nVerificando erros do script de webhooks.py impressos no log:")
print(run("journalctl -u borges.service -n 500 --no-pager | grep -i 'EVOLUTION WEBHOOK\|META WEBHOOK' | tail -15"))

ssh.close()
