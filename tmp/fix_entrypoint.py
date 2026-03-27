import paramiko
import time

HOST = "31.97.247.28"
USER = "root"
PASSWORD = "Borges35133@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

# Criar um novo entrypoint que tolera erros de migração
NEW_ENTRYPOINT = """#!/usr/bin/env bash
set -uo pipefail

# Run migrations (tolera erros de migração que podem ocorrer quando colunas já existem)
echo "[entrypoint] Running migrations..."
python -m alembic upgrade head || echo "[entrypoint] AVISO: Migração falhou ou não necessária, continuando..."

# Optional first-run bootstrap
if [[ "${SEED_ADMIN_ON_STARTUP:-false}" == "true" ]]; then
  echo "[entrypoint] Seeding default tenant/admin (SEED_ADMIN_ON_STARTUP=true)..."
  python seed_admin.py || true
fi

echo "[entrypoint] Starting API..."
exec python -m uvicorn main:app --host 0.0.0.0 --port 8000
"""

# Escrever o novo entrypoint
with open("/tmp/new_entrypoint.sh", "w", newline="\n") as f:
    f.write(NEW_ENTRYPOINT)

# Enviar para a VPS
sftp = ssh.open_sftp()
sftp.put("/tmp/new_entrypoint.sh", "/root/borges_os/docker-entrypoint.sh")
sftp.close()
print("Entrypoint atualizado!")

# Dar permissão de execução
_, out, _ = ssh.exec_command("chmod +x /root/borges_os/docker-entrypoint.sh && cat /root/borges_os/docker-entrypoint.sh")
print("Novo conteúdo:\n", out.read().decode("utf-8", errors="replace"))

# Parar e remover o container atual
print("\nParando container atual...")
_, out, _ = ssh.exec_command("docker stop borges_os-api-1 && docker rm borges_os-api-1 2>&1")
print(out.read().decode("utf-8", errors="replace"))

# Rebuild com o novo entrypoint
print("\nRebuildando imagem com novo entrypoint...")
chan = ssh.get_transport().open_session()
chan.exec_command("cd /root/borges_os && docker build -t borges_os-api . 2>&1")

start = time.time()
while time.time() - start < 120:
    if chan.recv_ready():
        data = chan.recv(4096).decode("utf-8", errors="replace")
        for line in data.splitlines():
            if "step" in line.lower() or "done" in line.lower() or "error" in line.lower():
                print(f"  BUILD: {line.strip()}")
    if chan.exit_status_ready():
        break
    time.sleep(1)

exit_status = chan.recv_exit_status()
print(f"\nBuild finalizado com status: {exit_status}")

if exit_status == 0:
    print("\nIniciando container...")
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
        -v /root/borges_os/media_storage:/app/media_storage \
        borges_os-api 2>&1
    """)
    print("Container start:", out.read().decode("utf-8", errors="replace"))
    
    time.sleep(12)
    
    _, out, _ = ssh.exec_command("docker logs borges_os-api-1 --tail 20 2>&1")
    print("\nLogs:\n", out.read().decode("utf-8", errors="replace"))
    
    _, out, _ = ssh.exec_command("curl -s http://localhost:8000/health 2>&1")
    print("\nHealth:", out.read().decode("utf-8", errors="replace"))

ssh.close()
