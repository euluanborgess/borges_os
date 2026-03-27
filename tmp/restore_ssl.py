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

print("Restaurando configuração de Nginx para suportar o domínio borgesos.com.br e HTTPS...")
nginx_conf = """server {
    server_name borgesos.com.br www.borgesos.com.br;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
"""

run(f"cat << 'EOF' > /etc/nginx/sites-available/borges\n{nginx_conf}EOF")
run("ln -sf /etc/nginx/sites-available/borges /etc/nginx/sites-enabled/")
run("systemctl reload nginx")

print("Rodando certbot para reinstalar os certificados SSL na configuração...")
print(run("certbot --nginx -d borgesos.com.br -d www.borgesos.com.br --non-interactive --agree-tos --redirect -m mcluvin.xyz@gmail.com"))

print("Status final do Nginx:")
print(run("systemctl status nginx --no-pager"))

ssh.close()
