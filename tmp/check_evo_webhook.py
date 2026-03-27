import paramiko
import requests

HOST = "187.77.253.67"
USER = "root"
PASSWORD = "Borges35133@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

def run(cmd):
    _, out, err = ssh.exec_command(cmd)
    return (out.read() + err.read()).decode("utf-8", errors="replace")

print("Obtendo as instâncias configuradas da Evolution API para o Tenant...")
sql = "SELECT evolution_instance_id FROM tenants LIMIT 1;"
res = run(f"docker exec borges_os-db-1 psql -U borges -d borges_os -t -c \"{sql}\"")
instance_id = res.strip()
print(f"Instância encontrada: {instance_id}")

ssh.close()

if instance_id:
    evo_url = "http://31.97.247.28:8080"
    evo_key = "global-api-key-evolution"
    print(f"\nBuscando webhook da Evolution API para a instância {instance_id}")
    try:
        r = requests.get(f"{evo_url}/webhook/find/{instance_id}", headers={"apikey": evo_key})
        print(f"Status: {r.status_code}")
        print(r.json())
        
        # Também verificar integração do Instagram
        print("\nVerificando fetchInstances para ver todas instâncias:")
        r2 = requests.get(f"{evo_url}/instance/fetchInstances", headers={"apikey": evo_key})
        instances = r2.json()
        for i in instances:
            name = i.get('instance', {}).get('instanceName')
            print(f"Instância NOME: {name}")
            # Buscar webhook dessa instância
            r3 = requests.get(f"{evo_url}/webhook/find/{name}", headers={"apikey": evo_key})
            print(f"  Webhook config para {name}: {r3.json()}")
    except Exception as e:
        print(e)
