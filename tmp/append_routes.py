import aiohttp
from fastapi import HTTPException

# Rotas restauradas
@router.get("/meta/adaccounts/{pending_id}")
async def get_meta_adaccounts(
    pending_id: str,
    db: Session = Depends(get_db)
):
    """
    Lista as contas de anúncio disponíveis na Meta usando o token recém-autorizado (PENDING).
    Não exige JWT (current_user) porque o pending_id (UUID) age como token de segurança temporário
    após o redirecionamento OAuth cross-domain.
    """
    account = db.query(AdAccount).filter(AdAccount.id == pending_id, AdAccount.status == AdStatus.PENDING).first()
    if not account:
        raise HTTPException(status_code=404, detail="Conta pendente não encontrada ou já ativada.")
        
    # Buscar contas no Graph API da Meta
    url = f"https://graph.facebook.com/v19.0/me/adaccounts?fields=name,account_id,account_status&access_token={account.access_token}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                error_data = await response.json()
                raise HTTPException(status_code=400, detail=f"Erro na Meta: {error_data}")
            data = await response.json()
            
    return {"ad_accounts": data.get("data", [])}

@router.post("/meta/adaccounts/{pending_id}/select")
def select_meta_adaccount(
    pending_id: str,
    account_data: dict,
    db: Session = Depends(get_db)
):
    """
    Confirma a conta de anúncios selecionada e ativa a integração.
    """
    account = db.query(AdAccount).filter(AdAccount.id == pending_id, AdAccount.status == AdStatus.PENDING).first()
    if not account:
        raise HTTPException(status_code=404, detail="Conta pendente não encontrada.")
        
    selected_id = account_data.get("account_id")
    selected_name = account_data.get("name")
    
    if not selected_id:
        raise HTTPException(status_code=400, detail="account_id não fornecido")
        
    # Se account_id não começar com act_, adiciona
    if not selected_id.startswith("act_"):
        selected_id = f"act_{selected_id}"
        
    # Atualiza a conta genérica PENDING com os dados reais selecionados
    account.account_id = selected_id
    account.name = selected_name or "Minha Conta de Anúncios"
    account.status = AdStatus.ACTIVE
    
    # Busca tenant para atualizar status
    tenant = db.query(Tenant).filter(Tenant.id == account.tenant_id).first()
    if tenant:
        integrations = tenant.integrations or {}
        integrations["meta_ads_connected"] = True
        tenant.integrations = integrations
        db.add(tenant)
        
    db.commit()
    return {"success": True, "message": "Conta ativada com sucesso!"}
