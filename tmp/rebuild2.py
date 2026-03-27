import paramiko
import time
import sys
import io

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HOST = "31.97.247.28"
USER = "root"
PASSWORD = "Borges35133@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

def run(cmd):
    _, out, err = ssh.exec_command(cmd)
    o = out.read().decode("utf-8", errors="replace")
    e = err.read().decode("utf-8", errors="replace")
    return o + e

# Parar e remover container antigo
print(run("docker stop borges_os-api-1 2>&1 || true"))
print(run("docker rm borges_os-api-1 2>&1 || true"))

# Rebuild rapido sem cache
print("Rebuilding...")
chan = ssh.get_transport().open_session()
chan.exec_command("cd /root/borges_os && docker build -t borges_os-api . 2>&1")
start = time.time()
output = ""
while time.time() - start < 180:
    if chan.recv_ready():
        chunk = chan.recv(4096).decode("utf-8", errors="replace")
        output += chunk
    if chan.exit_status_ready():
        break
    time.sleep(1)
status = chan.recv_exit_status()
print(f"Build status: {status}")
if status != 0:
    print("BUILD FAILED:", output[-1000:])
    ssh.close()
    exit(1)
print("Build OK!")

# Iniciar container
start_cmd = (
    "docker run -d "
    "--name borges_os-api-1 "
    "--network borges_os_default "
    "--restart unless-stopped "
    "-p 8000:8000 "
    "--env-file /root/borges_os/.env "
    "-e DATABASE_URL=postgresql://borges:borgespassword@db:5432/borges_os "
    "-e REDIS_URL=redis://redis:6379/0 "
    "-e EVOLUTION_API_URL=http://evolution_api:8080 "
    "-e EVOLUTION_API_KEY=global-api-key-evolution "
    "-v /root/borges_os/public:/app/public "
    "-v /root/borges_os/media_storage:/app/media_storage "
    "borges_os-api"
)
print(run(start_cmd))

time.sleep(15)
print(run("docker ps | grep borges_os-api"))
print(run("docker logs borges_os-api-1 --tail 20 2>&1"))
print(run("curl -s http://localhost:8000/health 2>&1"))

ssh.close()
