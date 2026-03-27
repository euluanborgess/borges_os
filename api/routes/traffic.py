import aiohttp
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
import urllib.parse
from pydantic import BaseModel
import requests
from core.config import settings
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc
from datetime import datetime, date, timedelta
from typing import List, Dict, Any

from core.database import get_db
from api.deps import get_current_user
from models.user import User
from models.lead import Lead
from models.ads import AdAccount, AdCampaign, AdMetric, AdStatus, AdPlatform
from models.tenant import Tenant

router = APIRouter(tags=["Traffic & Ads"])

@router.get("/dashboard-summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    period: str = Query("mensal", description="Período: mensal, semanal, hoje")
):
    """
    Retorna os grandes números do topo do Funil:
    Visitantes (Cliques FB/Google), Leads, Oportunidades, Vendas
    """
    # Determinando intervalo de tempo (mock simplificado)
    hoje = date.today()
    if period == "hoje":
        start_date = hoje
    elif period == "semanal":
        start_date = hoje - timedelta(days=7)
    else: # mensal
        start_date = hoje.replace(day=1)

    tenant_id = current_user.tenant_id

    # 1. Totalizadores CRM (Leads, Oportunidades, Vendas)
    stmt_leads = select(func.count(Lead.id)).where(
        Lead.tenant_id == tenant_id,
        func.date(Lead.created_at) >= start_date
    )
    result_leads = db.execute(stmt_leads)
    total_leads = result_leads.scalar() or 0

    total_oportunidades = int(total_leads * 0.3) if total_leads > 0 else 0
    total_vendas = int(total_oportunidades * 0.15) if total_oportunidades > 0 else 0

    # 2. Totalizadores de Ads (Cliques/Visitantes) puxados da Tabela AdMetric
    stmt_clicks = select(func.sum(AdMetric.clicks)).where(
        AdMetric.tenant_id == tenant_id,
        AdMetric.date >= start_date
    )
    result_clicks = db.execute(stmt_clicks)
    total_clicks = result_clicks.scalar() or 0

    return {
        "visitantes": total_clicks,
        "leads": total_leads,
        "oportunidades": total_oportunidades,
        "vendas": total_vendas
    }

@router.get("/campaigns-performance")
def get_campaigns_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna a lista de performance agrupada por Campanha
    """
    tenant_id = current_user.tenant_id
    
    start_date = date.today().replace(day=1)
    
    stmt = (
        select(
            AdCampaign.id,
            AdCampaign.name,
            AdAccount.platform,
            func.sum(AdMetric.clicks).label("total_clicks"),
            func.sum(AdMetric.spend).label("total_spend"),
            func.sum(AdMetric.leads_platform).label("total_leads_meta")
        )
        .join(AdAccount, AdCampaign.ad_account_id == AdAccount.id)
        .outerjoin(AdMetric, AdCampaign.id == AdMetric.ad_campaign_id)
        .where(
            AdCampaign.tenant_id == tenant_id,
            AdMetric.date >= start_date
        )
        .group_by(AdCampaign.id, AdCampaign.name, AdAccount.platform)
        .order_by(desc("total_clicks"))
    )
    
    result = db.execute(stmt)
    rows = result.all()
    
    campaigns = []
    for row in rows:
        crm_leads = row.total_leads_meta or 0 
        cpa = round(float((row.total_spend or 0) / crm_leads), 2) if crm_leads > 0 else 0
        conversion_rate = round(float((crm_leads / (row.total_clicks or 1)) * 100), 2)
        
        campaigns.append({
            "id": row.id,
            "name": row.name,
            "platform": row.platform.value if hasattr(row.platform, 'value') else str(row.platform),
            "spend": row.total_spend or 0,
            "clicks": row.total_clicks or 0,
            "leads": crm_leads,
            "cpa": cpa,
            "conversion_rate": conversion_rate
        })
        
    return {"campaigns": campaigns}

# ==========================================
# FASE 3: Integração OAuth com Meta Ads
# ==========================================

@router.get("/meta/login")
def meta_login(type: str = Query("ads"), current_user: User = Depends(get_current_user)):
    """
    Retorna a URL de autorização OAuth do Facebook para o frontend redirecionar.
    """
    app_id = getattr(settings, "META_APP_ID", "")
    if not app_id:
        return {"error": "META_APP_ID não configurado no servidor (.env)."}
        
    redirect_uri = f"{settings.PUBLIC_BASE_URL}/api/v1/traffic/meta/callback"
    state = f"tenant_{current_user.tenant_id}_{type}"
    
    # Adicionado pages_messaging e instagram_manage_comments para habilitar respostas e leitura de perfil no SaaS
    scope = "ads_read,instagram_manage_messages,instagram_manage_comments,pages_show_list,pages_read_engagement,pages_messaging"
    url = f"https://www.facebook.com/v19.0/dialog/oauth?client_id={app_id}&redirect_uri={urllib.parse.quote(redirect_uri)}&state={state}&scope={scope}"
    
    return {"url": url}

@router.get("/meta/callback")
def meta_callback(
    code: str = Query(None, description="Código de autorização retornado pela Meta"),
    state: str = Query(None, description="Payload de estado"),
    db: Session = Depends(get_db)
):
    if not code:
        from fastapi.responses import HTMLResponse
        return HTMLResponse("<script>alert('Código de autorização não fornecido pela Meta.'); window.close();</script>")
        
    app_id = getattr(settings, "META_APP_ID", "")
    app_secret = getattr(settings, "META_APP_SECRET", "")
    redirect_uri = f"{settings.PUBLIC_BASE_URL}/api/v1/traffic/meta/callback"
    
    # Real token exchange with Meta Graph API
    token_url = f"https://graph.facebook.com/v19.0/oauth/access_token?client_id={app_id}&redirect_uri={urllib.parse.quote(redirect_uri)}&client_secret={app_secret}&code={code}"
    
    print(f"[META CALLBACK DEV] Trocando code por token na Meta (App: {app_id})...")
    
    response = requests.get(token_url)
    if response.status_code != 200:
        err_msg = response.json()
        print(f"[META CALLBACK ERRO CRÍTICO] Falha ao trocar token: {err_msg}")
        from fastapi.responses import HTMLResponse
        return HTMLResponse(f"<script>alert('Erro ao trocar código pelo token: {err_msg}'); window.close();</script>")
        
    token_data = response.json()
    final_token = token_data.get("access_token")
    if not final_token:
        print("[META CALLBACK ERRO CRÍTICO] Token ausente na resposta 200!")
        from fastapi.responses import HTMLResponse
        return HTMLResponse("<script>alert('Token de acesso não recebido na resposta.'); window.close();</script>")
    
    print("[META CALLBACK DEV] Novo Token obtido com Sucesso. Extraindo estado...")
    
    # Extrair Tenant ID e Tipo
    if not state:
        print("[META CALLBACK ERRO CRÍTICO] State ausente!")
        return {"error": "State nao fornecido"}
        
    state_parts = state.replace("tenant_", "").split("_")
    tenant_id = state_parts[0] if len(state_parts) > 0 else None
    integration_type = state_parts[1] if len(state_parts) > 1 else "ads"
    
    if not tenant_id:
        return {"error": "Tenant ID nao identificado"}
        
    print(f"[META CALLBACK DEV] Procurando tenant {tenant_id}...")
        
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if tenant:
        # Fazer cópia profunda para SQLAlchemy reconhecer a mudança do JSON na hora de salvar
        integrations = dict(tenant.integrations) if tenant.integrations else {}
        
        # Buscar o ID da conta do Instagram atrelada a esta conta do Meta
        ig_business_id = None
        page_token = None
        page_id = None
        
        try:
            pages_res = requests.get(f"https://graph.facebook.com/v19.0/me/accounts?fields=id,name,access_token,instagram_business_account&access_token={final_token}")
            if pages_res.status_code == 200:
                for page in pages_res.json().get("data", []):
                    if "instagram_business_account" in page:
                        ig_business_id = page["instagram_business_account"].get("id")
                        page_token = page.get("access_token")
                        page_id = page.get("id")
                        break
        except Exception as e:
            print(f"Erro ao buscar IG ID e Page Token: {e}")
            
        with open("tmp/meta_token.txt", "w") as f:
            f.write(final_token)
        print(f"[META CALLBACK DEV] User Token GRAVADO no txt. Tamanho: {len(final_token)}")
            
        # Para instagram, salvar o Page Token para evitar Erro 403 (pages_messaging required)
        token_to_save = page_token if (integration_type == "insta" and page_token) else final_token
        
        if integration_type == "insta" and page_token and page_id:
            print(f"[META CALLBACK INSTA] Inscrevendo a Página {page_id} automaticamente nos Webhooks...")
            try:
                requests.post(f"https://graph.facebook.com/v19.0/{page_id}/subscribed_apps", params={
                    "subscribed_fields": "messages,messaging_postbacks,comments",
                    "access_token": page_token
                })
            except Exception as sub_err:
                print(f"[META CALLBACK INSTA] Falha na auto-inscrição: {sub_err}")

        integrations["instagram_connected"] = True
        integrations["instagram_token"] = token_to_save
        if ig_business_id:
            integrations["instagram_business_account_id"] = ig_business_id
            
        tenant.integrations = integrations
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(tenant, "integrations") # Força o update do JSON
        db.add(tenant)
        db.commit()
        print(f"[META CALLBACK DEV] Token {'SALVO' if tenant_id else 'IGNORADO'} no DB!")
    
    # Se for fluxo normal (Ads), criar fallback AdAccount PENDING
    pending_id = ""
    if integration_type != "insta":
        pending_account = AdAccount(
            tenant_id=tenant_id,
            platform=AdPlatform.meta_ads,
            account_id="pending_auth",
            name="Aguardando Selecao",
            access_token=final_token,
            status=AdStatus.PENDING
        )
        db.add(pending_account)
        db.commit()
        db.refresh(pending_account)
        pending_id = pending_account.id

    from fastapi.responses import HTMLResponse
    html_content = f"""
    <html>
    <body>
    <script>
        if (window.opener) {{
            window.opener.postMessage({{
                type: 'META_AUTH_SUCCESS',
                integration_type: '{integration_type}',
                pending_id: '{pending_id}',
                tenant_id: '{tenant_id}'
            }}, '*');
            // Timeout para dar chance ao postMessage de enviar antes de fechar violentamente
            setTimeout(() => window.close(), 500);
        }} else {{
            // Fallback se abriu na mesma janela
            window.location.href = "{settings.PUBLIC_BASE_URL}/?modal=select_ad_account&pending_id={pending_id}";
        }}
    </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
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
