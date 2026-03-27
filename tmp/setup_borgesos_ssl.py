import paramiko
import time

IP = '187.77.253.67'
USER = 'root'
PASSWORD = 'Borges35133@'
PORT = 22
DOMAIN = 'borgesos.com.br'

print(f"Connecting to VPS for SSL setup on {DOMAIN}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(IP, port=PORT, username=USER, password=PASSWORD)

def run_cmd(cmd):
    print(f"#> {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8', errors='replace').strip()
    error = stderr.read().decode('utf-8', errors='replace').strip()
    if output:
        try:
            print(output)
        except UnicodeEncodeError:
            print(output.encode('ascii','replace').decode('ascii'))
    if error:
        try:
            print(f"Error: {error}")
        except UnicodeEncodeError:
            print(f"Error: {error.encode('ascii','replace').decode('ascii')}")
    return exit_status

# Update Nginx Server Block with correct domain
nginx_conf = f"""server {{
    listen 80;
    server_name {DOMAIN} www.{DOMAIN};

    location / {{
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""

print("Updating Nginx config...")
run_cmd(f"cat << 'EOF' > /etc/nginx/sites-available/borges\n{nginx_conf}EOF")
run_cmd("systemctl reload nginx")

print("Waiting 30s for DNS propagation...")
time.sleep(30)

print(f"Running Certbot for {DOMAIN}...")
# Try with -d DOMAIN -d www.DOMAIN
cmd = f"certbot --nginx -d {DOMAIN} -d www.{DOMAIN} --non-interactive --agree-tos -m atendimentocapitaojack@gmail.com"
exit_code = run_cmd(cmd)

if exit_code != 0:
    print("Certbot failed, probably due to propagation. Will try again later.")
else:
    print("SSL setup complete! Updating environment variables...")
    # Update HOSTNAME in .env or main.py if needed
    run_cmd(f"sed -i 's|BASE_URL=.*|BASE_URL=https://{DOMAIN}|' /var/www/borges_os/.env")
    run_cmd("systemctl restart borges")

ssh.close()
