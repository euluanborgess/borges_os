from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from models import Event, User, Lead
from api.deps import get_current_user
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class EventCreateInput(BaseModel):
    title: str
    start_time: str
    end_time: str
    origin: Optional[str] = "Portal CRM"
    observations: Optional[str] = None
    lead_id: Optional[str] = None

@router.get("/events")
def get_calendar_events(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenant_id = current_user.tenant_id
    events = db.query(Event).filter(Event.tenant_id == tenant_id).order_by(Event.start_time.asc()).all()
    
    results = []
    for e in events:
        lead = db.query(Lead).filter(Lead.id == e.lead_id).first()
        results.append({
            "id": e.id,
            "title": e.title,
            "start_time": e.start_time.isoformat(),
            "end_time": e.end_time.isoformat(),
            "origin": e.origin or "WhatsApp",
            "attendant": e.attendant or "Borges IA",
            "observations": e.observations,
            "lead": {
                "id": lead.id if lead else None,
                "name": lead.name if lead else "Lead não vinculado",
                "whatsapp": lead.phone if lead else "--"
            }
        })
    return {"status": "success", "events": results}

@router.post("/events")
def create_event(payload: EventCreateInput, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenant_id = current_user.tenant_id
    
    new_event = Event(
        tenant_id=tenant_id,
        title=payload.title,
        start_time=datetime.fromisoformat(payload.start_time.replace("Z", "+00:00")),
        end_time=datetime.fromisoformat(payload.end_time.replace("Z", "+00:00")),
        origin=payload.origin,
        observations=payload.observations,
        attendant=current_user.full_name,
        lead_id=payload.lead_id
    )
    
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return {"status": "success", "data": {"id": new_event.id}}

@router.put("/events/{event_id}")
def update_event(event_id: str, payload: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    event = db.query(Event).filter(Event.id == event_id, Event.tenant_id == current_user.tenant_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    
    if "title" in payload: event.title = payload["title"]
    if "start_time" in payload and payload["start_time"]: 
        event.start_time = datetime.fromisoformat(payload["start_time"].replace("Z", ""))
    if "end_time" in payload and payload["end_time"]: 
        event.end_time = datetime.fromisoformat(payload["end_time"].replace("Z", ""))
    if "observations" in payload: event.observations = payload["observations"]
    
    # [AUDIT] Registrar que o atendente humano alterou o evento
    event.attendant = current_user.full_name
    db.commit()
    return {"status": "success"}
