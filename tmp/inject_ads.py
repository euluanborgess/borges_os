import asyncio
from core.database import async_session_factory
from models.lead import Lead
from sqlalchemy import select

async def inject_ad_data():
    async with async_session_factory() as session:
        # Pega nosso lead chamado 'Ad Source'
        stmt = select(Lead).where(Lead.name == 'Ad Source')
        result = await session.execute(stmt)
        lead = result.scalars().first()
        if lead:
            lead.ad_source = 'instagram'
            lead.ad_campaign_name = 'Campanha Vendas Black Friday 2026'
            # Fake Ad Creative Image
            lead.ad_creative_url = 'https://images.unsplash.com/photo-1611162617474-5b21e879e113?q=80&w=150&auto=format&fit=crop'
            await session.commit()
            print("Dados Meta Ads (com miniatura) injetados com sucesso!")
        else:
            print("Lead 'Ad Source' não encontrado.")

if __name__ == "__main__":
    asyncio.run(inject_ad_data())
