import json
import asyncio
from core.database import SessionLocal
from models.buffer import MessageBuffer
from models import Lead, Tenant, Message
from datetime import datetime

BUFFER_TIME = 30  
_buffer_tasks = {}

def handle_incoming_message(tenant_id: str, lead_id: str, message_text: str):
    """
    Recebe uma mensagem e persiste no banco de dados (SQLite Persistence).
    Isso substitui o Redis em ambientes onde ele não está disponível.
    """
    buffer_key = f"{tenant_id}:{lead_id}"
    print(f"[DEBUG] handle_incoming_message (Persistent): {buffer_key} - {message_text}")
    
    # 1. Salvar no banco de forma persistente
    db = SessionLocal()
    try:
        new_entry = MessageBuffer(
            tenant_id=tenant_id,
            lead_id=lead_id,
            content=message_text
        )
        db.add(new_entry)
        db.commit()
    finally:
        db.close()
    
    # 2. Gerenciar o Debounce (30s)
    if buffer_key in _buffer_tasks:
        _buffer_tasks[buffer_key].cancel()
        print(f"[DEBUG] Timer resetado para {buffer_key}")

    try:
        loop = asyncio.get_running_loop()
        task = loop.create_task(deferred_lead_buffer(tenant_id, lead_id))
        _buffer_tasks[buffer_key] = task
    except RuntimeError:
        pass

async def deferred_lead_buffer(tenant_id: str, lead_id: str):
    """Aguarda o buffer e depois envia para a fila de processamento."""
    try:
        await asyncio.sleep(BUFFER_TIME)
        # Roda o processamento
        await asyncio.get_event_loop().run_in_executor(None, process_lead_buffer, tenant_id, lead_id)
        
        buffer_key = f"{tenant_id}:{lead_id}"
        if buffer_key in _buffer_tasks:
            del _buffer_tasks[buffer_key]
    except asyncio.CancelledError:
        pass

def process_lead_buffer(tenant_id: str, lead_id: str):
    """
    Puxa todas as mensagens pendentes do banco para esse lead e processa com IA.
    """
    buffer_key = f"{tenant_id}:{lead_id}"
    print(f"[DEBUG] process_lead_buffer start for {buffer_key}")
    
    db = SessionLocal()
    try:
        # Puxar mensagens do buffer
        pending_msgs = db.query(MessageBuffer).filter(
            MessageBuffer.tenant_id == tenant_id,
            MessageBuffer.lead_id == lead_id
        ).order_by(MessageBuffer.created_at.asc()).all()
        
        if not pending_msgs:
            return

        consolidated_text = " ".join([m.content for m in pending_msgs])
        
        # Limpar o buffer no banco para esse lead
        db.query(MessageBuffer).filter(
            MessageBuffer.tenant_id == tenant_id,
            MessageBuffer.lead_id == lead_id
        ).delete()
        db.commit()

        # Iniciar fluxo da IA
        _execute_ai_flow(db, tenant_id, lead_id, consolidated_text)

    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def _execute_ai_flow(db, tenant_id, lead_id, consolidated_text):
    from services.llm_engine import process_conversation
    from services.action_resolver import ActionResolver
    from models import Tenant, Lead, Message
    from services.evolution_sender import send_whatsapp_message, send_presence
    from core.config import settings
    
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    
    if lead and getattr(lead, "is_paused_for_human", 0) == 1:
        print(f"[BUFFER SKIP] Lead {lead_id} em modo humano.")
        return

    print(f"[IA START] Processando context para {lead_id}")
    
    ai_c = tenant.ai_config or {}
    kb = tenant.knowledge_base or {}
    integ = tenant.integrations or {}
    
    # API Key: prioridade tenant > global settings
    openai_key = integ.get("openai_api_key") or settings.OPENAI_API_KEY
    llm_model = integ.get("llm_model") or settings.LLM_MODEL
    
    # Contexto enriquecido (mantém compat com versão antiga)
    tenant_context = f"Empresa: {kb.get('company_name') or tenant.name}."
    if ai_c.get("agent_goal"):
        tenant_context += f" Objetivo: {ai_c['agent_goal']}."
    if ai_c.get("agent_tone"):
        tenant_context += f" Tom: {ai_c['agent_tone']}."
    
    lead_profile = dict(lead.profile_data) if lead.profile_data else {}
    lead_profile["nome"] = lead.name
    lead_profile["telefone"] = lead.phone
    lead_profile["canal"] = getattr(lead, "channel", "whatsapp")
    lead_profile["etapa_pipeline"] = lead.pipeline_stage or "novo"
    lead_profile["temperatura"] = getattr(lead, "temperature", "desconhecida")
    lead_profile["score"] = getattr(lead, "score", 0)
    
    # History fetch (últimas 15 msgs)
    messages_db = db.query(Message).filter(Message.lead_id == lead_id).order_by(Message.created_at.desc()).limit(15).all()
    messages_db.reverse()
    history = [{"sender_type": m.sender_type, "content": m.content} for m in messages_db]

    # Typing presence
    asyncio.run(send_presence(
        tenant.evolution_instance_id, lead.phone, "composing",
        integ.get("evolution_api_url"), integ.get("evolution_api_key")
    ))

    try:
        resultado = asyncio.run(process_conversation(
            tenant_context=tenant_context,
            lead_profile=lead_profile,
            conversation_history=history,
            latest_message=consolidated_text,
            openai_api_key=openai_key,
            model=llm_model,
            ai_config=ai_c,
            knowledge_base=kb
        ))
        
        reply = resultado.get("reply_text")
        if reply:
            # Salvar mensagem da IA no DB
            db.add(Message(tenant_id=tenant_id, lead_id=lead_id, sender_type="ai", content=reply))
            db.commit()
            
            # Enviar texto via WhatsApp/Instagram
            if getattr(lead, "channel", "whatsapp") == "instagram" and integ.get("instagram_page_token"):
                import requests
                ig_sid = lead.phone.replace("ig_", "")
                page_token = integ.get("instagram_page_token")
                try:
                    res = requests.post(
                        "https://graph.facebook.com/v19.0/me/messages",
                        json={"recipient": {"id": ig_sid}, "message": {"text": reply}},
                        params={"access_token": page_token},
                        timeout=5
                    )
                    print(f"[IG DIRECT] IA Reply Status: {res.status_code} - {res.text}")
                except Exception as e:
                    print(f"[IG DIRECT] Falha no roteamento nativo: {e}")
            else:
                asyncio.run(send_whatsapp_message(
                    tenant.evolution_instance_id, lead.phone, reply,
                    integ.get("evolution_api_url"), integ.get("evolution_api_key")
                ))
            
            # Auto-TTS: se habilitado, também enviar como áudio
            if ai_c.get("auto_audio"):
                try:
                    from services.tts_service import text_to_speech_evolution
                    # Enviar presença "gravando" antes do áudio
                    asyncio.run(send_presence(
                        tenant.evolution_instance_id, lead.phone, "recording",
                        integ.get("evolution_api_url"), integ.get("evolution_api_key")
                    ))
                    asyncio.run(text_to_speech_evolution(
                        text=reply,
                        instance_id=tenant.evolution_instance_id,
                        remote_jid=lead.phone,
                        evolution_url=integ.get("evolution_api_url") or settings.EVOLUTION_API_URL,
                        evolution_api_key=integ.get("evolution_api_key") or settings.EVOLUTION_API_KEY,
                        openai_api_key=openai_key
                    ))
                    print(f"[TTS] Áudio enviado para {lead.phone}")
                except Exception as e:
                    print(f"[TTS] Falha no auto-áudio: {e}")
            
            # WebSocket broadcast
            from services.websocket_manager import manager
            asyncio.run(manager.broadcast_to_tenant(tenant_id, {
                "type": "inbox_update",
                "lead_id": lead_id,
                "message": {"sender_type": "ai", "content": reply}
            }))
            
        # Executar Actions (pipeline, temperatura, agendamento, etc.)
        if resultado.get("actions"):
            resolver = ActionResolver(db, tenant_id, lead_id)
            resolver.execute_all(resultado["actions"])
            
            # Broadcast ações para UI atualizar em tempo real
            from services.websocket_manager import manager
            asyncio.run(manager.broadcast_to_tenant(tenant_id, {
                "type": "lead_actions_executed",
                "lead_id": lead_id,
                "actions": resultado["actions"]
            }))
            
    except Exception as e:
        import traceback
        print(f"[IA Error] {e}")
        traceback.print_exc()
