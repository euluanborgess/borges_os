"""
Testa busca de perfil pelos IDs reais dos leads do Instagram
"""
import sys
import httpx
import asyncio
sys.path.append('c:\\Users\\User\\Documents\\BorgesOS_Atualizado')

from core.database import SessionLocal
from models import Tenant, Lead

REAL_SENDER_IDS = ["6741197482560089", "2158921044911270"]

async def main():
    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.name.contains("Jack")).first()
        integ = tenant.integrations or {}
        token = integ.get("instagram_token")
        page_id = integ.get("instagram_business_account_id")  # 17841455926157544
        
        print(f"Token: {token[:30]}...")
        print(f"Page ID: {page_id}")
        
        async with httpx.AsyncClient() as client:
            for sid in REAL_SENDER_IDS:
                print(f"\n--- Testando sender_id: {sid} ---")
                
                # Método 1: Direto (funciona para PSIDs do Messenger/Instagram)
                url1 = f"https://graph.facebook.com/v19.0/{sid}?fields=name,profile_pic&access_token={token}"
                r1 = await client.get(url1, timeout=10)
                print(f"Método 1 (direto): {r1.status_code} -> {r1.text[:200]}")
                
                # Método 2: Via recipient (para Instagram Business)  
                url2 = f"https://graph.facebook.com/v19.0/{page_id}/messages?fields=from&access_token={token}"
                # Isso lista conversas, não um user específico - só para verificar acesso
                
                # Método 3: User info via Instagram API
                url3 = f"https://graph.facebook.com/v19.0/{sid}?fields=id,name&access_token={token}&appsecret_proof="
                r3 = await client.get(url3, timeout=10)
                print(f"Método 3: {r3.status_code} -> {r3.text[:200]}")
                
    finally:
        db.close()

asyncio.run(main())
