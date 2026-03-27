import paramiko

HOST = "31.97.247.28"
USER = "root"
PASSWORD = "Borges35133@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

cmds = [
    "docker logs borges_os-api-1 --tail 30 2>&1",  # Ver por que crashou
    "ls /root/06-03/",  # Outra pasta encontrada
    "cat /root/06-03/*.service 2>/dev/null || echo 'No service'",
    "netstat -tlnp 2>/dev/null | grep -E '(8000|80|443|5000|8080)' | head -20",
    "ss -tlnp | grep -E '(8000|80|443|5000)' | head -20",
    "cat /root/borges_os/.env | grep -v PASSWORD | grep -v KEY | head -15",
]

for cmd in cmds:
    _, out, err = ssh.exec_command(cmd)
    o = out.read().decode("utf-8", errors="replace")
    e = err.read().decode("utf-8", errors="replace")
    print(f"\n=== CMD: {cmd[:60]} ===\n{o}{e}")

ssh.close()
