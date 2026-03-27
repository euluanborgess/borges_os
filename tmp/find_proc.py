import paramiko

HOST = "31.97.247.28"
USER = "root"
PASSWORD = "Borges35133@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

# Docker check
_, out, _ = ssh.exec_command("docker ps 2>/dev/null | head -20")
print("Docker containers:", out.read().decode(errors="replace"))

# Nginx check - confirmar proxy
_, out, _ = ssh.exec_command("ls /etc/nginx/sites-enabled/")
print("Nginx sites:", out.read().decode(errors="replace"))

# Procurar processo uvicorn/gunicorn
_, out, _ = ssh.exec_command("ps aux | grep -E '(uvicorn|gunicorn|python)' | grep -v grep | head -10")
print("Python/uvicorn procs:", out.read().decode(errors="replace"))

# Ver onde está o código
_, out, _ = ssh.exec_command("ls /root/")
print("Root dir:", out.read().decode(errors="replace"))

_, out, _ = ssh.exec_command("ls /root/borges_os/ 2>/dev/null || ls /root/ | head -20")
print("App dir:", out.read().decode(errors="replace"))

ssh.close()
