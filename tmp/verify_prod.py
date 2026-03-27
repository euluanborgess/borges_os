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

def run(cmd, timeout=15):
    _, out, err = ssh.exec_command(cmd, timeout=timeout)
    o = out.read().decode("utf-8", errors="replace")
    e = err.read().decode("utf-8", errors="replace")
    return o + e

# Checar se a API subiu
print("=== Status do container ===")
print(run("docker ps | grep borges_os-api"))

# Health check direto
print("\n=== Health Check ===")
time.sleep(5)  # Dar tempo para uvicorn subir
print(run("curl -s http://localhost:8000/health"))

# Verificar que o webhook está respondendo
print("\n=== Logs uvicorn ===")
print(run("docker logs borges_os-api-1 --tail 30 2>&1"))

# Checar se a Evolution API está configurada para mandar webhooks
print("\n=== Nginx config/ports ===")
print(run("ss -tlnp | grep 8000"))

ssh.close()
