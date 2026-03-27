import urllib.request
import urllib.parse
import json
import urllib.error
import sys

# Login para pegar token
data = urllib.parse.urlencode({"username": "admin@borges.com", "password": "admin123456"}).encode()
req_login = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/auth/login',
    data=data,
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)
try:
    res_login = urllib.request.urlopen(req_login)
    token = json.loads(res_login.read())["access_token"]
except urllib.error.HTTPError as e:
    print(f"Login failed: {e.code}")
    print(e.read().decode())
    sys.exit(1)

# Request problemático de criação de leads
payload = {
    "name": "Lead Test",
    "email": "test@t.com",
    "phone": "11999999999",
    "pipeline_stage": "lead",
    "temperature": "frio"
}

req_lead = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/ws/inbox/leads',
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
)

try:
    res_lead = urllib.request.urlopen(req_lead)
    print("Success:", res_lead.read().decode())
except urllib.error.HTTPError as e:
    print(f"Lead creation failed: {e.code}")
    print(e.read().decode())
