from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from models import Message, Lead, Tenant, AuditLog, User
from sqlalchemy import func
import os

router = APIRouter()

@router.get("/audit")
def get_audit_logs(db: Session = Depends(get_db)):
    """
    Retorna os logs de auditoria do sistema.
    """
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(50).all()
    results = []
    for l in logs:
        u = db.query(User).filter(User.id == l.user_id).first()
        results.append({
            "timestamp": l.created_at.isoformat(),
            "user": u.full_name if u else "Sistema/IA",
            "action": l.action,
            "target": f"{l.target_type} ({l.target_id})",
            "details": l.details
        })
    return {"status": "success", "data": results}

@router.get("/status")
def get_agent_status(db: Session = Depends(get_db)):
    """
    Retorna o status atual do agente e histórico de atividades.
    """
    # 1. Atividade Recente (Últimas 10 mensagens do sistema/IA)
    recent_activities = db.query(Message).order_by(Message.created_at.desc()).limit(15).all()
    
    history = []
    for m in recent_activities:
        history.append({
            "timestamp": m.created_at.isoformat() if m.created_at else None,
            "type": m.sender_type,
            "content": m.content,
            "has_media": True if m.media_url else False,
            "lead_id": m.lead_id
        })

    # 2. Métricas de Operação
    total_leads = db.query(Lead).count()
    ai_responses = db.query(Message).filter(Message.sender_type == "ai").count()
    media_processed = db.query(Message).filter(Message.media_url != None).count()

    # 3. Status de Serviços (Simulado baseado em processos)
    # Em produção isso checaria Redis/Celery
    services = {
        "api": "online",
        "whatsapp_polling": "active",
        "ai_vision": "enabled",
        "ai_whisper": "enabled"
    }

    return {
        "status": "success",
        "current_task": "Monitorando leads e processando mídias multimodais",
        "metrics": {
            "total_leads": total_leads,
            "ai_responses": ai_responses,
            "media_processed": media_processed
        },
        "services": services,
        "history": history
    }
