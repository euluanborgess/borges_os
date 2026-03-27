import urllib.request
import urllib.parse
import json
import urllib.error
import sys

data = urllib.parse.urlencode({"username": "admin@borges.com", "password": "admin123456"}).encode()
req_login = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/auth/login', data=data, headers={"Content-Type": "application/x-www-form-urlencoded"}
)
token = json.loads(urllib.request.urlopen(req_login).read())["access_token"]

payload = {"lead_id": None, "type": "task", "title": "Teste Manual", "description": "Teste Python", "status": "pending", "due_date": None}
req_task = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/ws/tasks/', data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
)
try:
    print("Success:", urllib.request.urlopen(req_task).read().decode())
except Exception as e:
    print(e.read().decode())
