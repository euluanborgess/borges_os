from core.database import SessionLocal
from models.task_event import Event
from models.user import User
from models.tenant import Tenant
from models.lead import Lead
from datetime import datetime, timedelta

db = SessionLocal()
tenant = db.query(Tenant).first()
if tenant:
    # Cria um lead
    lead = db.query(Lead).filter(Lead.tenant_id == tenant.id).first()
    if not lead:
        lead = Lead(tenant_id=tenant.id, name="Lead Teste CRM", whatsapp="5511999999999")
        db.add(lead)
        db.commit()
        db.refresh(lead)
        
    # Cria evento simulado The User wants
    event = Event(
        tenant_id=tenant.id,
        lead_id=lead.id,
        title="Reunião de Alinhamento AI",
        start_time=datetime.now() + timedelta(days=1),
        end_time=datetime.now() + timedelta(days=1, hours=1),
        status="scheduled",
        origin="Site",
        attendant="AI Sophia",
        observations="Resumo: O Lead quer implementar IA no suporte N1."
    )
    db.add(event)
    db.commit()
    print("Evento Injetado no BD com Sucesso!")
else:
    print("Nenhum Tenant encontrado.")
