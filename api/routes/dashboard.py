from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from core.database import get_db
from models import Lead, Event, Task, User
from api.deps import get_current_user

router = APIRouter()

@router.get("/metrics")
def get_dashboard_metrics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Agrega as principais métricas para o Painel Gerencial do BORGES OS.
    """
    tenant_id = current_user.tenant_id
    
    # 1. Leads por Temperatura
    leads_by_temp = db.query(
        Lead.temperature, 
        func.count(Lead.id)
    ).filter(Lead.tenant_id == tenant_id).group_by(Lead.temperature).all()
    
    temp_dict = {t: count for t, count in leads_by_temp}

    # 2. Leads por Estágio do Pipeline
    leads_by_stage = db.query(
        Lead.pipeline_stage, 
        func.count(Lead.id)
    ).filter(Lead.tenant_id == tenant_id).group_by(Lead.pipeline_stage).all()
    
    stage_dict = {s: count for s, count in leads_by_stage}
    
    # 3. Total de Agendamentos (Eventos)
    total_events = db.query(func.count(Event.id)).filter(Event.tenant_id == tenant_id).scalar()
    
    # 4. Total de Tarefas Pendentes
    pending_tasks = db.query(func.count(Task.id)).filter(
        Task.tenant_id == tenant_id, 
        Task.is_completed == False
    ).scalar()
    
    # 5. Leads esperando Handoff (Humano)
    waiting_human = db.query(func.count(Lead.id)).filter(
        Lead.tenant_id == tenant_id,
        Lead.is_paused_for_human == 1
    ).scalar()

    return {
        "status": "success",
        "data": {
            "temperature_breakdown": temp_dict,
            "pipeline_breakdown": stage_dict,
            "total_events": total_events,
            "pending_activities": pending_tasks,
            "leads_waiting_human": waiting_human
        }
    }
