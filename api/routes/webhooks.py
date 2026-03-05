from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from models import Tenant, Lead
from services.message_buffer import handle_incoming_message

router = APIRouter()

@router.post("/evolution")
async def evolution_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Recebe os eventos da Evolution API.
    Suporta: texto, áudio, imagem, documento, sticker.
    """
    payload = await request.json()

    event_type_raw = payload.get("event") or ""
    event_type = str(event_type_raw).strip().lower().replace("_", ".")
    instance_name = payload.get("instance")

    # Normalize common Evolution variants
    if event_type in ("messages.upsert", "messages.upsert."):
        event_type = "messages.upsert"
    if event_type in ("connection.update", "connection.update."):
        event_type = "connection.update"

    tenant = db.query(Tenant).filter(Tenant.evolution_instance_id == instance_name).first()
    # Fallback caso evolution_instance_id nao tenha sido salvo
    if not tenant and instance_name and instance_name.startswith("borges_"):
        all_tenants = db.query(Tenant).all()
        for t in all_tenants:
            if instance_name == f"borges_{str(t.id)[0:8]}":
                tenant = t
                tenant.evolution_instance_id = instance_name
                db.commit()
                break
                
    if not tenant:
        return {"status": "tenant_not_found"}

    # ------------------ EVENTO DE CONEXÃO ------------------
    if event_type == "connection.update":
        data = payload.get("data", {})
        state = data.get("state")
        if state == "open":
            import os
            import httpx
            try:
                integ = tenant.integrations or {}
                evt_url = integ.get("evolution_api_url") or os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
                evt_key = integ.get("evolution_api_key") or os.getenv("EVOLUTION_API_KEY", "global-api-key-evolution")
                evt_url = evt_url.strip().rstrip('/')
                headers = {"apikey": evt_key.strip()}
                
                async with httpx.AsyncClient(timeout=10.0) as client:
                    res = await client.get(f"{evt_url}/instance/fetchInstances?instanceName={instance_name}", headers=headers)
                    if res.status_code == 200:
                        inst_list = res.json()
                        if inst_list and isinstance(inst_list, list):
                            owner = inst_list[0].get("ownerJid", "")
                            if owner:
                                tenant.whatsapp_number = owner.split("@")[0]
                                db.commit()
                                print(f"🌟 WEBHOOK: Tenant atualizado via connection.update para {tenant.whatsapp_number}")
            except Exception as e:
                print("Erro no Webhook de connection.update:", e)
        return {"status": "connection_handled"}

    # ------------------ EVENTO DE MENSAGENS ------------------
    if event_type != "messages.upsert":
        return {"status": "ignored"}
        
    data = payload.get("data", {})
    
    # Evolution V2 tem várias formas de agrupar o payload
    msg_obj = {}
    if "messages" in data and isinstance(data["messages"], list) and len(data["messages"]) > 0:
        msg_obj = data["messages"][0]
    else:
        msg_obj = data
        
    # Extrair key
    key = msg_obj.get("key", {})
    if not key and "key" in data:
        key = data["key"]
        
    if key.get("fromMe"):
        return {"status": "ignored"}
        
    remote_jid = key.get("remoteJid", "")
    
    # === CORREÇÃO DE SEGURANÇA WHATSAPP V2.2+ (@lid) ===
    if remote_jid and remote_jid.endswith("@lid"):
        alt_jid = key.get("remoteJidAlt") or msg_obj.get("participant") or msg_obj.get("remoteJidAlt") or data.get("remoteJidAlt")
        if alt_jid:
            remote_jid = alt_jid

    if not remote_jid:
        print("[ERRO WEBHOOK] Não foi possível extrair remoteJid do payload:", payload)
        return {"status": "no_remote_jid_ignored"}
        
    phone = remote_jid.split("@")[0] if "@" in remote_jid else remote_jid
    
    # pushName
    push_name = msg_obj.get("pushName") or data.get("pushName") or "Desconhecido"
    
    # ─────────────────── CLASSIFICAR TIPO DE MÍDIA ───────────────────
    message_content = msg_obj.get("message", {}) or msg_obj
    
    text = ""
    media_type = None      # "audio", "image", "document", "sticker"
    media_url = None        # URL gerada pela Evolution para a mídia
    is_media = False
    media_mimetype = ""
    media_filename = ""
    
    if "conversation" in message_content:
        text = message_content["conversation"]
    elif "extendedTextMessage" in message_content:
        text = message_content["extendedTextMessage"].get("text", "")
    elif "audioMessage" in message_content:
        media_type = "audio"
        is_media = True
        media_mimetype = message_content["audioMessage"].get("mimetype", "audio/ogg")
    elif "imageMessage" in message_content:
        media_type = "image"
        is_media = True
        media_mimetype = message_content["imageMessage"].get("mimetype", "image/jpeg")
        text = message_content["imageMessage"].get("caption", "")  # legenda da imagem
    elif "documentMessage" in message_content:
        media_type = "document"
        is_media = True
        media_mimetype = message_content["documentMessage"].get("mimetype", "application/pdf")
        media_filename = message_content["documentMessage"].get("fileName", "documento")
        text = message_content["documentMessage"].get("caption", "")
    elif "documentWithCaptionMessage" in message_content:
        # Formato alternativo para docs com legenda
        doc_msg = message_content["documentWithCaptionMessage"].get("message", {}).get("documentMessage", {})
        media_type = "document"
        is_media = True
        media_mimetype = doc_msg.get("mimetype", "application/pdf")
        media_filename = doc_msg.get("fileName", "documento")
        text = doc_msg.get("caption", "")
    elif "stickerMessage" in message_content:
        media_type = "sticker"
        is_media = True
        media_mimetype = message_content["stickerMessage"].get("mimetype", "image/webp")
    elif "videoMessage" in message_content:
        media_type = "video"
        is_media = True
        media_mimetype = message_content["videoMessage"].get("mimetype", "video/mp4")
        text = message_content["videoMessage"].get("caption", "")
    
    if not text and not is_media:
        return {"status": "no_text_or_media_ignored"}

    # Se for mídia mas não conseguimos gerar URL/base64, ainda assim registramos a mensagem
    # com um placeholder de conteúdo para aparecer no chat.
    if is_media and not text:
        text = "📎 Mídia recebida"
    
    # ─────────────────── PROCESSAR MÍDIA ───────────────────
    message_id = key.get("id")
    ai_context_text = text  # Texto que será enviado para a IA (pode incluir transcrição/descrição)
    
    if is_media:
        from services.media_processor import (
            download_media_from_evolution, 
            transcribe_audio_base64, 
            describe_image_base64,
            extract_document_text
        )
        
        # Tentar pegar base64 do payload OU baixar via API
        base64_data = data.get("message", {}).get("base64", "")
        if not base64_data:
            base64_data = msg_obj.get("message", {}).get("base64", "") if isinstance(msg_obj.get("message"), dict) else ""
        
        # Fallback: tentar baixar base64 via Evolution API usando o ID da mensagem
        if not message_id:
            # Evolution pode trazer o id em campos alternativos
            message_id = (key or {}).get("id") or msg_obj.get("id") or msg_obj.get("messageId")

        if not base64_data and message_id:
            try:
                import os
                integ = tenant.integrations or {}
                evt_url = integ.get("evolution_api_url") or os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
                evt_key = integ.get("evolution_api_key") or os.getenv("EVOLUTION_API_KEY", "global-api-key-evolution")

                base64_data = await download_media_from_evolution(
                    tenant.evolution_instance_id,
                    message_id,
                    evolution_url=evt_url,
                    evolution_api_key=evt_key,
                    remote_jid=remote_jid,
                )
                if base64_data:
                    print(f"[Media] Base64 baixado via API - {len(base64_data)} chars")
            except Exception as e:
                print(f"[Media Error] Falha ao baixar mídia: {e}")
        
        # Gerar data URI para servir no frontend
        if base64_data:
            # Salvar o arquivo no disco e gerar URL estática
            import base64 as b64module, os, uuid as uuid_mod
            ext_map = {
                "audio/ogg": "ogg", "audio/mpeg": "mp3", "audio/mp4": "m4a", "audio/opus": "ogg",
                "image/jpeg": "jpg", "image/png": "png", "image/webp": "webp",
                "video/mp4": "mp4",
                "application/pdf": "pdf", "application/msword": "doc",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
            }
            ext = ext_map.get(media_mimetype, "bin")
            filename = f"{uuid_mod.uuid4().hex[:12]}_{media_type}.{ext}"
            # Garantir pasta
            os.makedirs("media_storage", exist_ok=True)
            filepath = os.path.join("media_storage", filename)
            try:
                file_bytes = b64module.b64decode(base64_data.split(",")[-1])
                with open(filepath, "wb") as f:
                    f.write(file_bytes)
                media_url = f"/media/{filename}"
                print(f"[Media] Arquivo salvo: {filepath} ({len(file_bytes)} bytes)")
            except Exception as e:
                print(f"[Media Error] Falha ao salvar arquivo: {e}")
                media_url = ""
        
        # Processar para contexto da IA
        if media_type == "audio":
            print("[Whisper] Transcrevendo áudio...")
            transcription = await transcribe_audio_base64(base64_data)
            if transcription:
                ai_context_text = f"[Áudio Transcrito]\n{transcription}"
                if not text:
                    text = ai_context_text
            else:
                ai_context_text = "[Áudio recebido - não foi possível transcrever]"
                if not text:
                    text = ai_context_text
                    
        elif media_type in ("image", "sticker"):
            print("[Vision] Analisando imagem...")
            description = await describe_image_base64(base64_data)
            ai_context_text = f"[Imagem enviada pelo cliente]\nDescrição: {description}"
            if text:
                ai_context_text = f"[Imagem com legenda: {text}]\nDescrição da imagem: {description}"
            if not text:
                text = f"📷 Imagem"
                
        elif media_type == "document":
            print("[Doc] Processando documento...")
            doc_text = await extract_document_text(base64_data, media_filename, media_mimetype)
            ai_context_text = doc_text
            if not text:
                text = f"📄 {media_filename}"
                
        elif media_type == "video":
            ai_context_text = f"[Vídeo recebido: {text or 'sem legenda'}]"
            if not text:
                text = "🎥 Vídeo"
    
    # ─────────────────── IDENTIFICAR OU CRIAR LEAD ───────────────────
    from sqlalchemy.exc import IntegrityError
    
    lead = db.query(Lead).filter(Lead.tenant_id == tenant.id, Lead.phone == phone).first()
    
    # Buscar foto de perfil
    picture_url = ""
    try:
        import httpx
        import os
        integ = tenant.integrations or {}
        evt_url = integ.get("evolution_api_url") or os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
        evt_key = integ.get("evolution_api_key") or os.getenv("EVOLUTION_API_KEY", "global-api-key-evolution")
        
        async with httpx.AsyncClient(timeout=3.0) as client:
            pic_res = await client.post(
                f"{evt_url.strip().rstrip('/')}/chat/fetchProfilePictureUrl/{tenant.evolution_instance_id}",
                headers={"apikey": evt_key.strip()},
                json={"number": f"{phone}@s.whatsapp.net"}
            )
            if pic_res.status_code == 200:
                pic_data = pic_res.json()
                picture_url = pic_data.get("profilePictureUrl", "")
    except Exception as e:
        print(f"[Webhook] Falha silenciosa ao buscar foto de perfil: {e}")

    if not lead:
        try:
            lead = Lead(tenant_id=tenant.id, phone=phone, name=push_name, unread_count=1)
            if picture_url:
                lead.profile_data = {"picture": picture_url}
            db.add(lead)
            db.commit()
            db.refresh(lead)
        except IntegrityError:
            db.rollback()
            lead = db.query(Lead).filter(Lead.tenant_id == tenant.id, Lead.phone == phone).first()
            if not lead:
                return {"status": "lead_creation_failed"}
    else:
        # Atualiza nome, foto e incrementa unread
        changed = False
        if lead.name == "Desconhecido" and push_name != "Desconhecido":
            lead.name = push_name
            changed = True
            
        pdata = dict(lead.profile_data) if lead.profile_data else {}
        if picture_url and pdata.get("picture") != picture_url:
            pdata["picture"] = picture_url
            lead.profile_data = pdata
            changed = True
        
        # Incrementar unread_count
        lead.unread_count = (lead.unread_count or 0) + 1
        changed = True
            
        if changed:
            db.commit()
        
    # ─────────────────── SALVAR MENSAGEM ───────────────────
    from models import Message
    new_message = Message(
        tenant_id=tenant.id,
        lead_id=lead.id,
        sender_type="lead",
        content=text,
        media_url=media_url,
        media_type=media_type,
        metadata_json={
            "evolution": {
                "instance": instance_name,
                "event": event_type,
                "remoteJid": remote_jid,
                "messageId": message_id,
            }
        },
    )
    db.add(new_message)
    db.commit()
    
    # ─────────────────── BROADCAST WEBSOCKET ───────────────────
    import asyncio
    from services.websocket_manager import manager
    asyncio.create_task(
        manager.broadcast_to_tenant(str(tenant.id), {
            "type": "inbox_update",
            "lead_id": str(lead.id),
            "lead_name": lead.name,
            "lead_phone": lead.phone,
            "unread_count": lead.unread_count,
            "message": {
                "sender_type": "lead",
                "content": text,
                "media_url": media_url,
                "media_type": media_type,
                "created_at": new_message.created_at.isoformat() if new_message.created_at else None
            }
        })
    )
    
    if getattr(lead, "is_paused_for_human", 0) == 1:
        return {"status": "paused_for_human"}
        
    # Enviar para a fila de bufferização (usa ai_context_text que inclui transcrição/descrição)
    handle_incoming_message(str(tenant.id), str(lead.id), ai_context_text)
    
    return {"status": "received_and_buffered"}
