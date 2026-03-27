import paramiko

HOST = "31.97.247.28"
USER = "root"
PASSWORD = "Borges35133@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

# Verificar o main.py que está DENTRO do container (pode ser diferente do /root/borges_os/main.py)
_, out, _ = ssh.exec_command("docker cp borges_os-api-1:/app/main.py /tmp/api_main.py && sed -n '35,55p' /tmp/api_main.py")
print("main.py DENTRO DO CONTAINER:\n", out.read().decode("utf-8", errors="replace"))

_, out, _ = ssh.exec_command("cat /tmp/api_main.py | python3 -c 'import ast, sys; ast.parse(sys.stdin.read())' && echo 'SEM ERROS' || echo 'TEM ERROS DE SINTAXE'")
print("Validação sintaxe:\n", out.read().decode("utf-8", errors="replace"))

ssh.close()
