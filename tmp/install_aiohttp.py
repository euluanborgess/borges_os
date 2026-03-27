import paramiko
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HOST = "31.97.247.28"
USER = "root"
PASSWORD = "Borges35133@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

def run(cmd, timeout=60):
    _, out, err = ssh.exec_command(cmd, timeout=timeout)
    return (out.read() + err.read()).decode("utf-8", errors="replace")

# Verificar quais pacotes estão faltando
print("Verificando requirements.txt da VPS...")
print(run("cat /root/borges_os/requirements.txt"))

# Instalar aiohttp dentro do container
print("\nInstalando aiohttp dentro do container...")
print(run("docker exec borges_os-api-1 pip install aiohttp --quiet 2>&1", timeout=60))

# Verificar se o traffic.py realmente precisa de aiohttp ou se pode ser simplificado
print("\nVerificando traffic.py...")
print(run("head -20 /root/borges_os/api/routes/traffic.py"))

ssh.close()
