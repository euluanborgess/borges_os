from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from api.deps import get_current_user
from models import User, Tenant, Lead, Message
from pydantic import BaseModel

router = APIRouter()


@router.post("/sync")
async def sync_instagram(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Ponto de sincronização do Instagram (agora gerenciado via webhook nativo da Meta).
    """
    return {"status": "success", "message": "Instagram usa webhook nativo - sem sincronizacao manual necessaria"}


@router.get("/ai-suggestion/{lead_id}")
async def get_ai_suggestion(lead_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Retorna sugestão de IA para um lead Instagram.
    """
    tenant_id = current_user.tenant_id
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.tenant_id == tenant_id).first()
    if not lead or lead.channel != "instagram":
        raise HTTPException(status_code=404, detail="Lead not found or not an Instagram lead")
    return {"status": "success", "suggestion": "Use o endpoint /api/v1/ai/suggest para sugestoes de IA"}


class SendMessageInput(BaseModel):
    content: str


@router.post("/send/{lead_id}")
async def send_instagram_message(
    lead_id: str,
    payload: SendMessageInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Envia mensagem via Evolution API para um lead Instagram.
    """
    import httpx
    import os
    tenant_id = current_user.tenant_id
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.tenant_id == tenant_id).first()
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    if not lead or lead.channel != "instagram":
        raise HTTPException(status_code=404, detail="Lead not found")

    integ = tenant.integrations or {}
    ev_url = (integ.get("evolution_api_url") or os.getenv("EVOLUTION_API_URL", "")).rstrip("/")
    ev_key = integ.get("evolution_api_key") or os.getenv("EVOLUTION_API_KEY", "")
    instance = tenant.evolution_instance_id

    if not ev_url or not instance:
        raise HTTPException(status_code=500, detail="Evolution API not configured")

    # Enviar via Evolution
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{ev_url}/message/sendText/{instance}",
            headers={"apikey": ev_key, "Content-Type": "application/json"},
            json={"number": lead.phone, "text": payload.content},
            timeout=10.0
        )
    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=500, detail=f"Evolution error: {resp.text[:200]}")

    new_msg = Message(
        tenant_id=tenant_id,
        lead_id=lead.id,
        sender_type="human",
        content=payload.content
    )
    db.add(new_msg)
    db.commit()
    return {"status": "success"}

