from sqlalchemy.orm import Session
from models import Lead, Message
from sqlalchemy import func

def calculate_lead_score(db: Session, lead: Lead) -> int:
    """
    Calcula o score de um lead (0-100) baseado em engajamento e dados coletados.
    
    Critérios:
    - Tem nome: +10
    - Tem email: +10
    - Temperatura quente: +30
    - Temperatura morna: +15
    - Valor estimado > 0: +20
    - Número de mensagens trocadas: +2 por mensagem (max 20)
    - Estágio avançado (reuniao/proposta): +10
    """
    score = 0
    
    if lead.name and lead.name != "Desconhecido":
        score += 10
    
    if lead.email:
        score += 10
        
    if lead.temperature == "quente":
        score += 30
    elif lead.temperature == "morno":
        score += 15
        
    if lead.estimated_value and lead.estimated_value > 0:
        score += 20
        
    # Mensagens
    msg_count = db.query(func.count(Message.id)).filter(Message.lead_id == lead.id).scalar() or 0
    score += min(msg_count * 2, 20)
    
    if lead.pipeline_stage in ["reuniao", "proposta"]:
        score += 10
        
    return min(score, 100)

def update_all_lead_scores(db: Session, tenant_id: str):
    leads = db.query(Lead).filter(Lead.tenant_id == tenant_id).all()
    for lead in leads:
        lead.score = calculate_lead_score(db, lead)
    db.commit()
