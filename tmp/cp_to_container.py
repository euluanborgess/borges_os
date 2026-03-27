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

# O problema: os arquivos ficam em /root/borges_os mas o container os lê de dentro do seu filesystem
# Durante o build, os arquivos são copiados. Mas o container usa a imagem antiga buildada.
# Precisamos PARAR o container, copiar usando docker cp, e reiniciar.

# Parar o container primeiro
print("Parando container para copiar arquivos...")
print(run("docker stop borges_os-api-1 2>&1"))
time.sleep(2)

# Verificar que o container parou (mas ainda existe)
print(run("docker ps -a | grep borges_os-api-1"))

# Copiar arquivos de rota críticos para dentro do container parado
files_to_copy = [
    ("/root/borges_os/api/routes/instagram.py", "/app/api/routes/instagram.py"),
    ("/root/borges_os/api/routes/billing.py", "/app/api/routes/billing.py"),
    ("/root/borges_os/api/routes/traffic.py", "/app/api/routes/traffic.py"),
    ("/root/borges_os/api/routes/webhooks.py", "/app/api/routes/webhooks.py"),
    ("/root/borges_os/main.py", "/app/main.py"),
]

for src, dst in files_to_copy:
    result = run(f"docker cp {src} borges_os-api-1:{dst} 2>&1")
    print(f"CP {src.split('/')[-1]}: {result.strip() or 'OK'}")

# Reiniciar o container
print("\nReiniciando container...")
print(run("docker start borges_os-api-1 2>&1"))
time.sleep(20)

print("\nStatus:")
print(run("docker ps | grep borges_os-api"))
print("\nLogs:")
print(run("docker logs borges_os-api-1 --tail 30 2>&1"))
print("\nHealth:")
print(run("curl -s --max-time 5 http://localhost:8000/health"))

ssh.close()
