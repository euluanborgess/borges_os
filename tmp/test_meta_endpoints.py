"""
Testa o endpoint correto da Graph API para buscar perfil de usuários Instagram (PSID)
Conforme documentação oficial da Instagram Messaging API:
https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/get-started

Para obter info de um remetente, precisa:
1. Token da página (PAGE ACCESS TOKEN) com escopo instagram_manage_messages
2. Endpoint: GET /{instagram-user-id}?fields=name,profile_pic&access_token={PAGE_TOKEN}
   Mas o instagram-user-id aqui é o IGSID do remetente.

O IGSID é fornecido no payload do webhook como sender.id.
"""
import sys
import httpx
import asyncio
import hmac
import hashlib
sys.path.append('c:\\Users\\User\\Documents\\BorgesOS_Atualizado')

from core.database import SessionLocal
from models import Tenant

async def main():
    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.name.contains("Jack")).first()
        integ = tenant.integrations or {}
        token = integ.get("instagram_token")
        page_id = integ.get("instagram_business_account_id")
        
        # Calcular appsecret_proof
        app_secret = "b16ba38b8554c6208d5bbe77dd2f0382"
        h = hmac.new(app_secret.encode(), token.encode(), hashlib.sha256)
        appsecret_proof = h.hexdigest()
        
        print(f"Page ID: {page_id}")
        
        async with httpx.AsyncClient() as client:
            # 1. Verificar o que o token pode acessar
            print("\n1. Verificando conta Instagram conectada...")
            me_url = f"https://graph.facebook.com/v19.0/me?fields=id,name,instagram_business_account&access_token={token}"
            r = await client.get(me_url, timeout=10)
            print(f"  Status: {r.status_code}")
            print(f"  Resp: {r.text[:500]}")
            
            # 2. Tentar buscar a página de Instagram conectada
            print("\n2. Buscando páginas...")
            pages_url = f"https://graph.facebook.com/v19.0/me/accounts?access_token={token}"
            r2 = await client.get(pages_url, timeout=10)
            print(f"  Status: {r2.status_code}")
            print(f"  Resp: {r2.text[:1000]}")
            
            # 3. Verificar se o page token é USER ou PAGE token
            print("\n3. Verificando tipo do token...")
            debug_url = f"https://graph.facebook.com/debug_token?input_token={token}&access_token={token}"
            r3 = await client.get(debug_url, timeout=10)
            data3 = r3.json().get("data", {})
            print(f"  Tipo: {data3.get('type')} | Expira: {data3.get('expires_at')} | Scopes: {data3.get('scopes')}")
            
    finally:
        db.close()

asyncio.run(main())
