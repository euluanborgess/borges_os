import paramiko

HOST = "187.77.253.67"
USER = "root"
PASSWORD = "Borges35133@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

def run(cmd):
    _, out, err = ssh.exec_command(cmd)
    return (out.read() + err.read()).decode("utf-8", errors="replace")

print("Corrigindo o Nginx para habilitar WebSockets...")
script = """
awk '
/proxy_pass http:\\/\\/127\\.0\\.0\\.1:8000;/ {
    print $0
    print "        proxy_http_version 1.1;"
    print "        proxy_set_header Upgrade $http_upgrade;"
    print "        proxy_set_header Connection \"upgrade\";"
    next
}
{ print $0 }
' /etc/nginx/sites-available/borges > /tmp/borges_nginx_temp && mv /tmp/borges_nginx_temp /etc/nginx/sites-available/borges
"""

run(script)
print(run("systemctl reload nginx"))

print("Logs recentes para confirmar se WebSockets agora conectam (101 Switching Protocols):")
# Vamos buscar websocket no uvicorn e checar se mudou de 404 para conectando.
# Primeiro precisamos forçar um request. Mas logo vai aparecer.
print(run("journalctl -u borges.service -n 10 | grep -i 'websocket\|stream'"))

ssh.close()
