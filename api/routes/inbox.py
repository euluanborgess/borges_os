from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import asyncio
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from core.database import get_db
from models import Lead, Message, User, Tenant
from services.websocket_manager import manager
from api.deps import get_current_user
from jose import jwt, JWTError
from core.security import SECRET_KEY, ALGORITHM

router = APIRouter()

@router.get("/leads")
def get_leads(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Retorna a lista de Leads do tenant (ordenados por recência).
    """
    tenant_id = current_user.tenant_id
    from sqlalchemy import func as sqlfunc
    leads = db.query(Lead).filter(Lead.tenant_id == tenant_id).order_by(
        sqlfunc.coalesce(Lead.updated_at, Lead.created_at).desc()
    ).all()
    
    results = []
    for l in leads:
        last_msg = db.query(Message).filter(Message.lead_id == l.id).order_by(Message.created_at.desc()).first()
        
        pdata = l.profile_data if isinstance(l.profile_data, dict) and l.profile_data else None
        ts = l.updated_at or l.created_at
        
        results.append({
            "id": l.id,
            "phone": l.phone,
            "name": l.name,
            "pipeline_stage": l.pipeline_stage or "lead",
            "temperature": l.temperature or "frio",
            "score": l.score or 0,
            "channel": l.channel or "whatsapp",
            "unread_count": l.unread_count or 0,
            "is_paused_for_human": l.is_paused_for_human or 0,
            "last_message": last_msg.content if last_msg else "Conversa iniciada",
            "last_message_at": last_msg.created_at.isoformat() if last_msg and last_msg.created_at else None,
            "last_message_media_type": last_msg.media_type if last_msg else None,
            "profile_data": pdata,
            "updated_at": ts.isoformat() if ts else None
        })
    return {"status": "success", "data": results}


@router.get("/messages/{lead_id}")
def get_messages(lead_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Retorna o histórico de mensagens de um lead específico, incluindo mídia.
    """
    tenant_id = current_user.tenant_id
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.tenant_id == tenant_id).first()
    if not lead:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Lead not found or does not belong to tenant")

    msgs = db.query(Message).filter(Message.lead_id == lead_id).order_by(Message.created_at.asc()).all()
    results = []
    for m in msgs:
        results.append({
            "id": m.id,
            "sender_type": m.sender_type,
            "content": m.content,
            "media_url": m.media_url,
            "media_type": m.media_type,
            "created_at": m.created_at.isoformat() if m.created_at else None
        })
    return {"status": "success", "data": results}


class LeadUpdateInput(BaseModel):
    pipeline_stage: Optional[str] = None
    temperature: Optional[str] = None
    score: Optional[int] = None
    tags: Optional[list[str]] = None

@router.put("/leads/{lead_id}")
def update_lead(lead_id: str, payload: LeadUpdateInput, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenant_id = current_user.tenant_id
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.tenant_id == tenant_id).first()
    if not lead:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Lead not found")

    if payload.pipeline_stage is not None:
        lead.pipeline_stage = payload.pipeline_stage
    if payload.temperature is not None:
        lead.temperature = payload.temperature
    if payload.score is not None:
        lead.score = payload.score
    if payload.tags is not None:
        lead.tags = payload.tags

    db.commit()
    return {"status": "success"}


@router.post("/leads/{lead_id}/read")
def mark_lead_read(lead_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Zera o unread_count do lead quando o atendente abre a conversa.
    """
    tenant_id = current_user.tenant_id
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.tenant_id == tenant_id).first()
    if not lead:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead.unread_count = 0
    db.commit()
    return {"status": "success"}


@router.get("/leads/{lead_id}/media")
def get_lead_media(lead_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Retorna todas as mídias (imagens, áudios, documentos) de um lead.
    """
    tenant_id = current_user.tenant_id
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.tenant_id == tenant_id).first()
    if not lead:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Lead not found")
    
    medias = db.query(Message).filter(
        Message.lead_id == lead_id,
        Message.media_type != None
    ).order_by(Message.created_at.desc()).all()
    
    results = {
        "images": [],
        "audios": [],
        "documents": [],
        "videos": []
    }
    
    for m in medias:
        entry = {
            "id": m.id,
            "media_url": m.media_url,
            "media_type": m.media_type,
            "content": m.content,
            "created_at": m.created_at.isoformat() if m.created_at else None
        }
        if m.media_type in ("image", "sticker"):
            results["images"].append(entry)
        elif m.media_type == "audio":
            results["audios"].append(entry)
        elif m.media_type == "document":
            results["documents"].append(entry)
        elif m.media_type == "video":
            results["videos"].append(entry)
    
    return {"status": "success", "data": results}


@router.websocket("/stream")
async def inbox_websocket(websocket: WebSocket, token: str):
    """
    WebSocket para comunicação em tempo real do Inbox.
    """
    await websocket.accept()
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        tenant_id = payload.get("tenant_id")
        if not tenant_id:
            await websocket.close(code=1008)
            return
    except JWTError:
        await websocket.close(code=1008)
        return
        
    await manager.connect(websocket, tenant_id)
    from core.database import SessionLocal
    
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("action") == "send_message":
                lead_id = data.get("lead_id")
                content = (data.get("content") or "").strip()
                if not lead_id or not content:
                    continue

                db = SessionLocal()
                try:
                    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.tenant_id == tenant_id).first()
                    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
                    if not lead or not tenant:
                        continue

                    # Save message in DB
                    new_msg = Message(
                        tenant_id=tenant_id,
                        lead_id=lead_id,
                        sender_type="human",
                        content=content,
                    )
                    db.add(new_msg)
                    db.commit()

                    # Send to WhatsApp (best-effort)
                    try:
                        from services.evolution_sender import send_whatsapp_message
                        integ = tenant.integrations or {}
                        evt_url = integ.get("evolution_api_url")
                        evt_key = integ.get("evolution_api_key")
                        # Evolution accepts plain numbers; keep it consistent with stored lead.phone
                        asyncio.create_task(
                            send_whatsapp_message(
                                tenant.evolution_instance_id,
                                lead.phone,
                                content,
                                evolution_url=evt_url,
                                evolution_api_key=evt_key,
                            )
                        )
                    except Exception as e:
                        print(f"[Inbox] Falha ao enviar via Evolution: {e}")

                finally:
                    db.close()

                await manager.broadcast_to_tenant(tenant_id, {
                    "type": "inbox_update",
                    "lead_id": lead_id,
                    "message": {
                        "sender_type": "human",
                        "content": content,
                        "media_url": None,
                        "media_type": None
                    }
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, tenant_id)
