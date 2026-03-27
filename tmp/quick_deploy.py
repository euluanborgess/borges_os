"""
Deploy do webhooks.py corrigido para a VPS + reiniciar o serviço
"""
import paramiko
import os

HOST = "31.97.247.28"
PORT = 22
USER = "root"
PASSWORD = "Borges35133@"
LOCAL_FILE = r"c:\Users\User\Documents\BorgesOS_Atualizado\api\routes\webhooks.py"
REMOTE_FILE = "/root/borges_os/api/routes/webhooks.py"

def deploy():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Conectando em {HOST}...")
    ssh.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=30)
    
    # Upload do arquivo
    print("Enviando webhooks.py...")
    sftp = ssh.open_sftp()
    sftp.put(LOCAL_FILE, REMOTE_FILE)
    sftp.close()
    print("Arquivo enviado!")
    
    # Reiniciar o serviço
    print("Reiniciando servidor...")
    stdin, stdout, stderr = ssh.exec_command("systemctl restart borges.service && sleep 3 && systemctl status borges.service | head -20")
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    print("STDOUT:", out)
    if err: print("STDERR:", err)
    
    ssh.close()
    print("Deploy concluído!")

if __name__ == "__main__":
    deploy()
