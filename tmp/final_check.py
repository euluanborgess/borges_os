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

def run(cmd):
    _, out, err = ssh.exec_command(cmd, timeout=15)
    return (out.read() + err.read()).decode("utf-8", errors="replace")

# Aguardar uvicorn subir
time.sleep(15)

print("=== Container status ===")
print(run("docker ps | grep borges"))

print("\n=== Full logs ===")
print(run("docker logs borges_os-api-1 --tail 40 2>&1"))

print("\n=== Health check ===")
print(run("curl -s --max-time 5 http://localhost:8000/health"))

print("\n=== Test homepage ===")
print(run("curl -s --max-time 5 -o /dev/null -w '%{http_code}' http://localhost:8000/"))

ssh.close()
