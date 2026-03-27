import paramiko

HOST = "31.97.247.28"
USER = "root"
PASSWORD = "Borges35133@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

# Ver todos os serviços ativos
_, out, _ = ssh.exec_command("systemctl list-units --type=service --state=running | head -40")
print("Serviços rodando:\n", out.read().decode(errors="replace"))

# Ver o Nginx e buscar a porta que está roteando
_, out, _ = ssh.exec_command("ls /etc/nginx/ && cat /etc/nginx/nginx.conf | head -30")
print("\nNginx config:\n", out.read().decode(errors="replace"))

# Ver se existe um arquivo de serviço na pasta /etc/systemd
_, out, _ = ssh.exec_command("find /etc/systemd -name '*.service' -newer /etc/hosts 2>/dev/null | head -20")
print("\nServices criados recentemente:\n", out.read().decode(errors="replace"))

# Todos os processos python/uvicorn incluindo root
_, out, _ = ssh.exec_command("ps -ef | grep -E '(uvicorn|gunicorn|main.py)' | grep -v grep")
print("\nProcessos uvicorn/gunicorn:\n", out.read().decode(errors="replace"))

# Ver o cloudflared que pode estar sendo usado como tunnel
_, out, _ = ssh.exec_command("ps -ef | grep cloudflared | grep -v grep | head -5")
print("\nCloudflared:\n", out.read().decode(errors="replace"))

ssh.close()
