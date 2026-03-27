import paramiko

HOST = "187.77.253.67"
USER = "root"
PASSWORD = "Borges35133@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

def run(cmd):
    _, out, err = ssh.exec_command(cmd)
    return (out.read() + err.read()).decode("utf-8", errors="replace")

print("Localizando o app borges_os na VPS principal:")
print(run("ls -la /var/www/borges_os"))

print("\nLogs recentes do serviço systemd (borges.service):")
print(run("journalctl -u borges.service -n 50 --no-pager"))

ssh.close()
