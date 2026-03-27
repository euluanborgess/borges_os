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

print("Testando Nginx config:")
print(run("nginx -t"))

print("Lendo o conteúdo do nginx conf atual para ver onde errei:")
print(run("cat /etc/nginx/sites-available/borges"))

ssh.close()
