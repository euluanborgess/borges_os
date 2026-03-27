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
    from models.order import Order
    
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

    # 6. [ENTERPRISE] - Financeiro Real
    total_revenue = db.query(func.sum(Order.amount)).filter(
        Order.tenant_id == tenant_id,
        Order.status == "paid"
    ).scalar() or 0.0

    estimated_revenue = db.query(func.sum(Lead.estimated_value)).filter(
        Lead.tenant_id == tenant_id
    ).scalar() or 0.0

    total_leads = db.query(func.count(Lead.id)).filter(Lead.tenant_id == tenant_id).scalar() or 0
    hot_leads = db.query(func.count(Lead.id)).filter(Lead.tenant_id == tenant_id, Lead.temperature == "quente").scalar() or 0

    # 7. Últimas Atividades (Enterprise)
    from models.message import Message
    recent_messages = db.query(Message, Lead).join(Lead, Message.lead_id == Lead.id)\
        .filter(Lead.tenant_id == tenant_id)\
        .order_by(Message.created_at.desc())\
        .limit(5).all()
    
    activities = []
    for msg, lead in recent_messages:
        activities.append({
            "lead_name": lead.name or lead.phone,
            "content": msg.content[:50] + "..." if len(msg.content) > 50 else msg.content,
            "sender_type": msg.sender_type,
            "timestamp": msg.created_at.isoformat() if msg.created_at else None
        })

    return {
        "status": "success",
        "data": {
            "temperature_breakdown": temp_dict,
            "pipeline_breakdown": stage_dict,
            "total_events": total_events,
            "pending_activities": pending_tasks,
            "leads_waiting_human": waiting_human,
            "total_revenue": float(total_revenue),
            "estimated_revenue": float(estimated_revenue),
            "total_leads": total_leads,
            "hot_leads": hot_leads,
            "recent_activities": activities
        }
    }

@router.get("/leads/export")
def export_leads(format: str = "json", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Exporta a lista de leads do tenant para uso em campanhas de Ads ou CRM externo.
    """
    tenant_id = current_user.tenant_id
    leads = db.query(Lead).filter(Lead.tenant_id == tenant_id).all()
    
    data = []
    for l in leads:
        data.append({
            "name": l.name,
            "phone": l.phone,
            "email": l.email,
            "temperature": l.temperature,
            "score": l.score,
            "stage": l.pipeline_stage,
            "created_at": l.created_at.isoformat() if l.created_at else None
        })
        
    if format == "csv":
        import csv
        from io import StringIO
        from fastapi.responses import StreamingResponse
        
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=["name", "phone", "email", "temperature", "score", "stage", "created_at"])
        writer.writeheader()
        writer.writerows(data)
        output.seek(0)
        
        headers = {"Content-Disposition": f"attachment; filename=leads_export_{tenant_id}.csv"}
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers=headers)
        
    return {"status": "success", "data": data}
