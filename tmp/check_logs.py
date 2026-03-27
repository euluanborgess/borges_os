import paramiko

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect('187.77.253.67', username='root', password='Borges35133@')
stdin, stdout, stderr = s.exec_command('journalctl -u borges -n 500 --no-pager')
logs = stdout.read().decode('utf-8', errors='replace')
for line in logs.split('\n'):
    if 'pages_messaging' in line or 'Graph' in line or 'erro' in line.lower() or 'oauth' in line.lower():
        print(line)
s.close()
