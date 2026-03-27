from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, UploadFile, File, HTTPException
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
    from models.order import Order
    from sqlalchemy import func as sqlfunc
    
    for l in leads:
        last_msg = db.query(Message).filter(Message.lead_id == l.id).order_by(Message.created_at.desc()).first()
        
        # [ENTERPRISE FIX] - LTV & Ultima Compra
        ltv = db.query(sqlfunc.sum(Order.amount)).filter(Order.lead_id == l.id, Order.status == "paid").scalar() or 0
        last_order = db.query(Order).filter(Order.lead_id == l.id).order_by(Order.created_at.desc()).first()
        
        assigned_user_name = None
        if l.assigned_user_id:
            assigned_user = db.query(User).filter(User.id == l.assigned_user_id).first()
            if assigned_user:
                assigned_user_name = assigned_user.full_name

        pdata = l.profile_data if isinstance(l.profile_data, dict) and l.profile_data else {}
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
            "email": l.email,
            "origin": l.origin,
            "responsible": l.responsible,
            "next_step": l.next_step,
            "estimated_value": l.estimated_value or 0,
            "closed_value": l.closed_value or 0,
            "ltv": float(ltv),
            "last_order_date": last_order.created_at.isoformat() if last_order else None,
            "last_order_amount": last_order.amount if last_order else 0,
            "last_contact_at": l.last_contact_at.isoformat() if l.last_contact_at else None,
            "updated_at": ts.isoformat() if ts else None,
            "assigned_user_id": l.assigned_user_id,
            "assigned_user_name": assigned_user_name,
            "internal_notes": l.internal_notes,
            "ad_source": l.ad_source,
            "ad_campaign_name": l.ad_campaign_name,
            "ad_creative_url": l.ad_creative_url
        })
    return {"status": "success", "data": results}

@router.post("/leads/{lead_id}/accept")
async def accept_lead(lead_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Atribui o lead ao usuário logado (Assumir atendimento).
    """
    tenant_id = current_user.tenant_id
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.tenant_id == tenant_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if lead.assigned_user_id and lead.assigned_user_id != current_user.id and current_user.role != 'super_admin':
        raise HTTPException(status_code=403, detail="Lead já está em atendimento por outro agente")

    lead.assigned_user_id = current_user.id
    
    # [TIMELINE LOG]
    from models.lead_timeline import LeadTimeline
    new_event = LeadTimeline(
        tenant_id=tenant_id,
        lead_id=lead_id,
        user_id=current_user.id,
        action="assigned",
        details={"user_name": current_user.full_name}
    )
    db.add(new_event)
    
    db.commit()
    
    # Notificar via WS
    await manager.broadcast_to_tenant(tenant_id, {
        "type": "lead_assigned",
        "lead_id": lead_id,
        "assigned_user_id": current_user.id,
        "assigned_user_name": current_user.full_name
    })
    
    return {"status": "success", "message": "Lead assumido com sucesso"}

@router.post("/leads/{lead_id}/transfer")
async def transfer_lead(lead_id: str, target_user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Transfere o lead para outro atendente.
    """
    tenant_id = current_user.tenant_id
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.tenant_id == tenant_id).first()
    target = db.query(User).filter(User.id == target_user_id, User.tenant_id == tenant_id).first()
    
    if not lead or not target:
        raise HTTPException(status_code=404, detail="Lead ou Usuário destino não encontrado")

    lead.assigned_user_id = target_user_id
    
    # [TIMELINE LOG]
    from models.lead_timeline import LeadTimeline
    new_event = LeadTimeline(
        tenant_id=tenant_id,
        lead_id=lead_id,
        user_id=current_user.id,
        action="transferred",
        details={"from_user": current_user.full_name, "to_user": target.full_name, "to_user_id": target_user_id}
    )
    db.add(new_event)
    
    db.commit()
    
    await manager.broadcast_to_tenant(tenant_id, {
        "type": "lead_assigned",
        "lead_id": lead_id,
        "assigned_user_id": target_user_id,
        "assigned_user_name": target.full_name
    })
    
    return {"status": "success"}

@router.post("/leads/{lead_id}/notes")
def update_internal_notes(lead_id: str, payload: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Atualiza as notas internas de um lead.
    """
    tenant_id = current_user.tenant_id
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.tenant_id == tenant_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead.internal_notes = payload.get("notes", "")
    db.commit()
    return {"status": "success"}


@router.get("/messages/{lead_id}")
def get_messages(lead_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Retorna o histórico de mensagens de um lead específico, incluindo mídia.
    """
    tenant_id = current_user.tenant_id
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.tenant_id == tenant_id).first()
    if not lead:
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
    name: Optional[str] = None
    phone: Optional[str] = None
    pipeline_stage: Optional[str] = None
    temperature: Optional[str] = None
    score: Optional[int] = None
    tags: Optional[list[str]] = None
    email: Optional[str] = None
    origin: Optional[str] = None
    responsible: Optional[str] = None
    next_step: Optional[str] = None
    estimated_value: Optional[float] = None
    closed_value: Optional[float] = None

@router.post("/leads")
def create_lead(payload: LeadUpdateInput, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Cria um Lead manulmente no CRM.
    """
    tenant_id = current_user.tenant_id
    if not payload.name:
        raise HTTPException(status_code=400, detail="Name is required")
        
    new_lead = Lead(
        tenant_id=tenant_id,
        name=payload.name,
        phone=payload.phone if payload.phone else (payload.email if payload.email else "11999999999"),
        email=payload.email,
        pipeline_stage=payload.pipeline_stage or "lead",
        temperature=payload.temperature or "frio",
        channel="manual",
    )
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    return {"status": "success", "data": {"id": new_lead.id}}

@router.put("/leads/{lead_id}")
def update_lead(lead_id: str, payload: LeadUpdateInput, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenant_id = current_user.tenant_id
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.tenant_id == tenant_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if payload.name is not None:
        lead.name = payload.name
    
    old_stage = lead.pipeline_stage
    if payload.pipeline_stage is not None:
        lead.pipeline_stage = payload.pipeline_stage
        
        # [AUDIT] Log stage change
        from services.audit_service import log_action
        log_action(db, tenant_id, "move_pipeline", "lead", current_user.id, lead_id, {"from": old_stage, "to": payload.pipeline_stage})

    if payload.temperature is not None:
        lead.temperature = payload.temperature
    if payload.score is not None:
        lead.score = payload.score
    if payload.tags is not None:
        lead.tags = payload.tags
    if payload.email is not None:
        lead.email = payload.email
    if payload.origin is not None:
        lead.origin = payload.origin
    if payload.responsible is not None:
        lead.responsible = payload.responsible
    if payload.next_step is not None:
        lead.next_step = payload.next_step
    if payload.estimated_value is not None:
        lead.estimated_value = payload.estimated_value
    if payload.closed_value is not None:
        lead.closed_value = payload.closed_value

    db.commit()
    
    # [AUDIT FIX] - Notificar UI sobre a mudança de estágio ou dados via WS
    asyncio.create_task(manager.broadcast_to_tenant(tenant_id, {
        "type": "inbox_update",
        "lead_id": lead_id,
        "message": {
            "sender_type": "system",
            "content": f"Lead atualizado: {payload.pipeline_stage or 'dados'}",
            "media_url": None,
            "media_type": None
        }
    }))
    
    return {"status": "success"}


@router.post("/leads/{lead_id}/read")
def mark_lead_read(lead_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Zera o unread_count do lead quando o atendente abre a conversa.
    """
    tenant_id = current_user.tenant_id
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.tenant_id == tenant_id).first()
    if not lead:
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


@router.post("/leads/{lead_id}/send-media")
async def send_lead_media(
    lead_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Envia uma mídia (imagem, doc, áudio) para o lead via atendente humano.
    """
    tenant_id = current_user.tenant_id
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.tenant_id == tenant_id).first()
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not lead or not tenant:
        raise HTTPException(status_code=404, detail="Lead/Tenant not found")

    # 1. Salvar arquivo localmente
    import os, uuid, base64
    ext = file.filename.split(".")[-1]
    filename = f"human_{uuid.uuid4().hex[:8]}.{ext}"
    save_dir = os.path.join("public", "media_storage", str(tenant_id))
    os.makedirs(save_dir, exist_ok=True)
    filepath = os.path.join(save_dir, filename)
    
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    
    media_url = f"/media/{tenant_id}/{filename}"
    
    # 2. Determinar tipo de mídia
    mtype = "document"
    if ext.lower() in ["jpg", "jpeg", "png", "webp", "gif"]: mtype = "image"
    elif ext.lower() in ["mp3", "ogg", "wav", "m4a"]: mtype = "audio"
    
    # 3. Salvar no Banco
    new_msg = Message(
        tenant_id=tenant_id,
        lead_id=lead_id,
        sender_type="human",
        content=f"📎 Mídia enviada: {file.filename}",
        media_url=media_url,
        media_type=mtype
    )
    db.add(new_msg)
    db.commit()
    
    # 4. Enviar via Evolution
    try:
        import httpx
        from services.evolution_sender import settings
        integ = tenant.integrations or {}
        evt_url = (integ.get("evolution_api_url") or settings.EVOLUTION_API_URL).strip().rstrip('/')
        evt_key = (integ.get("evolution_api_key") or settings.EVOLUTION_API_KEY).strip()
        
        # Converter para base64 para enviar via API
        b64_content = base64.b64encode(content).decode("utf-8")
        
        evt_endpoint = f"{evt_url}/message/sendMedia/{tenant.evolution_instance_id}"
        payload = {
            "number": lead.phone,
            "mediaMessage": {
                "mediatype": mtype,
                "fileName": file.filename,
                "media": b64_content
            }
        }
        
        async with httpx.AsyncClient() as client:
            await client.post(evt_endpoint, json=payload, headers={"apikey": evt_key}, timeout=30.0)
            
    except Exception as e:
        print(f"[Inbox Media] Erro ao enviar para Evolution: {e}")

    # 5. Broadcast WS
    await manager.broadcast_to_tenant(tenant_id, {
        "type": "inbox_update",
        "lead_id": lead_id,
        "message": {
            "sender_type": "human",
            "content": new_msg.content,
            "media_url": media_url,
            "media_type": mtype,
            "created_at": new_msg.created_at.isoformat()
        }
    })
    
    return {"status": "success", "media_url": media_url}


@router.get("/leads/{lead_id}/timeline")
def get_lead_timeline(lead_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Retorna a linha do tempo de atendimento do lead (quem assumiu, quem transferiu).
    """
    tenant_id = current_user.tenant_id
    from models.lead_timeline import LeadTimeline
    
    events = db.query(LeadTimeline).filter(
        LeadTimeline.lead_id == lead_id,
        LeadTimeline.tenant_id == tenant_id
    ).order_by(LeadTimeline.created_at.desc()).all()
    
    results = []
    for e in events:
        results.append({
            "action": e.action,
            "user_name": e.details.get("user_name", "Sistema"),
            "details": e.details,
            "created_at": e.created_at.isoformat()
        })
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
            
            if data.get("action") == "resume_ai":
                lead_id = data.get("lead_id")
                if lead_id:
                    db = SessionLocal()
                    try:
                        lead = db.query(Lead).filter(Lead.id == lead_id, Lead.tenant_id == tenant_id).first()
                        if lead:
                            lead.is_paused_for_human = 0
                            db.commit()
                            await manager.broadcast_to_tenant(tenant_id, {
                                "type": "inbox_update",
                                "lead_id": lead_id,
                                "message": {
                                    "sender_type": "system",
                                    "content": "IA reativada pelo atendente",
                                    "media_url": None, "media_type": None
                                }
                            })
                    finally:
                        db.close()

            elif data.get("action") == "send_message":
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

                    # [AUDIT FIX] - Marcar lead como pausado para humano ao enviar manual
                    lead.is_paused_for_human = 1
                    
                    # Save message in DB
                    new_msg = Message(
                        tenant_id=tenant_id,
                        lead_id=lead_id,
                        sender_type="human",
                        content=content,
                    )
                    db.add(new_msg)
                    db.commit()

                    # Send to respective channel
                    if lead.channel == "instagram":
                        try:
                            from services.instagram_service import instagram_service
                            # For Instagram, lead.phone stores the username
                            asyncio.create_task(asyncio.to_thread(instagram_service.send_message, tenant, lead.phone, content))
                        except Exception as e:
                            print(f"[Inbox] Falha ao enviar via Instagram: {e}")
                    else:
                        # Default to WhatsApp (best-effort)
                        try:
                            from services.evolution_sender import send_whatsapp_message
                            integ = tenant.integrations or {}
                            evt_url = integ.get("evolution_api_url")
                            evt_key = integ.get("evolution_api_key")
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
