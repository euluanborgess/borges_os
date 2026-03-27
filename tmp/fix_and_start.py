import paramiko
import time

HOST = "31.97.247.28"
USER = "root"
PASSWORD = "Borges35133@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

print("Copiando main.py correto para dentro do container...")
_, out, err = ssh.exec_command("docker cp /root/borges_os/main.py borges_os-api-1:/app/main.py")
o = out.read().decode("utf-8", errors="replace")
e = err.read().decode("utf-8", errors="replace")
print(f"Copy result: {o}{e}")

print("\nValidando sintaxe dentro do container...")
_, out, err = ssh.exec_command("docker exec borges_os-api-1 python3 -c 'import ast; ast.parse(open(\"/app/main.py\").read()); print(\"SYNTAX OK\")' 2>&1 || echo 'SYNTAX ERROR'")
# Container is stopped, so exec won't work. Let's use a temp container instead
_, out, err = ssh.exec_command("python3 -c 'import ast; ast.parse(open(\"/root/borges_os/main.py\").read()); print(\"SYNTAX OK\")'")
o = out.read().decode("utf-8", errors="replace")
e = err.read().decode("utf-8", errors="replace")
print(f"Validação: {o}{e}")

# Tentar iniciar o container via docker compose v2
print("\nIniciando container via docker compose v2...")
_, out, err = ssh.exec_command("cd /root/borges_os && docker compose up -d api 2>&1")
o = out.read().decode("utf-8", errors="replace")
e = err.read().decode("utf-8", errors="replace")
print(f"docker compose result:\n{o}{e}")

time.sleep(5)

print("\nStatus dos containers...")
_, out, _ = ssh.exec_command("docker ps 2>&1")
print(out.read().decode("utf-8", errors="replace"))

# Se ainda com erro, verificar os logs
_, out, _ = ssh.exec_command("docker logs borges_os-api-1 --tail 15 2>&1")
print("Logs:\n", out.read().decode("utf-8", errors="replace"))

ssh.close()
print("Concluído!")
