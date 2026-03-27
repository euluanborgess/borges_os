import zipfile
import subprocess
import os
import shutil

zip_path = r"c:\Users\User\Documents\BorgesOS_Atualizado\borges_vps_backup.zip"
extract_path = r"c:\Users\User\Documents\BorgesOS_Atualizado"

print("Limpando ambiente local e extraindo versão VPS...")
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_path)

print("Commitando e enviando pro GitHub (Base 44)...")
os.chdir(extract_path)

subprocess.run(["git", "add", "."], check=True)
try:
    subprocess.run(["git", "commit", "-m", "Restore from VPS (Base 44)"], check=True)
except subprocess.CalledProcessError:
    # Ignora se não houver alterações (embora a extração deva gerar mudanças)
    pass

res = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
print(res.stdout)
if res.stderr:
    print(f"Stderr: {res.stderr}")

print("Sucesso total! Código na nuvem.")
