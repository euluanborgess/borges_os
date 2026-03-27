import paramiko
import os
import time

IP = '187.77.253.67'
USER = 'root'
PASSWORD = 'Borges35133@'
PORT = 22
LOCAL_ZIP = 'c:/Users/User/Documents/BorgesOS_Atualizado/borges.zip'

def run_cmd(ssh, cmd):
    print(f"#> {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8', errors='replace').strip()
    error = stderr.read().decode('utf-8', errors='replace').strip()
    if output:
        try:
            print(output)
        except UnicodeEncodeError:
            print(output.encode('ascii', 'replace').decode('ascii'))
    if error:
        try:
            print(f"Error: {error}")
        except UnicodeEncodeError:
            print(f"Error: {error.encode('ascii', 'replace').decode('ascii')}")
    return exit_status, output, error

print("Connecting to VPS...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(IP, port=PORT, username=USER, password=PASSWORD)

print("Uploading Codebase...")
sftp = ssh.open_sftp()
sftp.put(LOCAL_ZIP, '/root/borges.zip')
sftp.close()

print("Setting up Ubuntu Environment...")
commands = [
    "apt-get update",
    "DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pip python3-venv unzip nginx python3-certbot-nginx sqlite3 curl",
    "mkdir -p /var/www/borges_os",
    "unzip -o /root/borges.zip -d /var/www/borges_os/",
    "cd /var/www/borges_os && python3 -m venv venv",
    "cd /var/www/borges_os && ./venv/bin/pip install --upgrade pip",
    "cd /var/www/borges_os && ./venv/bin/pip install -r requirements.txt",
]

for c in commands:
    run_cmd(ssh, c)

# Setup Systemd Service
service_content = """[Unit]
Description=Borges OS FastAPI Server
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/borges_os
Environment="PATH=/var/www/borges_os/venv/bin"
ExecStart=/var/www/borges_os/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
"""
run_cmd(ssh, f"cat << 'EOF' > /etc/systemd/system/borges.service\n{service_content}EOF")
run_cmd(ssh, "systemctl daemon-reload")
run_cmd(ssh, "systemctl enable borges")
run_cmd(ssh, "systemctl restart borges")

# Setup Nginx
nginx_conf = """server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
"""
run_cmd(ssh, f"cat << 'EOF' > /etc/nginx/sites-available/borges\n{nginx_conf}EOF")
run_cmd(ssh, "ln -sf /etc/nginx/sites-available/borges /etc/nginx/sites-enabled/")
run_cmd(ssh, "rm -f /etc/nginx/sites-enabled/default")
run_cmd(ssh, "systemctl restart nginx")

ssh.close()
print("Deployment Baseline Finished Successfully!")
