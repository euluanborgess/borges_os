import json
import asyncio
from core.redis_client import redis_client

BUFFER_TIME = 15  # Segundos

def handle_incoming_message(tenant_id: str, lead_id: str, message_text: str):
    """
    Recebe uma mensagem e enfileira no Redis.
    Se for a primeira mensagem da rajada, agenda a task Asyncio.
    """
    redis_key = f"buffer:{tenant_id}:{lead_id}"
    
    try:
        # Adicionar mensagem na lista do Redis
        length = redis_client.rpush(redis_key, message_text)

        # Se formos o primeiro a inserir, agenda o processamento
        if length == 1:
            # Coloca a expiração para não sujar o redis caso a task falhe
            redis_client.expire(redis_key, BUFFER_TIME * 3)

            # Despacha para processamento assíncrono em background
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(deferred_lead_buffer(tenant_id, lead_id))
            except RuntimeError:
                pass
    except Exception as e:
        # DEV-safe behavior: if Redis is down, don't crash the webhook.
        # We still store the inbound message in DB in the webhook route.
        print(f"[Buffer] Redis indisponível — IA/buffer desativado para esta mensagem. Erro: {e}")
        return

async def deferred_lead_buffer(tenant_id: str, lead_id: str):
    """Aguarda o buffer e depois envia para a fila de processamento (em thread separada para não travar o loop)."""
    await asyncio.sleep(BUFFER_TIME)
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, process_lead_buffer, tenant_id, lead_id)

def process_lead_buffer(tenant_id: str, lead_id: str):
    """
    Função síncrona que processa as mensagens acumuladas no Redis.
    """
    redis_key = f"buffer:{tenant_id}:{lead_id}"
    
    # Pega tudo e deleta atomicamente usando transaction/pipeline ou só lendo depois deletando
    # O ideal aqui é ler tudo e deletar. (Para garantir atomicidade num ambiente de concorrência,
    # seria bom usar lua script, mas o básico funciona bem).
    messages = redis_client.lrange(redis_key, 0, -1)
    redis_client.delete(redis_key)
    
    if not messages:
        return
    
    consolidated_text = " ".join(messages)
    
    print(f"[BUFFER DONE] Enviando para IA -> Tenant: {tenant_id} | Lead: {lead_id}")
    print(f"Texto Consolidado: {consolidated_text}")
    
    import asyncio
    from core.database import SessionLocal
    from services.llm_engine import process_conversation
    from services.action_resolver import ActionResolver
    from models import Tenant, Lead, Message
    
    # Abrir sessão no banco
    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        
        ai_c = tenant.ai_config or {}
        kb = tenant.knowledge_base or {}
        
        agent_name = ai_c.get("agent_name") or "Assistente Virtual"
        agent_tone = ai_c.get("agent_tone") or "Profissional, acolhedor e focado em vendas"
        agent_goal = ai_c.get("agent_goal") or "Qualificar o lead e conduzir para uma conversão."
        sys_prompt = ai_c.get("system_prompt") or ""
        
        biz_name = tenant.name if tenant else 'Desconhecida'
        biz_niche = kb.get("business_niche") or "Vendas e Serviços"
        biz_hours = kb.get("working_hours") or "Horário Comercial"
        biz_address = kb.get("physical_address") or "Atendimento Online"
        biz_products = kb.get("products_services") or "Consulte nosso catálogo para mais informações."
        biz_objections = kb.get("objection_handling") or "Em caso de objeção, mostre o valor da nossa solução."
        
        tenant_context = f"""
# PERSONA DA IA
Você é {agent_name}, o assistente de vendas da empresa {biz_name} (Nicho: {biz_niche}).
Seu tom de voz obrigatório nas respostas: {agent_tone}.
O SEU OBJETIVO PRINCIPAL NESTA CONVERSA É: {agent_goal}

# BASE DE CONHECIMENTO DA EMPRESA
- Horário de Funcionamento: {biz_hours}
- Endereço Físico: {biz_address}

# NOSSOS PRODUTOS, SERVIÇOS E PREÇOS
{biz_products}

# COMO CONTORNAR OBJEÇÕES DE VENDAS
{biz_objections}

# INSTRUÇÕES ADICIONAIS DO SISTEMA
{sys_prompt}
"""
        # Monta o profile do Lead, injetando o nome e o estágio atual do funil
        lead_profile = dict(lead.profile_data) if lead and lead.profile_data else {}
        if lead:
            lead_profile["nome"] = lead.name if lead.name else "Desconhecido"
            lead_profile["estagio_funil_atual"] = lead.pipeline_stage if lead.pipeline_stage else "novo"
        
        # Puxa histórico real do banco (últimas 20 mensagens para otimizar tokens)
        messages_db = db.query(Message).filter(
            Message.tenant_id == tenant_id, 
            Message.lead_id == lead_id
        ).order_by(Message.created_at.desc()).limit(20).all()
        
        messages_db.reverse() # Coloca em ordem cronológica (mais antigas primeiro)
        
        history = []
        for m in messages_db:
            if m.content == consolidated_text:
                continue # Evita passar a mensagem atual repetida duas vezes (no history e no latest_message)
            history.append({"sender_type": m.sender_type, "content": m.content})
        
        integ = tenant.integrations or {} if tenant else {}
        openai_key = integ.get("openai_api_key")
        chosen_model = (ai_c.get("llm_model") or ai_c.get("model")) if ai_c else None

        resultado_sdr = asyncio.run(
            process_conversation(
                tenant_context=tenant_context,
                lead_profile=lead_profile,
                conversation_history=history,
                latest_message=consolidated_text,
                openai_api_key=openai_key,
                model=chosen_model,
            )
        )
        print(f"RESPOSTA IA: {resultado_sdr['reply_text']}")
        print(f"AÇÕES: {resultado_sdr['actions']}")
        
        # Resolve e Salva as actions no banco!
        if resultado_sdr.get('actions'):
            resolver = ActionResolver(db, tenant_id, lead_id)
            resolver.execute_all(resultado_sdr['actions'])
            
        # Enviar o reply_text de volta pela Evolution API
        reply = resultado_sdr.get('reply_text')
        if reply:
            from models import Tenant, Lead, Message
            from services.evolution_sender import send_whatsapp_message
            
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            
            if tenant and lead and tenant.evolution_instance_id:
                # Salvar a resposta da IA no banco de dados
                ai_message = Message(
                    tenant_id=tenant.id,
                    lead_id=lead.id,
                    sender_type="ai",
                    content=reply
                )
                db.add(ai_message)
                db.commit()
                
                # Para a Evolution V2, basta passar o número na maioria dos casos.
                # Se for enviar o sufixo @s.whatsapp.net, as vezes a API comete erros no br (ex 55119 vs 5511).
                # Vamos passar apenas o ID numérico extraído diretamente do banco (que já veio higienizado do webhook)
                destination_number = lead.phone
                
                # Roda o envio de forma bloqueante para a thread do worker, garantindo que dispare antes de morrer
                integ = tenant.integrations or {}
                asyncio.run(
                    send_whatsapp_message(
                        tenant.evolution_instance_id,
                        destination_number,
                        reply,
                        evolution_url=integ.get("evolution_api_url"),
                        evolution_api_key=integ.get("evolution_api_key"),
                    )
                )

                # Dispara evento WebSockets para a UI (InBox) ser notificada em tempo real
                try:
                    from services.websocket_manager import manager
                    asyncio.run(
                        manager.broadcast_to_tenant(str(tenant.id), {
                            "type": "inbox_update",
                            "lead_id": str(lead.id),
                            "message": {
                                "sender_type": "ai",
                                "content": reply
                            }
                        })
                    )
                except Exception as ws_e:
                    print(f"WS Broadcast falhou no worker da IA: {ws_e}")
            
    except Exception as e:
        import traceback
        print(f"ERRO IA FATAL:")
        traceback.print_exc()
    finally:
        db.close()
        
    return consolidated_text
