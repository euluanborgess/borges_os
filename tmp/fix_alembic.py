import paramiko
import time

HOST = "31.97.247.28"
USER = "root"
PASSWORD = "Borges35133@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

# Checar o estado atual do alembic no banco
print("Verificando estado do Alembic...")
_, out, _ = ssh.exec_command("docker exec borges_os-db-1 psql -U borges -d borges_os -c \"SELECT version_num FROM alembic_version;\" 2>&1")
print(out.read().decode("utf-8", errors="replace"))

# Ver as revisões disponíveis localmente
_, out, _ = ssh.exec_command("ls /root/borges_os/alembic/versions/ | head -20")
revisions = out.read().decode("utf-8", errors="replace")
print("Revisões disponíveis:\n", revisions)

# A solução é limpar a versão errada do alembic_version e configurar para a head
print("\nCorrigindo versão do Alembic (configurando para head)...")
_, out, _ = ssh.exec_command("docker exec borges_os-db-1 psql -U borges -d borges_os -c \"DELETE FROM alembic_version;\" 2>&1")
print("DELETE:", out.read().decode("utf-8", errors="replace"))

# Ver qual é a head revision disponível
_, out, _ = ssh.exec_command("ls /root/borges_os/alembic/versions/ | sort -r | head -1")
head_file = out.read().decode("utf-8", errors="replace").strip()
print("Head file:", head_file)

# Extrair o hash da revisão do nome do arquivo (ex: abc123_add_field.py -> abc123)
if head_file:
    head_hash = head_file.split("_")[0]
    print(f"Head hash: {head_hash}")
    
    # Inserir a revisão correta
    _, out, _ = ssh.exec_command(f"docker exec borges_os-db-1 psql -U borges -d borges_os -c \"INSERT INTO alembic_version (version_num) VALUES ('{head_hash}');\" 2>&1")
    print("INSERT:", out.read().decode("utf-8", errors="replace"))

# Reiniciar o container
print("\nReiniciando container...")
_, out, _ = ssh.exec_command("docker restart borges_os-api-1 && sleep 10 && docker logs borges_os-api-1 --tail 20 2>&1")
print(out.read().decode("utf-8", errors="replace"))

# Testar se a API está respondendo
time.sleep(5)
_, out, _ = ssh.exec_command("curl -s http://localhost:8000/health 2>&1")
print("Health check:", out.read().decode("utf-8", errors="replace"))

ssh.close()
