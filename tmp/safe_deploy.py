import paramiko
import os

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
    if output: print(output)
    if error: print(f"Error: {error}")
    return exit_status, output, error

print("Connecting to VPS...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(IP, port=PORT, username=USER, password=PASSWORD)

print("Uploading Codebase...")
sftp = ssh.open_sftp()
sftp.put(LOCAL_ZIP, '/root/borges.zip')
sftp.close()

print("Unzipping and Restarting API (Safe Deploy)...")
commands = [
    "unzip -o /root/borges.zip -d /var/www/borges_os/",
    "cd /var/www/borges_os && ./venv/bin/pip install -r requirements.txt",
    "systemctl restart borges"
]

for c in commands:
    run_cmd(ssh, c)

ssh.close()
print("Safe Deployment Finished Successfully!")
