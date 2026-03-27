import paramiko
import sys
import io
import time
import os

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

sftp = ssh.open_sftp()

# Sincronizar toda a pasta services/
services_local = os.path.join(LOCAL_BASE, "services")
for filename in os.listdir(services_local):
    if filename.endswith(".py"):
        local_path = os.path.join(services_local, filename)
        remote_host_path = f"/root/borges_os/services/{filename}"
        container_path = f"/app/services/{filename}"
        try:
            sftp.put(local_path, remote_host_path)
            print(f"  HOST OK: services/{filename}")
        except Exception as e:
            print(f"  HOST SKIP: services/{filename} ({e})")

# Sincronizar modelos e core também
for folder in ["models", "core", "api/routes", "api"]:
    local_folder = os.path.join(LOCAL_BASE, folder.replace("/", "\\"))
    if os.path.isdir(local_folder):
        for filename in os.listdir(local_folder):
            if filename.endswith(".py"):
                local_path = os.path.join(local_folder, filename)
                remote_host_path = f"/root/borges_os/{folder}/{filename}"
                try:
                    sftp.put(local_path, remote_host_path)
                except Exception as e:
                    pass

sftp.close()

# Copiar todos de uma vez com docker cp da pasta inteira
print("\nCopiando services/ para container...")
print(run("docker cp /root/borges_os/services/. borges_os-api-1:/app/services/"))
print("Copiando models/ para container...")
print(run("docker cp /root/borges_os/models/. borges_os-api-1:/app/models/"))
print("Copiando api/ para container...")
print(run("docker cp /root/borges_os/api/. borges_os-api-1:/app/api/"))
print("Copiando main.py para container...")
print(run("docker cp /root/borges_os/main.py borges_os-api-1:/app/main.py"))

# Iniciar container
print("\nIniciando container...")
print(run("docker start borges_os-api-1"))
time.sleep(25)

print("Status:")
print(run("docker ps | grep borges_os-api"))
print("Logs:")
print(run("docker logs borges_os-api-1 --tail 30 2>&1"))
print("Health:")
print(run("curl -s --max-time 8 http://localhost:8000/health"))

ssh.close()
print("Concluido!")
