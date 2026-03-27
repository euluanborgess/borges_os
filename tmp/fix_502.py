import paramiko

IP = '187.77.253.67'
USER = 'root'
PASSWORD = 'Borges35133@'
PORT = 22

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(IP, port=PORT, username=USER, password=PASSWORD)

def run_cmd(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    output = stdout.read().decode('utf-8', errors='replace').strip()
    error = stderr.read().decode('utf-8', errors='replace').strip()
    return output, error

print("Installing instagrapi...")
out, err = run_cmd("cd /var/www/borges_os && ./venv/bin/pip install instagrapi")
if out: print(out)
if err: print(f"Error: {err}")

print("Restarting borges service...")
run_cmd("systemctl restart borges")

out, err = run_cmd("systemctl status borges --no-pager")
if out: print(out)

ssh.close()
