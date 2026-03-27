import paramiko

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect('187.77.253.67', username='root', password='Borges35133@')
_, out, _ = s.exec_command('journalctl -u borges -n 500 --no-pager | grep -i "meta callback"')
print(out.read().decode('utf-8'))
s.close()
