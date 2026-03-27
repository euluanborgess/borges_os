"""Script to fix the corrupted line 150 in traffic.py"""
with open('api/routes/traffic.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_line = r"""    if not code:\n        return {\"error\": \"Acesso negado pelo usuário ou erro no OAuth do Facebook.\"}\n        \n    app_id = getattr(settings, \"META_APP_ID\", \"\")\n    app_secret = getattr(settings, \"META_APP_SECRET\", \"\")\n    redirect_uri = f\"{settings.PUBLIC_BASE_URL}/api/v1/traffic/meta/callback\"\n    \n    print(f\"[META CALLBACK] app_id={app_id}, redirect_uri={redirect_uri}\")\n    \n    # 1. Trocar código pelo Token de Acesso via POST (conforme documentação atual da Meta)\n    token_res = requests.post(\n        \"https://graph.facebook.com/v19.0/oauth/access_token\",\n        data={\n            \"client_id\": app_id,\n            \"client_secret\": app_secret,\n            \"redirect_uri\": redirect_uri,\n            \"code\": code,\n        }\n    )\n    print(f\"[META CALLBACK] token response: {token_res.status_code} {token_res.text}\")\n    if not token_res.ok:\n        return {\"error\": \"Falha ao obter token da Meta\", \"details\": token_res.json()}\n        \n    token_data = token_res.json()\n    short_token = token_data.get(\"access_token\")"""

new_block = """    if not code:
        return {"error": "Acesso negado pelo usuário ou erro no OAuth do Facebook."}
        
    app_id = getattr(settings, "META_APP_ID", "")
    app_secret = getattr(settings, "META_APP_SECRET", "")
    redirect_uri = f"{settings.PUBLIC_BASE_URL}/api/v1/traffic/meta/callback"
    
    print(f"[META CALLBACK] app_id={app_id}, redirect_uri={redirect_uri}, code_len={len(code) if code else 0}")
    
    # 1. Trocar código pelo Token via POST (documentação atual da Meta)
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

if old_line in content:
    content = content.replace(old_line, new_block)
    with open('api/routes/traffic.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed!")
else:
    print("Pattern not found, trying raw search...")
    # find the line
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if r'if not code:\\n' in line:
            print(f"Found at line {i+1}: {line[:100]}")
            lines[i] = new_block
            with open('api/routes/traffic.py', 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            print("Fixed by line replacement!")
            break
    else:
        print("Could not find pattern")
