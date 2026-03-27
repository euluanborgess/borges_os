import paramiko
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HOST = "31.97.247.28"
USER = "root"
PASSWORD = "Borges35133@"
LOCAL_BASE = r"c:\Users\User\Documents\BorgesOS_Atualizado"
REMOTE_BASE = "/root/borges_os"

FILES_TO_SYNC = [
    "api/routes/instagram.py",
    "api/routes/billing.py", 
    "api/routes/traffic.py",
    "api/routes/webhooks.py",
    "api/routes/inbox.py",
    "api/routes/super_admin.py",
    "api/routes/auth.py",
    "api/routes/ai.py",
    "api/routes/users.py",
    "api/routes/contracts.py",
    "api/routes/tasks.py",
    "api/routes/config.py",
    "api/routes/calendar.py",
    "api/routes/dashboard.py",
    "api/routes/agent_monitor.py",
    "main.py",
    "services/message_buffer.py",
    "services/websocket_manager.py",
]

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

sftp = ssh.open_sftp()
for f in FILES_TO_SYNC:
    local = LOCAL_BASE + "\\" + f.replace("/", "\\")
    remote = REMOTE_BASE + "/" + f
    try:
        sftp.put(local, remote)
        print(f"OK: {f}")
    except Exception as e:
        print(f"SKIP: {f} ({e})")
sftp.close()

print("\nTodos os arquivos sincronizados!")
print("Reiniciando container...")

_, out, _ = ssh.exec_command("docker restart borges_os-api-1 2>&1")
print(out.read().decode("utf-8", errors="replace"))

time.sleep(20)

def run(cmd):
    _, out, err = ssh.exec_command(cmd)
    return (out.read() + err.read()).decode("utf-8", errors="replace")

print("\nStatus:")
print(run("docker ps | grep borges_os-api"))
print("\nLogs:")
print(run("docker logs borges_os-api-1 --tail 25 2>&1"))
print("\nHealth:")
print(run("curl -s http://localhost:8000/health 2>&1"))

ssh.close()
