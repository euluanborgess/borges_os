import sys
import os
import requests
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Adiciona o diretório raiz ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal
from models.ads import AdAccount, AdCampaign, AdMetric, AdStatus, AdPlatform

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AdsSyncWorker")

META_GRAPH_URL = "https://graph.facebook.com/v19.0"

def sync_meta_ad_accounts():
    """
    Função principal do Worker.
    Varre todas as contas ativas de Meta Ads no banco e puxa Campanhas e Métricas diárias.
    """
    logger.info("Iniciando rotina de sincronização de Meta Ads...")
    db = SessionLocal()
    try:
        active_accounts = db.query(AdAccount).filter(
            AdAccount.platform == AdPlatform.meta_ads,
            AdAccount.status == AdStatus.ACTIVE
        ).all()
        
        logger.info(f"Encontradas {len(active_accounts)} contas da Meta ativas para sincronizar.")
        
        for account in active_accounts:
            try:
                logger.info(f"Sincronizando AdAccount: {account.name} ({account.account_id}) - Tenant: {account.tenant_id}")
                sync_meta_campaigns(db, account)
                sync_meta_insights(db, account)
                
                # Atualizando a data de última sincronização
                account.last_sync_at = datetime.utcnow()
                db.commit()
            except Exception as e:
                logger.error(f"Erro ao sincronizar conta {account.account_id}: {e}")
                db.rollback()
                
    except Exception as e:
        logger.error(f"Erro fatal no worker de Ads: {e}")
    finally:
        db.close()
        logger.info("Rotina de sincronização de Meta Ads finalizada.")

def sync_meta_campaigns(db, account: AdAccount):
    """
    Puxa a lista de campanhas da conta de anúncios.
    """
    url = f"{META_GRAPH_URL}/{account.account_id}/campaigns?fields=id,name,status,daily_budget&limit=200&access_token={account.access_token}"
    res = requests.get(url)
    if not res.ok:
        raise Exception(f"Falha ao buscar campanhas: {res.text}")
        
    data = res.json().get("data", [])
    
    for camp_data in data:
        camp_id = camp_data.get("id")
        
        campaign = db.query(AdCampaign).filter(AdCampaign.platform_campaign_id == camp_id, AdCampaign.tenant_id == account.tenant_id).first()
        if not campaign:
            campaign = AdCampaign(
                tenant_id=account.tenant_id,
                ad_account_id=account.id,
                platform_campaign_id=camp_id,
            )
            db.add(campaign)
            
        campaign.name = camp_data.get("name", "Campanha Sem Nome")
        
        # Mapeamento do status da Meta
        api_status = camp_data.get("status", "ACTIVE")
        if api_status in ["ACTIVE", "IN_PROCESS"]:    
            campaign.status = AdStatus.ACTIVE
        elif api_status in ["PAUSED", "ARCHIVED", "DELETED"]:
            campaign.status = AdStatus.PAUSED
        else:
            campaign.status = AdStatus.ERROR
            
        # Meta retorna orçamento em centavos ou similar, convertido para R$
        daily_budget = camp_data.get("daily_budget", 0)
        if daily_budget:
            campaign.budget_daily = float(daily_budget) / 100.0
            
    db.commit()
    logger.info(f"    - {len(data)} campanhas sincronizadas.")

def sync_meta_insights(db, account: AdAccount):
    """
    Puxa as métricas de performance agrupadas por campanha e por dia (últimos 7 dias).
    """
    # Exemplo: Puxar últimos 7 dias para garantir atualizações retroativas e faturamento atrasado
    url = f"{META_GRAPH_URL}/{account.account_id}/insights?level=campaign&date_preset=last_7d&time_increment=1&fields=campaign_id,spend,impressions,clicks&limit=500&access_token={account.access_token}"
    
    res = requests.get(url)
    if not res.ok:
        raise Exception(f"Falha ao buscar insights: {res.text}")
        
    data = res.json().get("data", [])
    metrics_saved = 0
    
    for row in data:
        camp_id = row.get("campaign_id")
        date_start = row.get("date_start") # string YYYY-MM-DD
        
        if not camp_id or not date_start:
            continue
            
        # Pega a campanha do banco local
        campaign = db.query(AdCampaign).filter(AdCampaign.platform_campaign_id == camp_id, AdCampaign.tenant_id == account.tenant_id).first()
        if not campaign:
            continue # Se a campanha não foi puxada antes por algum motivo, pula
            
        date_obj = datetime.strptime(date_start, "%Y-%m-%d").date()
        
        metric = db.query(AdMetric).filter(
            AdMetric.ad_campaign_id == campaign.id,
            AdMetric.date == date_obj
        ).first()
        
        if not metric:
            metric = AdMetric(
                tenant_id=account.tenant_id,
                ad_campaign_id=campaign.id,
                date=date_obj
            )
            db.add(metric)
            
        metric.spend = float(row.get("spend", 0.0))
        metric.impressions = int(row.get("impressions", 0))
        metric.clicks = int(row.get("clicks", 0))
        
        metrics_saved += 1
        
    db.commit()
    logger.info(f"    - {metrics_saved} métricas diárias atualizadas.")

if __name__ == "__main__":
    logger.info("Execução Manual do Worker: Sincronização de Ads")
    sync_meta_ad_accounts()
