import paramiko

HOST = "31.97.247.28"
USER = "root"
PASSWORD = "Borges35133@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

def run(cmd):
    _, out, err = ssh.exec_command(cmd)
    return (out.read() + err.read()).decode("utf-8", errors="replace")

py_script = """
import os
import sys
sys.path.append("/app")
from core.database import SessionLocal
from models.lead import Lead

db = SessionLocal()
leads = db.query(Lead).order_by(Lead.created_at.desc()).limit(10).all()
print("LEADS NA API (via SQLAlchemy):")
for L in leads:
    print(f"ID={L.id} Name='{L.name}' Phone='{L.phone}' Channel='{L.channel}'")
"""

with open("query_inside_docker.py", "w", encoding="utf-8") as f:
    f.write(py_script)

sftp = ssh.open_sftp()
sftp.put("query_inside_docker.py", "/root/borges_os/query_inside_docker.py")
sftp.close()

print(run("docker cp /root/borges_os/query_inside_docker.py borges_os-api-1:/app/query_inside_docker.py"))
print(run("docker exec borges_os-api-1 python /app/query_inside_docker.py"))

ssh.close()
