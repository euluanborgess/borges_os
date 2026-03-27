import paramiko
import os

IP = '187.77.253.67'
USER = 'root'
PASSWORD = 'Borges35133@'
PORT = 22
REMOTE_ZIP_PATH = '/root/borges_vps_backup.zip'
LOCAL_ZIP_PATH = r'c:\Users\User\Documents\BorgesOS_Atualizado\borges_vps_backup.zip'

def run():
    print("Conectando na VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(IP, port=PORT, username=USER, password=PASSWORD)

    print("Instalando o pacote zip se necessário...")
    _, out, _ = ssh.exec_command('apt-get update && apt-get install -y zip')
    out.channel.recv_exit_status()
    
    print("Compactando a pasta /var/www/borges_os na VPS (ignorando venv e pycache)...")
    cmd = 'cd /var/www/borges_os && zip -r /root/borges_vps_backup.zip . -x "venv/*" "__pycache__/*" ".git/*" "node_modules/*"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    # Wait for the command to finish
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        print(f"Aviso na compactação: {stderr.read().decode('utf-8')}")
    else:
        print("Compactação na VPS concluída!")

    print("Baixando o arquivo ZIP para a sua máquina local...")
    sftp = ssh.open_sftp()
    
    def print_progress(transferred, total):
        print(f"Progresso do download: {transferred}/{total} bytes", end='\r')
        
    sftp.get(REMOTE_ZIP_PATH, LOCAL_ZIP_PATH, callback=print_progress)
    sftp.close()
    ssh.close()
    print("\nDownload concluído com sucesso!")

if __name__ == "__main__":
    run()
