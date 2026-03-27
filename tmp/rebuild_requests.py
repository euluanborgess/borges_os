import paramiko
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HOST = "31.97.247.28"
USER = "root"
PASSWORD = "Borges35133@"
LOCAL_BASE = r"c:\Users\User\Documents\BorgesOS_Atualizado"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

def run(cmd, timeout=20):
    _, out, err = ssh.exec_command(cmd, timeout=timeout)
    return (out.read() + err.read()).decode("utf-8", errors="replace")

# Parar container atual
print("Parando container...")
print(run("docker stop borges_os-api-1 && docker rm borges_os-api-1"))

# Enviar requirements.txt atualizado 
sftp = ssh.open_sftp()
sftp.put(LOCAL_BASE + r"\requirements.txt", "/root/borges_os/requirements.txt")
sftp.close()
print("requirements.txt enviado!")

# Rebuild
print("\nRebuildando imagem (sem cache)...")
chan = ssh.get_transport().open_session()
chan.exec_command("cd /root/borges_os && docker build --no-cache -t borges_os-api . 2>&1")

start = time.time()
while time.time() - start < 300:
    if chan.recv_ready():
        data = chan.recv(8192).decode("utf-8", errors="replace")
        for line in data.splitlines():
            l = line.strip()
            if l and any(x in l.lower() for x in ["step", "done", "error", "install", "success", "pip", "failed"]):
                print(f"  {l}")
    if chan.exit_status_ready():
        break
    time.sleep(2)

status = chan.recv_exit_status()
print(f"\nBuild status: {status}")

if status != 0:
    print("BUILD FALHOU")
    ssh.close()
    exit(1)

# Iniciar container
print("\nIniciando container...")
print(run("""docker run -d \
    --name borges_os-api-1 \
    --network borges_os_default \
    --restart unless-stopped \
    -p 8000:8000 \
    --env-file /root/borges_os/.env \
    -e DATABASE_URL=postgresql://borges:borgespassword@db:5432/borges_os \
    -e REDIS_URL=redis://redis:6379/0 \
    -e EVOLUTION_API_URL=http://evolution_api:8080 \
    -e EVOLUTION_API_KEY=global-api-key-evolution \
    -v /root/borges_os/public:/app/public \
    -v /root/borges_os/media_storage:/app/media_storage \
    borges_os-api 2>&1""", timeout=30))

# Aguardar e verificar
time.sleep(30)
print("\nStatus:")
print(run("docker ps -a | grep borges_os-api"))
print("\nLogs:")
print(run("docker logs borges_os-api-1 --tail 20 2>&1"))
print("\nHealth:")
print(run("curl -s --max-time 10 http://localhost:8000/health"))

ssh.close()
print("Concluido!")
