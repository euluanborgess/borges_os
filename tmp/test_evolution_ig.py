import requests
import os
from dotenv import load_dotenv

load_dotenv("C:\\Users\\User\\Documents\\BorgesOS_Atualizado\\.env")

api_url = os.environ.get("EVOLUTION_API_URL")
api_key = os.environ.get("EVOLUTION_API_KEY")

def test_evolution_ig():
    print("Creating Instagram Instance on Evolution API...")
    url = f"{api_url}/instance/create"
    headers = {
        "apikey": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "instanceName": "test_insta_borges",
        "integration": "INSTAGRAM",
        "token": "admin_uuid123"
    }
    
    res = requests.post(url, headers=headers, json=payload)
    print("Status:", res.status_code)
    print("Response:", res.text)

if __name__ == "__main__":
    test_evolution_ig()
