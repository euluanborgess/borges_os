from datetime import date, timedelta
from sqlalchemy import select
from core.database import SessionLocal, engine
from models.base import Base # Garante que as tabelas sejam criadas se nâo estiverem
from models.tenant import Tenant
from models.ads import AdAccount, AdCampaign, AdMetric, AdPlatform, AdStatus
import models.ads

def run_seed():
    # Força a criação das tabelas caso o Uvicorn não tenha recarregado o Base
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Pega nosso tenant
        result = db.execute(select(Tenant))
        tenant = result.scalars().first()
        if not tenant:
            print("Nenhum tenant encontrado. Execute o sistema antes para criar.")
            return

        print(f"Semeando Ads no Tenant: {tenant.name}")

        # Cria ou Pega Conta de Anúncios Virtual
        result = db.execute(select(AdAccount).where(AdAccount.tenant_id == tenant.id))
        ad_account = result.scalars().first()
        if not ad_account:
            ad_account = AdAccount(
                tenant_id=tenant.id,
                platform=AdPlatform.meta_ads,
                account_id="act_123456789",
                name="Borges OS Business Manager",
                status=AdStatus.ACTIVE
            )
            db.add(ad_account)
            db.commit()
            print("Conta Meta Ads criada.")

        # Cria Campanhas
        result = db.execute(select(AdCampaign).where(AdCampaign.ad_account_id == ad_account.id))
        campaigns = result.scalars().all()
        if not campaigns:
            camp1 = AdCampaign(
                tenant_id=tenant.id,
                ad_account_id=ad_account.id,
                platform_campaign_id="c_101",
                name="Black Friday Oferta",
                budget_daily=50.0
            )
            camp2 = AdCampaign(
                tenant_id=tenant.id,
                ad_account_id=ad_account.id,
                platform_campaign_id="c_102",
                name="Converse Especialista",
                budget_daily=25.0
            )
            db.add_all([camp1, camp2])
            db.commit()
            campaigns = [camp1, camp2]
            print("2 Campanhas criadas.")

        # Cria Métricas Diárias para o mês atual
        hoje = date.today()
        start_date = hoje.replace(day=1)
        
        # Gera para camp1
        metrics_to_add = []
        for i in range((hoje - start_date).days + 1):
            dia_atual = start_date + timedelta(days=i)
            # Evita duplicidade se rodar mais de uma vez hoje
            existing = db.execute(select(AdMetric).where(AdMetric.tenant_id == tenant.id, AdMetric.date == dia_atual)).scalars().first()
            if existing: continue

            metrics_to_add.append(AdMetric(
                tenant_id=tenant.id,
                ad_campaign_id=campaigns[0].id,
                date=dia_atual,
                spend=18.5 + (i % 5),
                impressions=1200 + (i * 10),
                clicks=85 + (i * 2),
                leads_platform=10 + (i % 3)
            ))
            metrics_to_add.append(AdMetric(
                tenant_id=tenant.id,
                ad_campaign_id=campaigns[1].id,
                date=dia_atual,
                spend=9.2 + (i % 3),
                impressions=800 + (i * 5),
                clicks=40 + (i % 10),
                leads_platform=4 + (i % 2)
            ))
            
        if metrics_to_add:
            db.add_all(metrics_to_add)
            db.commit()
            print("Métricas do mês atual populadas com sucesso!")
        else:
            print("Nenhuma nova métrica populada.")
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()
