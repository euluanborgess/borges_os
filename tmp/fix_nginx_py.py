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

py_script = """
import os

filepath = "/etc/nginx/sites-available/borges"
with open(filepath, "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "proxy_set_header Connection ;" in line:
        continue # Remover linha quebrada
    if "proxy_http_version 1.1;" in line:
        continue # Remover tentativas anteriores
    if "proxy_set_header Upgrade $http_upgrade;" in line:
        continue # Remover tentativas anteriores
        
    new_lines.append(line)
    if "proxy_pass http://127.0.0.1:8000;" in line:
        new_lines.append("        proxy_http_version 1.1;\\n")
        new_lines.append("        proxy_set_header Upgrade $http_upgrade;\\n")
        new_lines.append("        proxy_set_header Connection \\"upgrade\\";\\n")

with open(filepath, "w") as f:
    f.writelines(new_lines)
print("Arquivo Nginx atualizado via python no servidor.")
"""

print("Corrigindo Nginx:")
sftp = ssh.open_sftp()
with sftp.file('/root/fix_nginx.py', 'w') as f: f.write(py_script)
sftp.close()

print(run("python3 /root/fix_nginx.py"))
print(run("nginx -t"))
print(run("systemctl reload nginx"))

ssh.close()
