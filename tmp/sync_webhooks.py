import paramiko
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HOST = "31.97.247.28"
USER = "root"
PASSWORD = "Borges35133@"
LOCAL_FILE = r"c:\Users\User\Documents\BorgesOS_Atualizado\api\routes\webhooks.py"
REMOTE_FILE = "/root/borges_os/api/routes/webhooks.py"
CONTAINER_FILE = "/app/api/routes/webhooks.py"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

def run(cmd):
    _, out, err = ssh.exec_command(cmd)
    return (out.read() + err.read()).decode("utf-8", errors="replace")

print("Enviando webhooks.py para a VPS...")
sftp = ssh.open_sftp()
sftp.put(LOCAL_FILE, REMOTE_FILE)
sftp.close()

print("Copiando para dentro do container...")
print(run(f"docker cp {REMOTE_FILE} borges_os-api-1:{CONTAINER_FILE}"))

print("Reiniciando container da API...")
print(run("docker restart borges_os-api-1"))
time.sleep(15)

print("\nStatus:")
print(run("docker ps | grep borges_os-api"))
print("\nLogs (verificando startup):")
print(run("docker logs borges_os-api-1 --tail 15 2>&1"))

ssh.close()
