import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('187.77.253.67', port=22, username='root', password='Borges35133@')

# Define the exact lines we want
commands = [
    "sed -i 's|^DATABASE_URL=.*|DATABASE_URL=sqlite:///./borges_os.db|' /var/www/borges_os/.env",
    "sed -i 's|^PUBLIC_BASE_URL=.*|PUBLIC_BASE_URL=https://borgesos.com.br|' /var/www/borges_os/.env",
    "systemctl restart borges"
]

for cmd in commands:
    print(f"Running: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    print(stderr.read().decode())

ssh.close()
print("Env fix complete.")
