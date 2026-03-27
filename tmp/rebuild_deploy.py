import paramiko
import time

HOST = "31.97.247.28"
USER = "root"
PASSWORD = "Borges35133@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

# Enviar main.py correto
sftp = ssh.open_sftp()
sftp.put(r"c:\Users\User\Documents\BorgesOS_Atualizado\main.py", "/root/borges_os/main.py")
print("main.py enviado!")

# Enviar webhooks.py corrigido (já feito, mas garantir)
sftp.put(r"c:\Users\User\Documents\BorgesOS_Atualizado\api\routes\webhooks.py", "/root/borges_os/api/routes/webhooks.py")
print("webhooks.py enviado!")
sftp.close()

# Rebuild e restart do container
print("\nReconstruindo container (pode demorar ~60s)...")
_, out, err = ssh.exec_command("cd /root/borges_os && docker-compose build api && docker-compose up -d api", get_pty=True)

# Aguardar até 120 segundos pelo output
import time
start = time.time()
while time.time() - start < 120:
    line = out.readline()
    if not line:
        break
    print(line.strip())

print("\nVerificando status...")
_, out2, _ = ssh.exec_command("docker ps | grep borges_os-api")
print(out2.read().decode("utf-8", errors="replace"))

_, out3, _ = ssh.exec_command("docker logs borges_os-api-1 --tail 20 2>&1")
print("\nLogs:\n", out3.read().decode("utf-8", errors="replace"))

ssh.close()
print("\nConcluído!")
