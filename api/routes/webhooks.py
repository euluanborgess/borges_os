from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from models import Tenant, Lead
from services.message_buffer import handle_incoming_message
import os
import json
import time
import base64 as b64module
import uuid as uuid_mod

from fastapi.responses import Response

router = APIRouter()

@router.get("/meta")
async def verify_meta_webhook(request: Request):
    """
    Verificação de Webhook exigida pela Meta (Facebook/Instagram).
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    
    verify_token = os.getenv("META_WEBHOOK_VERIFY_TOKEN", "borges_secure_hook_2025")
    
    if mode == "subscribe" and token == verify_token:
        return Response(content=challenge, media_type="text/plain")
    
    return Response(content="Verification failed", status_code=403)

@router.post("/meta")
async def meta_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Recebe os webhooks reais da Meta (notificações de mensagens).
    """
    try:
        payload = await request.json()
        print(f"[META WEBHOOK NATIVO] Payload: {json.dumps(payload)}")
    except Exception:
        return {"status": "invalid_json"}
    
    # Processar apenas objetos instagram ou page
    obj_type = payload.get("object")
    
    if obj_type not in ["instagram", "page"]:
        return {"status": "ignored"}

    entries = payload.get("entry", [])
    for entry in entries:
        messaging_events = entry.get("messaging", [])
        for event in messaging_events:
            if "message" not in event:
                continue
                
            sender_id = event.get("sender", {}).get("id")
            recipient_id = event.get("recipient", {}).get("id")
            message_data = event.get("message", {})
            text = message_data.get("text", "")
            mid = message_data.get("mid", "")
            
            # Ignorar ecos ou mensagens vazias sem mídia
            if message_data.get("is_echo") or not text:
                continue

            # Encontrar o Tenant pelo instagram_business_account_id
            tenant = None
            all_tenants = db.query(Tenant).all()
            for t in all_tenants:
                integ = t.integrations or {}
                # Suporta tanto recipient_id direto quanto o mapeado nas integrações
                if integ.get("instagram_business_account_id") == recipient_id or t.evolution_instance_id == recipient_id:
                    tenant = t
                    break

            if not tenant:
                print(f"[META WEBHOOK NATIVO] Ignorado: Tenant não encontrado para recipient {recipient_id}")
                continue

            # Criar ou buscar Lead
            from sqlalchemy.exc import IntegrityError
            phone = f"ig_{sender_id}"
            lead = db.query(Lead).filter(Lead.tenant_id == tenant.id, Lead.phone == phone).first()

            # Tenta buscar perfil se for novo ou não tiver nome real
            profile_name = None
            profile_pic = None
            
            integ = tenant.integrations or {}
            access_token = integ.get("instagram_token")
            
            if access_token and (not lead or lead.name.startswith("Lead IG")):
                import httpx
                try:
                    # https://developers.facebook.com/docs/messenger-platform/instagram/features/user-profile
                    url = f"https://graph.facebook.com/v19.0/{sender_id}?fields=name,profile_pic&access_token={access_token}"
                    async with httpx.AsyncClient() as client:
                        resp = await client.get(url)
                        if resp.status_code == 200:
                            data = resp.json()
                            profile_name = data.get("name")
                            profile_pic = data.get("profile_pic")
                            print(f"[META WEBHOOK NATIVO] Perfil obtido: {profile_name}")
                except Exception as e:
                    print(f"[META WEBHOOK NATIVO] Erro ao buscar perfil: {str(e)}")

            if not lead:
                try:
                    lead = Lead(
                        tenant_id=tenant.id,
                        phone=phone,
                        name=profile_name or f"Lead IG {sender_id[-4:]}",
                        unread_count=1,
                        channel="instagram",
                        origin="instagram",
                        profile_data={"picture": profile_pic} if profile_pic else {}
                    )
                    db.add(lead)
                    db.commit()
                    db.refresh(lead)
                except IntegrityError:
                    db.rollback()
                    lead = db.query(Lead).filter(Lead.tenant_id == tenant.id, Lead.phone == phone).first()
            else:
                lead.unread_count = (lead.unread_count or 0) + 1
                if profile_name:
                    lead.name = profile_name
                if profile_pic:
                    pdata = dict(lead.profile_data or {})
                    pdata["picture"] = profile_pic
                    lead.profile_data = pdata
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(lead, "profile_data")
                db.commit()

            # Salvar Mensagem
            from models import Message
            new_message = Message(
                tenant_id=tenant.id,
                lead_id=lead.id,
                sender_type="lead",
                content=text,
                media_url=None,
                media_type=None,
                metadata_json={"source": "meta_native", "mid": mid}
            )
            db.add(new_message)
            db.commit()

            # Broadcast Websocket
            from services.websocket_manager import manager
            import asyncio
            asyncio.create_task(manager.broadcast_to_tenant(
                str(tenant.id), 
                {
                    "type": "inbox_update", 
                    "lead_id": str(lead.id), 
                    "lead_name": lead.name, 
                    "lead_phone": lead.phone, 
                    "channel": "instagram", 
                    "unread_count": lead.unread_count, 
                    "lead_avatar": profile_pic,
                    "message": {
                        "sender_type": "lead", 
                        "content": text, 
                        "media_url": None, 
                        "media_type": None, 
                        "created_at": new_message.created_at.isoformat()
                    }
                }
            ))

            # Chamar AI
            if getattr(lead, "is_paused_for_human", 0) != 1:
                handle_incoming_message(str(tenant.id), str(lead.id), text)

    return {"status": "ok"}

@router.post("/evolution")
async def evolution_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Recebe os eventos da Evolution API. Suporta WhatsApp e Instagram Direct.
    """
    try:
        payload = await request.json()
    except Exception:
        return {"status": "invalid_json"}

    event_type_raw = payload.get("event") or ""
    event_type = str(event_type_raw).strip().lower().replace("_", ".")
    instance_name = payload.get("instance")

    if event_type in ("messages.upsert", "messages.upsert."):
        event_type = "messages.upsert"
    if event_type in ("connection.update", "connection.update."):
        event_type = "connection.update"

    tenant = db.query(Tenant).filter(Tenant.evolution_instance_id == instance_name).first()
    if not tenant and instance_name and instance_name.startswith("borges_"):
        all_tenants = db.query(Tenant).all()
        for t in all_tenants:
            if instance_name == f"borges_{str(t.id)[0:8]}" or instance_name == f"borges_insta_{str(t.id)[0:8]}":
                tenant = t
                break
                
    if not tenant:
        return {"status": "tenant_not_found"}

    # Determinar Canal (Instagram Direct vs WhatsApp)
    # A Evolution para Instagram costuma enviar menções e directs.
    channel = "whatsapp"
    data = payload.get("data", {})
    
    # Detecção de Instagram via payload ou nome da instância
    if "insta" in instance_name.lower() or data.get("isInstagram") or data.get("isDirect"):
        channel = "instagram"
        # Ignorar menções (Stories), focar apenas em Direct Messages
        if data.get("isMention") or data.get("isStory"):
            return {"status": "instagram_mention_ignored"}

    # ------------------ EVENTO DE CONEXÃO ------------------
    if event_type == "connection.update":
        return {"status": "connection_handled"}

    # ------------------ EVENTO DE MENSAGENS ------------------
    if event_type != "messages.upsert":
        return {"status": "ignored"}
        
    msg_obj = data["messages"][0] if "messages" in data and isinstance(data["messages"], list) and len(data["messages"]) > 0 else data
    
    # Ignorar mensagens antigas
    msg_timestamp = msg_obj.get("messageTimestamp") or data.get("messageTimestamp")
    if msg_timestamp:
        if int(time.time()) - int(msg_timestamp) > 300:
            return {"status": "old_message_ignored"}
        
    key = msg_obj.get("key", {}) or data.get("key", {})
    remote_jid = key.get("remoteJid", "")
    
    # Regra de Ouro: Ignorar mensagens enviadas por "mim" ou Grupos
    if key.get("fromMe") or (remote_jid and remote_jid.endswith("@g.us")):
        return {"status": "ignored"}
        
    # Higienizar JID/Phone
    if remote_jid and remote_jid.endswith("@lid"):
        alt_jid = key.get("remoteJidAlt") or msg_obj.get("participant") or data.get("remoteJidAlt")
        if alt_jid: remote_jid = alt_jid

    if not remote_jid: return {"status": "no_remote_jid_ignored"}
    phone = remote_jid.split("@")[0] if "@" in remote_jid else remote_jid
    push_name = msg_obj.get("pushName") or data.get("pushName") or ("Cliente Instagram" if channel == "instagram" else "Desconhecido")
    
    # ─────────────────── CLASSIFICAR TIPO DE MÍDIA ───────────────────
    message_content = msg_obj.get("message", {}) or msg_obj
    text = ""
    media_type = None
    media_url = None
    is_media = False
    media_mimetype = ""
    media_filename = ""
    
    # WhatsApp / Instagram Text
    if "conversation" in message_content: text = message_content["conversation"]
    elif "extendedTextMessage" in message_content: text = message_content["extendedTextMessage"].get("text", "")
    # Instagram Direct específico
    elif "text" in message_content and isinstance(message_content["text"], str): text = message_content["text"]
    
    # Media Handlers
    elif "audioMessage" in message_content:
        media_type = "audio"; is_media = True; media_mimetype = message_content["audioMessage"].get("mimetype", "audio/ogg")
    elif "imageMessage" in message_content:
        media_type = "image"; is_media = True; media_mimetype = message_content["imageMessage"].get("mimetype", "image/jpeg")
        text = message_content["imageMessage"].get("caption", "")
    
    if not text and not is_media: return {"status": "no_text_or_media_ignored"}
    if is_media and not text: text = f"📎 Mídia ({media_type}) recebida"
    
    # ─────────────────── PROCESSAR MÍDIA ───────────────────
    message_id = key.get("id")
    ai_context_text = text
    
    if is_media:
        from services.media_processor import download_media_from_evolution, transcribe_audio_base64, describe_image_base64
        base64_data = ""
        # Improved base64 search
        if data.get("message", {}).get("base64"): base64_data = data["message"]["base64"]
        elif msg_obj.get("message", {}).get("base64"): base64_data = msg_obj["message"]["base64"]
        elif data.get("base64"): base64_data = data["base64"]
        
        if base64_data:
            ext_map = {"audio/ogg": "ogg", "audio/mpeg": "mp3", "image/jpeg": "jpg", "image/png": "png"}
            ext = ext_map.get(media_mimetype, "bin")
            filename = f"{uuid_mod.uuid4().hex[:12]}_{media_type}.{ext}"
            save_dir = os.path.join("public", "media_storage", str(tenant.id))
            os.makedirs(save_dir, exist_ok=True)
            filepath = os.path.join(save_dir, filename)
            try:
                pure_base64 = base64_data.split(",")[-1] if "," in base64_data else base64_data
                with open(filepath, "wb") as f: f.write(b64module.b64decode(pure_base64))
                media_url = f"/media/{tenant.id}/{filename}"
            except Exception: media_url = ""
        
        if media_type == "audio" and base64_data:
            transcription = await transcribe_audio_base64(base64_data, openai_api_key=(tenant.integrations or {}).get('openai_api_key'))
            if transcription: ai_context_text = f"[Áudio Transcrito]\n{transcription}"
        elif media_type == "image" and base64_data:
            description = await describe_image_base64(base64_data, openai_api_key=(tenant.integrations or {}).get('openai_api_key'))
            ai_context_text = f"[Imagem enviada pelo cliente] Descrição: {description}"
    
    # ─────────────────── IDENTIFICAR OU CRIAR LEAD ───────────────────
    from sqlalchemy.exc import IntegrityError
    lead = db.query(Lead).filter(Lead.tenant_id == tenant.id, Lead.phone == phone).first()
    
    # Função para checar se o nome é genérico
    def is_generic_name(n):
        return not n or n in ("Desconhecido", "Novo Lead", "Cliente Instagram", "") or n.startswith("Lead IG")
        
    lead_name = push_name if push_name and not is_generic_name(push_name) else ("Novo Lead" if channel != "instagram" else "Cliente Instagram")
    
    # Tentar capturar foto de perfil via Evolution API (async)
    profile_pic = None
    if not lead or not lead.profile_data or not lead.profile_data.get("picture"):
        try:
            import httpx
            integ = tenant.integrations or {}
            ev_url = (integ.get("evolution_api_url") or "https://cosmicstarfish-evolution.cloudfy.live").rstrip("/")
            ev_key = integ.get("evolution_api_key") or "bMQLdgHiveJZOejgVQqCMEY0zUSGalNh"
            async with httpx.AsyncClient() as ev_client:
                pic_res = await ev_client.post(
                    f"{ev_url}/chat/fetchProfilePictureUrl/{instance_name}",
                    headers={"apikey": ev_key, "Content-Type": "application/json"},
                    json={"number": phone},
                    timeout=5.0
                )
            if pic_res.status_code == 200:
                profile_pic = pic_res.json().get("profilePictureUrl")
                print(f"[EVOLUTION WEBHOOK] Foto obtida para {push_name}: {profile_pic[:60] if profile_pic else 'None'}")
            else:
                print(f"[EVOLUTION WEBHOOK] Erro ao buscar foto ({pic_res.status_code}): {pic_res.text[:200]}")
        except Exception as e:
            print(f"[EVOLUTION WEBHOOK] Exceção ao buscar foto: {e}")

    # ─────────────────── EXTRAÇÃO DE DADOS DE ANÚNCIO (META ADS / UTMS) ───────────────────
    ad_id, campaign_id, ad_source, ad_url = None, None, None, None
    utm_src, utm_med, utm_camp, utm_cont = None, None, None, None
    
    ctx_info = message_content.get("extendedTextMessage", {}).get("contextInfo", {})
    if not ctx_info: ctx_info = msg_obj.get("contextInfo", {})
        
    ad_reply = ctx_info.get("adReply", {})
    source_url = ctx_info.get("sourceUrl", "")
    
    if ad_reply:
        ad_id = ad_reply.get("adId") or ad_reply.get("creativeId")
        campaign_id = ad_reply.get("campaignId")
        ad_source = "Meta Ads"
    
    if "ctwa" in source_url or "fb.me" in source_url or "facebook.com" in source_url:
        ad_source = "Meta Ads"
        
    if source_url:
        import urllib.parse
        parsed_url = urllib.parse.urlparse(source_url)
        params = urllib.parse.parse_qs(parsed_url.query)
        utm_src = params.get("utm_source", [None])[0]
        utm_med = params.get("utm_medium", [None])[0]
        utm_camp = params.get("utm_campaign", [None])[0]
        utm_cont = params.get("utm_content", [None])[0]

    if not lead:
        try:
            lead = Lead(
                tenant_id=tenant.id, 
                phone=phone, 
                name=lead_name, 
                unread_count=1, 
                channel=channel,
                profile_data={"picture": profile_pic},
                ad_creative_id=ad_id,
                ad_source=ad_source,
                utm_campaign=campaign_id or utm_camp,
                utm_source=utm_src,
                utm_medium=utm_med,
                utm_content=utm_cont,
                ad_creative_url=source_url
            )
            db.add(lead); db.commit(); db.refresh(lead)
        except IntegrityError:
            db.rollback()
            lead = db.query(Lead).filter(Lead.tenant_id == tenant.id, Lead.phone == phone).first()
    else:
        # Atualizar nome se for genérico (inclui nomes gerados automaticamente)
        if is_generic_name(lead.name) and push_name and not is_generic_name(push_name):
            lead.name = push_name
            print(f"[EVOLUTION WEBHOOK] Nome atualizado para o real: {lead.name}")
        
        # Atualizar foto se não tiver (usando flag_modified para JSON)
        if profile_pic and (not lead.profile_data or not lead.profile_data.get("picture")):
            from sqlalchemy.orm.attributes import flag_modified
            pdata = dict(lead.profile_data) if lead.profile_data else {}
            pdata["picture"] = profile_pic
            lead.profile_data = pdata
            flag_modified(lead, "profile_data")
            
        lead.unread_count = (lead.unread_count or 0) + 1
        lead.channel = channel  # Garante canal correto
        db.commit()
        
    # ─────────────────── SALVAR MENSAGEM ───────────────────
    from models import Message
    new_message = Message(
        tenant_id=tenant.id, lead_id=lead.id, sender_type="lead", content=text, 
        media_url=media_url, media_type=media_type, 
        metadata_json={"evolution": {"instance": instance_name, "event": event_type, "channel": channel, "messageId": message_id}}
    )
    db.add(new_message); db.commit()
    
    # ─────────────────── BROADCAST WEBSOCKET ───────────────────
    from services.websocket_manager import manager
    import asyncio
    asyncio.create_task(manager.broadcast_to_tenant(str(tenant.id), {"type": "inbox_update", "lead_id": str(lead.id), "lead_name": lead.name, "lead_phone": lead.phone, "channel": channel, "unread_count": lead.unread_count, "message": {"sender_type": "lead", "content": text, "media_url": media_url, "media_type": media_type, "created_at": new_message.created_at.isoformat()}}))
    
    if getattr(lead, "is_paused_for_human", 0) == 1: return {"status": "paused_for_human"}
    handle_incoming_message(str(tenant.id), str(lead.id), ai_context_text)
    return {"status": "received_and_buffered"}
