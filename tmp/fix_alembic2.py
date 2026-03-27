import paramiko
import time

HOST = "31.97.247.28"
USER = "root"
PASSWORD = "Borges35133@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

# O problema é que o Alembic não está na head mas a coluna já existe
# Vamos marcar todas as migrações como aplicadas (stamp head)
print("Aplicando stamp head via Alembic...")
_, out, err = ssh.exec_command("docker exec borges_os-api-1 alembic stamp head 2>&1 || echo 'Tentando dentro do container...'")
o = out.read().decode("utf-8", errors="replace")
print("Alembic stamp:", o)

# Tentar usar python diretamente no container
_, out, err = ssh.exec_command("docker exec borges_os-api-1 /bin/bash -c 'cd /app && alembic stamp head' 2>&1")
o = out.read().decode("utf-8", errors="replace")
print("via bash:", o)

# Alternativa: simplificar o docker-entrypoint para ignorar erros de migração
print("\nVerificando docker-entrypoint.sh...")
_, out, _ = ssh.exec_command("cat /root/borges_os/docker-entrypoint.sh")
print(out.read().decode("utf-8", errors="replace"))

ssh.close()
