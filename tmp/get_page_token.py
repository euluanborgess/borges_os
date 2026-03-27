import requests

def get_page_token():
    with open("tmp/meta_token.txt", "r") as f:
        user_token = f.read().strip()
        
    page_id = "109826838567470"
    url = f"https://graph.facebook.com/v19.0/{page_id}?fields=access_token&access_token={user_token}"
    
    print(f"Requesting Page Access Token directly...")
    res = requests.get(url)
    data = res.json()
    print(data)
    
    if "access_token" in data:
        page_token = data["access_token"]
        print("\nGOT PAGE TOKEN! Subscribing...")
        sub_res = requests.post(f"https://graph.facebook.com/v19.0/{page_id}/subscribed_apps", params={
            "subscribed_fields": "messages,messaging_postbacks",
            "access_token": page_token
        })
        print(sub_res.status_code, sub_res.text)

if __name__ == "__main__":
    get_page_token()
