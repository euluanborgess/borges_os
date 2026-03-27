import requests
import json

def blast():
    url = "http://127.0.0.1:8000/api/v1/webhooks/meta"
    payload = {
        "object": "instagram",
        "entry": [
            {
                "time": 1234567,
                "id": "17841455926157544",
                "messaging": [
                    {
                        "sender": {"id": "1234567890"},
                        "recipient": {"id": "17841455926157544"},
                        "timestamp": 1234567,
                        "message": {
                            "mid": "mid.123",
                            "text": "Teste Local do Webhook!"
                        }
                    }
                ]
            }
        ]
    }
    
    print("Enviando Fake Webhook...")
    res = requests.post(url, json=payload)
    print(res.status_code, res.text)
    
if __name__ == "__main__":
    blast()
