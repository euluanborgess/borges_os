"""Fix the corrupted meta_callback function in traffic.py"""

NEW_BLOCK = b"""    if not code:
        return {"error": "Acesso negado pelo usuario ou erro no OAuth do Facebook."}
        
    app_id = getattr(settings, "META_APP_ID", "")
    app_secret = getattr(settings, "META_APP_SECRET", "")
    redirect_uri = f"{settings.PUBLIC_BASE_URL}/api/v1/traffic/meta/callback"
    
    print(f"[META CALLBACK] app_id={app_id}, redirect_uri={redirect_uri}")
    
    # 1. Trocar codigo pelo Token via POST (documentacao atual da Meta)
    token_res = requests.post(
        "https://graph.facebook.com/v19.0/oauth/access_token",
        data={
            "client_id": app_id,
            "client_secret": app_secret,
            "redirect_uri": redirect_uri,
            "code": code,
        }
    )
    print(f"[META CALLBACK] token_status={token_res.status_code}, response={token_res.text[:300]}")
    if not token_res.ok:
        return {"error": "Falha ao obter token da Meta", "details": token_res.json()}
        
    token_data = token_res.json()
    short_token = token_data.get("access_token")"""

content = open('api/routes/traffic.py', 'rb').read()

# Find the corrupted block start
start = content.find(b'    if not code:\\\\n')
end = content.find(b'\r\n    \r\n    # 2.', start)
if end == -1:
    end = content.find(b'\n    \n    # 2.', start)

if start == -1:
    print("Could not find corrupted block!")
else:
    print(f"Found corrupted block from {start} to {end}")
    # Replace
    new_content = content[:start] + NEW_BLOCK + content[end:]
    open('api/routes/traffic.py', 'wb').write(new_content)
    print("Fixed!")
    
    # Verify
    verify = open('api/routes/traffic.py', 'r', encoding='utf-8').read()
    if 'token_res = requests.post' in verify:
        print("Verification OK: POST method found")
    else:
        print("WARNING: POST method not found in file!")
