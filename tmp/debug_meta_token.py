import requests
from dotenv import load_dotenv
import os

load_dotenv("c:\\Users\\User\\Documents\\BorgesOS_Atualizado\\.env")
app_id = os.environ.get("META_APP_ID")
app_secret = os.environ.get("META_APP_SECRET")

def debug():
    try:
        with open("tmp/meta_token.txt", "r") as f:
            token = f.read().strip()
    except Exception:
        print("Token file not found.")
        return

    print("Fetching /debug_token...")
    url = f"https://graph.facebook.com/debug_token?input_token={token}&access_token={app_id}|{app_secret}"
    res = requests.get(url)
    print(res.json())

    print("\nFetching /me/permissions...")
    res3 = requests.get(f"https://graph.facebook.com/v19.0/me/permissions?access_token={token}")
    print(res3.json())

    print("\nFetching /me/accounts...")
    res2 = requests.get(f"https://graph.facebook.com/v19.0/me/accounts?fields=id,name,instagram_business_account&access_token={token}")
    print(res2.json())

if __name__ == "__main__":
    debug()
