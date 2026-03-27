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

def run(cmd, timeout=15):
    _, out, err = ssh.exec_command(cmd, timeout=timeout)
    return (out.read() + err.read()).decode("utf-8", errors="replace")

# Parar container
print("Parando container...")
print(run("docker stop borges_os-api-1"))
time.sleep(2)

# Copiar arquivo corrigido para dentro do container
sftp = ssh.open_sftp()
sftp.put(LOCAL_BASE + r"\api\routes\instagram.py", "/root/borges_os/api/routes/instagram.py")
sftp.close()

print("Copiando instagram.py corrigido para dentro do container...")
print(run("docker cp /root/borges_os/api/routes/instagram.py borges_os-api-1:/app/api/routes/instagram.py"))

# Iniciar container
print("Iniciando container...")
print(run("docker start borges_os-api-1"))

time.sleep(20)

print("Status:")
print(run("docker ps | grep borges_os-api"))
print("Logs:")
print(run("docker logs borges_os-api-1 --tail 30 2>&1"))
print("Health:")
print(run("curl -s --max-time 5 http://localhost:8000/health"))

ssh.close()
