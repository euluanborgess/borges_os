import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('187.77.253.67', port=22, username='root', password='Borges35133@')

python_cmd = 'import sqlite3, json; conn = sqlite3.connect("borges_os.db"); c = conn.cursor(); c.execute("SELECT tenant_id FROM users WHERE email = \'atendimentocapitaojack@gmail.com\'"); tid = c.fetchone()[0]; c.execute("SELECT integrations FROM tenants WHERE id = ?", (tid,)); integ_str = c.fetchone()[0]; integ = json.loads(integ_str) if integ_str else {}; integ["instagram_token"] = None; integ["instagram_business_account_id"] = None; integ["instagram_connected"] = False; c.execute("UPDATE tenants SET integrations = ? WHERE id = ?", (json.dumps(integ), tid)); conn.commit(); conn.close(); print(f"Instagram disconnected for tenant {tid}")'

stdin, stdout, stderr = ssh.exec_command(f'cd /var/www/borges_os && ./venv/bin/python -c \'{python_cmd}\'')
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()
