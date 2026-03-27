import paramiko

HOST = "31.97.247.28"
USER = "root"
PASSWORD = "Borges35133@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

# Descobrir o nome do serviço
_, out, _ = ssh.exec_command("systemctl list-units --type=service | grep -i borges")
print("Serviços borges:", out.read().decode(errors="replace"))

_, out, _ = ssh.exec_command("pm2 list 2>/dev/null || echo 'no pm2'")
print("PM2:", out.read().decode(errors="replace"))

_, out, _ = ssh.exec_command("ls /etc/systemd/system/*.service | grep -i borges 2>/dev/null")
print("Service files:", out.read().decode(errors="replace"))

_, out, _ = ssh.exec_command("pgrep -a python | head -5")
print("Python processes:", out.read().decode(errors="replace"))

ssh.close()
