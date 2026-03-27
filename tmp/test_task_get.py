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

req_task_get = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/ws/tasks/', headers={"Authorization": f"Bearer {token}"}
)
try:
    print("Success:", urllib.request.urlopen(req_task_get).read().decode())
except Exception as e:
    print("Erro:")
    print(e.read().decode())
