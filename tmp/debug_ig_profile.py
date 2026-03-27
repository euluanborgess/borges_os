"""
Diagnóstico completo da integração Instagram - nome e foto
"""
import sys
import httpx
import asyncio
sys.path.append('c:\\Users\\User\\Documents\\BorgesOS_Atualizado')

from core.database import SessionLocal
from models import Tenant, Lead

async def main():
    db = SessionLocal()
    try:
        # 1. Verificar o token do Instagram
        tenant = db.query(Tenant).filter(Tenant.name.contains("Jack")).first()
        if not tenant:
            print("Tenant não encontrado!")
            return
        
        integ = tenant.integrations or {}
        token = integ.get("instagram_token")
        account_id = integ.get("instagram_business_account_id")
        
        print(f"Tenant: {tenant.name}")
        print(f"Account ID: {account_id}")
        print(f"Token: {'Presente (' + token[:20] + '...)' if token else 'AUSENTE!'}")
        
        # 2. Buscar leads do Instagram
        leads = db.query(Lead).filter(Lead.channel == "instagram").all()
        print(f"\nLeads Instagram encontrados: {len(leads)}")
        for l in leads:
            print(f"  - {l.name} | phone={l.phone} | profile_data={l.profile_data}")
        
        if not token:
            print("\n❌ Sem token! Impossível buscar perfil.")
            return
        
        # 3. Testar a Token com a Graph API
        print("\nTestando token com Graph API...")
        async with httpx.AsyncClient() as client:
            # Verificar validade do token
            debug_url = f"https://graph.facebook.com/debug_token?input_token={token}&access_token={token}"
            resp = await client.get(debug_url, timeout=10)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                d = resp.json().get("data", {})
                print(f"  Token válido: {d.get('is_valid')}")
                print(f"  Tipo: {d.get('type')}")
                print(f"  Expira em: {d.get('expires_at', 'nunca')}")
                print(f"  Scopes: {d.get('scopes', [])}")
            else:
                print(f"  Erro: {resp.text[:500]}")
            
            # 4. Testar busca de perfil de um sender real
            if leads:
                # Pegar o sender_id do phone do lead (formato ig_SENDERID)
                sample_lead = leads[0]
                sender_id = sample_lead.phone.replace("ig_", "")
                print(f"\nTestando busca de perfil para sender_id: {sender_id}")
                
                profile_url = f"https://graph.facebook.com/v19.0/{sender_id}?fields=name,profile_pic&access_token={token}"
                presp = await client.get(profile_url, timeout=10)
                print(f"Status: {presp.status_code}")
                print(f"Resposta: {presp.text[:500]}")
    finally:
        db.close()

asyncio.run(main())
