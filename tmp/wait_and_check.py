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

def run(cmd, timeout=20):
    _, out, err = ssh.exec_command(cmd, timeout=timeout)
    return (out.read() + err.read()).decode("utf-8", errors="replace")

# Aguardar 30s para o uvicorn iniciar completamente
time.sleep(30)

print("Status do container:")
print(run("docker ps | grep borges_os-api"))

print("\nLogs completos (ultimas 40 linhas):")
print(run("docker logs borges_os-api-1 --tail 50 2>&1", timeout=20))

print("\nHealth check:")
print(run("curl -s --max-time 8 http://localhost:8000/health"))

print("\nTeste da homepage:")
code = run("curl -s -o /dev/null -w '%{http_code}' --max-time 8 http://localhost:8000/")
print(f"HTTP Status: {code}")

ssh.close()
