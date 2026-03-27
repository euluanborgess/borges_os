import requests

evo_url = "http://31.97.247.28:8080"
evo_key = "global-api-key-evolution"

print("Listando instâncias:")
r = requests.get(f"{evo_url}/instance/fetchInstances", headers={"apikey": evo_key})
instances = r.json()

for i in instances:
    name = i.get('instance', {}).get('instanceName')
    if not name:
        continue
    print(f"\n--- Instância: {name} ---")
    
    r_wh = requests.get(f"{evo_url}/webhook/find/{name}", headers={"apikey": evo_key})
    print("Webhook:", r_wh.json())
