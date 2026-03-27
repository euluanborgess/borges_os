import sqlite3, requests, json

APP_ID = "892306240471319"
APP_SECRET = "b16ba38b8554c6208d5bbe77dd2f0382" # Using the one user shared recently

conn = sqlite3.connect('borges_os.db')
c = conn.cursor()
c.execute("SELECT access_token FROM ad_accounts WHERE id = '4ba22262-4831-4081-97f0-4588ff8a32ac'")
row = c.fetchone()
if row:
    token = row[0]
    # Debug the token using App Token
    app_token = f"{APP_ID}|{APP_SECRET}"
    url = f"https://graph.facebook.com/v19.0/debug_token?input_token={token}&access_token={app_token}"
    res = requests.get(url)
    print("DEBUG_TOKEN:")
    print(json.dumps(res.json(), indent=2))
conn.close()
