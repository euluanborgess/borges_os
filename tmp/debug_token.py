import sqlite3, requests, json

conn = sqlite3.connect('borges_os.db')
c = conn.cursor()
c.execute("SELECT access_token FROM ad_accounts WHERE id = '4ba22262-4831-4081-97f0-4588ff8a32ac'")
row = c.fetchone()
if not row:
    print("Account not found")
else:
    token = row[0]
    print(f"Token len: {len(token)}")
    url = f"https://graph.facebook.com/v19.0/debug_token?input_token={token}&access_token={token}"
    res = requests.get(url)
    print(json.dumps(res.json(), indent=2))
    
    # Try the me/adaccounts endpoint
    res2 = requests.get(f"https://graph.facebook.com/v19.0/me/adaccounts?fields=name,account_id,account_status&access_token={token}")
    print("\nme/adaccounts:")
    print(json.dumps(res2.json(), indent=2))
conn.close()
