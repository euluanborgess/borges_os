import paramiko
import time

HOST = "31.97.247.28"
USER = "root"
PASSWORD = "Borges35133@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

# Passo 1: Parar o container e remover a imagem antiga
print("Parando container antigo...")
_, out, _ = ssh.exec_command("docker stop borges_os-api-1 && docker rm borges_os-api-1 && docker rmi borges_os-api 2>&1")
print(out.read().decode("utf-8", errors="replace"))
time.sleep(2)

# Passo 2: Verificar se o main.py local na VPS está OK
_, out, _ = ssh.exec_command("python3 -c 'import ast; ast.parse(open(\"/root/borges_os/main.py\").read()); print(\"main.py OK\")'")
print("Validação main.py:", out.read().decode("utf-8", errors="replace"))

# Passo 3: Build da nova imagem
print("\nRebuildando imagem Docker (pode demorar 2-5 min)...")
chan = ssh.get_transport().open_session()
chan.exec_command("cd /root/borges_os && docker build -t borges_os-api . 2>&1")

# Aguardar o build com timeout de 5 minutos
start = time.time()
outputs = []
while time.time() - start < 300:
    if chan.recv_ready():
        data = chan.recv(4096).decode("utf-8", errors="replace")
        outputs.append(data)
        # Mostrar apenas linhas chave
        for line in data.splitlines():
            if any(x in line.lower() for x in ["step", "error", "warn", "success", "done", "complete"]):
                print(f"  BUILD: {line.strip()}")
    if chan.exit_status_ready():
        break
    time.sleep(1)

exit_status = chan.recv_exit_status()
print(f"\nBuild finalizado com status: {exit_status}")

if exit_status == 0:
    # Passo 4: Iniciar o container com a nova imagem
    print("\nIniciando container com nova imagem...")
    _, out, _ = ssh.exec_command("""
    docker run -d \
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
        -v /root/borges_os/borges_os.db:/app/borges_os.db \
        -v /root/borges_os/media_storage:/app/media_storage \
        borges_os-api 2>&1
    """)
    print("Start:", out.read().decode("utf-8", errors="replace"))
    
    time.sleep(8)
    _, out, _ = ssh.exec_command("docker ps | grep borges_os-api && echo 'CONTAINER RODANDO!'")
    print(out.read().decode("utf-8", errors="replace"))
    
    _, out, _ = ssh.exec_command("docker logs borges_os-api-1 --tail 20 2>&1")
    print("Logs recentes:\n", out.read().decode("utf-8", errors="replace"))
else:
    print("BUILD FALHOU! Ver logs completos:")
    print("".join(outputs)[-2000:])

ssh.close()
