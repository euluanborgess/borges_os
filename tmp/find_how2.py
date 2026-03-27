import paramiko
import sys

HOST = "31.97.247.28"
USER = "root"
PASSWORD = "Borges35133@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

cmds = [
    ("ps -ef | grep -E '(uvicorn|gunicorn|main.py)' | grep -v grep", "Uvicorn/gunicorn"),
    ("ls /etc/nginx/conf.d/ 2>/dev/null || echo 'no conf.d'", "Nginx conf.d"),
    ("cat /root/borges_os/docker-compose.yml | grep -A5 'api\\|borges' | head -40", "docker-compose"),
    ("docker ps -a 2>/dev/null | head -20", "Docker all containers"),
]
for cmd, label in cmds:
    _, out, err = ssh.exec_command(cmd)
    o = out.read().decode("utf-8", errors="replace")
    e = err.read().decode("utf-8", errors="replace")
    print(f"\n=== {label} ===\n{o}{e}")

ssh.close()
