from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from models.task_event import Event
from models.user import User
from models.lead import Lead
from api.deps import get_current_user
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class EventUpdateInput(BaseModel):
    title: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = None
    meeting_link: Optional[str] = None
    origin: Optional[str] = None
    attendant: Optional[str] = None
    observations: Optional[str] = None

@router.get("/events")
def list_events(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Lista todos os eventos agendados de um Tenant, com dados do Lead acoplados (Visão do Dashboard).
    """
    tenant_id = current_user.tenant_id
    
    # Realiza um Join com Lead para pegar o nome e whatsapp no grid do Frontend
    query = db.query(Event, Lead).outerjoin(Lead, Event.lead_id == Lead.id)\
              .filter(Event.tenant_id == tenant_id)\
              .order_by(Event.start_time.asc()).all()
              
    results = []
    for event, lead in query:
        results.append({
            "id": event.id,
            "title": event.title,
            "start_time": event.start_time.isoformat() if event.start_time else None,
            "end_time": event.end_time.isoformat() if event.end_time else None,
            "status": event.status,
            "meeting_link": event.meeting_link,
            "origin": event.origin,
            "attendant": event.attendant,
            "observations": event.observations,
            "created_at": event.created_at.isoformat() if event.created_at else None,
            "lead": {
                "id": lead.id if lead else None,
                "name": lead.name if lead else "Leads Órfãos/Manual",
                "whatsapp": lead.phone if lead else ""
            }
        })
        
    return {"status": "success", "data": results}

class EventCreateInput(BaseModel):
    lead_id: str
    title: str
    start_time: datetime
    end_time: datetime

@router.post("/events")
def create_event(payload: EventCreateInput, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Cria manualmente ou via Painel um evento para um cliente.
    A IA também pode ter acesso a essa rota via Actions no futuro.
    """
    tenant_id = current_user.tenant_id
    new_event = Event(
        tenant_id=tenant_id,
        lead_id=payload.lead_id,
        title=payload.title,
        start_time=payload.start_time,
        end_time=payload.end_time
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    return {
        "status": "success",
        "data": {
            "id": new_event.id,
            "title": new_event.title,
            "start_time": new_event.start_time.isoformat() if new_event.start_time else None,
            "end_time": new_event.end_time.isoformat() if new_event.end_time else None,
        }
    }

@router.delete("/events/{event_id}")
def delete_event(event_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenant_id = current_user.tenant_id
    event = db.query(Event).filter(Event.id == event_id, Event.tenant_id == tenant_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado.")
    db.delete(event)
    db.commit()
    return {"status": "success"}


@router.put("/events/{event_id}")
def update_event(
    event_id: str, 
    payload: EventUpdateInput, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Atualiza um evento existente. Usado no Modal CRM de Agendamentos.
    """
    tenant_id = current_user.tenant_id
    event = db.query(Event).filter(Event.id == event_id, Event.tenant_id == tenant_id).first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado.")
        
    if payload.title is not None: event.title = payload.title
    if payload.start_time is not None: event.start_time = payload.start_time
    if payload.end_time is not None: event.end_time = payload.end_time
    if payload.status is not None: event.status = payload.status
    if payload.meeting_link is not None: event.meeting_link = payload.meeting_link
    if payload.origin is not None: event.origin = payload.origin
    if payload.attendant is not None: event.attendant = payload.attendant
    if payload.observations is not None: event.observations = payload.observations
    
    db.commit()
    db.refresh(event)
    
    return {"status": "success", "data": {"id": event.id}}
