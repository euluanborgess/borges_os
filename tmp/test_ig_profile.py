import requests

def test_profile():
    with open("tmp/meta_token.txt", "r") as f:
        token = f.read().strip()
        
    ig_sid = "6741197482560089"
    url = f"https://graph.facebook.com/v19.0/{ig_sid}?fields=name,profile_pic&access_token={token}"
    res = requests.get(url)
    print(res.status_code, res.text)

if __name__ == "__main__":
    test_profile()
