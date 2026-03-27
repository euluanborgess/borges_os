import paramiko
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HOST = "31.97.247.28"
USER = "root"
PASSWORD = "Borges35133@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

def run(cmd, timeout=10):
    _, out, err = ssh.exec_command(cmd, timeout=timeout)
    return (out.read() + err.read()).decode("utf-8", errors="replace")

# Aguardar reinício
time.sleep(5)
# Pegar logs completos desde o início do container
print(run("docker logs borges_os-api-1 2>&1 | tail -60"))

ssh.close()
