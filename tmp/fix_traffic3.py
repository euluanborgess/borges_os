"""Fix the corrupted meta_callback function - the file has literal \\n bytes"""

new_block = b"""    if not code:
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

start = content.find(b'if not code:\\n')
print(f"Found at: {start}")

if start != -1:
    # Find the end: the next real line which starts with \r\n    \r\n    # 2.
    end = content.find(b'# 2.', start)
    # Go back to find the preceding \r\n    \r\n
    end = content.rfind(b'\r\n', start, end) 
    end2 = content.rfind(b'\r\n', start, end)
    print(f"End at: {end2}")
    
    new_content = content[:start] + new_block + b'\r\n' + content[end:]
    open('api/routes/traffic.py', 'wb').write(new_content)
    print("Fixed!")
else:
    print("Pattern not found, checking what's there...")
    idx = content.find(b'if not code:')
    print(repr(content[idx:idx+30]))
