import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('187.77.253.67', port=22, username='root', password='Borges35133@')

python_cmd = '''import sqlite3; from core.security import get_password_hash; conn = sqlite3.connect("borges_os.db"); c = conn.cursor(); pwd = get_password_hash("123456"); c.execute("UPDATE users SET hashed_password = ? WHERE email = \\"admin@borges.com\\"", (pwd,)); conn.commit(); conn.close()'''

stdin, stdout, stderr = ssh.exec_command(f'cd /var/www/borges_os && ./venv/bin/python -c \'{python_cmd}\'')
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()
