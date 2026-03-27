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

print("Conteúdo do arquivo .env da VPS:")
print(run("cat /root/borges_os/.env | grep 'DATABASE_URL'"))

print("\nVerificando o nginx proxy:")
print(run("cat /etc/nginx/sites-enabled/* | grep proxy_pass"))

ssh.close()
