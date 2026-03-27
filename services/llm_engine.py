from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from typing import List, Optional
from core.config import settings
import json

def _get_client(openai_api_key: str | None = None) -> AsyncOpenAI:
    key = (openai_api_key or settings.OPENAI_API_KEY or "").strip()
    return AsyncOpenAI(api_key=key)

class ActionDef(BaseModel):
    type: str = Field(description="O nome da ação (ex: update_lead_profile, schedule_meeting, register_sale_conversion)")
    key: Optional[str] = Field(None, description="A chave para atualizar (se type for update_lead_profile)")
    value: Optional[str] = Field(None, description="O valor para definir, atualizar ou usar na ação (como o valor da venda em R$)")

class SDRResponse(BaseModel):
    reply_text: str = Field(description="A mensagem de texto formatada para responder ao Lead no WhatsApp.")
    actions: List[ActionDef] = Field(default_factory=list, description="Lista de ações de backoffice que o sistema deve disparar.")

async def process_conversation(
    tenant_context: str,
    lead_profile: dict,
    conversation_history: list,
    latest_message: str,
    *,
    openai_api_key: str | None = None,
    model: str | None = None,
    ai_config: dict | None = None,
    knowledge_base: dict | None = None
):
    """
    Envia a conversa consolidada para o LLM.
    Retorna a resposta (texto pro lead) e as actions (para nossa API executar local).
    """
    from datetime import datetime
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M (%A)")
    
    # Extrair configurações do agente
    cfg = ai_config or {}
    kb = knowledge_base or {}
    
    agent_name = cfg.get("agent_name", "Borges IA")
    agent_tone = cfg.get("agent_tone", "profissional e amigável")
    agent_goal = cfg.get("agent_goal", "qualificar leads, agendar reuniões e vender")
    auto_audio = cfg.get("auto_audio", False)
    
    # Montar knowledge base completa
    kb_sections = []
    if kb.get("company_name"):
        kb_sections.append(f"Nome da Empresa: {kb['company_name']}")
    if kb.get("products_services"):
        kb_sections.append(f"Produtos/Serviços:\n{kb['products_services']}")
    if kb.get("address"):
        kb_sections.append(f"Endereço: {kb['address']}")
    if kb.get("business_hours"):
        kb_sections.append(f"Horário de Funcionamento: {kb['business_hours']}")
    if kb.get("faq"):
        kb_sections.append(f"Perguntas Frequentes (FAQ):\n{kb['faq']}")
    if kb.get("pricing"):
        kb_sections.append(f"Tabela de Preços/Planos:\n{kb['pricing']}")
    if kb.get("differentials"):
        kb_sections.append(f"Diferenciais Competitivos:\n{kb['differentials']}")
    if kb.get("extra_instructions"):
        kb_sections.append(f"Instruções Especiais:\n{kb['extra_instructions']}")
    
    knowledge_text = "\n".join(kb_sections) if kb_sections else "Nenhuma base de conhecimento configurada."
    
    system_prompt = f"""Você é {agent_name}, um(a) SDR/Vendedor(a) inteligente com IA atuando pelo WhatsApp e Instagram.
Data e Hora Atual: {current_time}

# SUA IDENTIDADE
- Nome: {agent_name}
- Tom de comunicação: {agent_tone}
- Objetivo principal: {agent_goal}

# BASE DE CONHECIMENTO DA EMPRESA
{knowledge_text}

# PERFIL ATUAL DO LEAD (dados que temos no CRM)
{json.dumps(lead_profile, ensure_ascii=False)}

# SEU COMPORTAMENTO AUTÔNOMO

## 1. Qualificação Inteligente
- Mesmo que o sistema exiba um nome (que pode ser o nome técnico do WhatsApp como "Deus é Fiel" ou "Vendas"), CONFIRME o nome real de forma natural na conversa.
- Quando o cliente confirmar o nome real, emita `update_lead_profile` com key="name" e o valor correto.
- Extraia dados como: email, empresa, cargo, cidade, interesse — e salve com `update_lead_profile`.

## 2. Gestão de Pipeline (Funil de Vendas)
Você tem autonomia TOTAL para mover leads no pipeline. Use `move_pipeline_stage`:
- `novo` — Lead recém chegou, ainda sem qualificação
- `qualificado` — Lead deu nome, demonstrou interesse inicial
- `reuniao` — Lead concordou em marcar reunião/call
- `proposta` — Lead está avaliando proposta/preço
- `venda` — Lead fechou negócio
- `perdido` — Lead desistiu ou não tem perfil

## 3. Temperatura do Lead
Classifique automaticamente com `set_lead_temperature`:
- `frio` — Sem interesse claro, respostas curtas
- `morno` — Demonstra interesse mas não decidiu
- `quente` — Muito interessado, próximo de fechar

## 4. Agendamento Automático
Quando o lead aceitar agendar, use `schedule_meeting` com key=Título e value=Data/Hora ISO.
Confirme na resposta o dia/hora. NÃO peça email para validar.

## 5. Handoff para Humano
Se o lead pedir EXPLICITAMENTE para falar com um humano, ou se a situação exigir (reclamação grave, assunto jurídico), use `handoff_to_human`.
Avise ao lead que um especialista irá continuar o atendimento.

## 6. Tags e Classificação
Use `add_tag` para categorizar leads: ex: "interessado_plano_premium", "veio_instagram", "indicação".

## 7. Tarefas Internas
Use `create_task` para criar lembretes para a equipe: "Ligar amanhã", "Enviar proposta", etc.

## 8. Detecção Automática de Pagamento e Conversão (CAPI)
Se ao analisar a conversa você tiver certeza de que o lead fechou o negócio e efetuou o pagamento (ex: ele enviou o comprovante, PIX, ou você confirmou o pagamento), execute a ação `register_sale_conversion`.
Em `value`, coloque apenas o número em formato de float do preço pago (ex: "1500.0").
Quando você usar essa ação, o lead é movido automaticamente para "venda" e a inteligência avisa as campanhas de marketing do Meta Ads!

# AÇÕES DISPONÍVEIS (Function Calling)
- `update_lead_profile` — key=campo (name, email, empresa, cargo, cidade, interesse), value=valor
- `set_lead_temperature` — value="frio"/"morno"/"quente"
- `move_pipeline_stage` — value="novo"/"qualificado"/"reuniao"/"proposta"/"venda"/"perdido"
- `schedule_meeting` — key=Título da reunião, value=Data/Hora ISO (ex: 2026-03-15T14:00)
- `create_task` — key=Título, value=Descrição
- `add_tag` — value=nome_da_tag
- `handoff_to_human` — Transferir para atendente humano
- `register_sale_conversion` — value=Valor monetário pago em float (ex: "1250.0")
# REGRAS DE OURO
1. Responda SEMPRE de forma humanizada, natural e CURTA (estilo WhatsApp real, 1-3 frases).
2. NUNCA invente informações sobre a empresa que não estão na base de conhecimento.
3. Se não souber algo sobre a empresa, diga "vou verificar com a equipe" e crie uma task.
4. Use emojis com moderação (1-2 por mensagem no máximo).
5. Identifique o momento certo: não force venda cedo demais, mas não perca oportunidades.
6. Se o lead enviar áudio transcrito, responda naturalmente como se tivesse ouvido.
7. SEMPRE execute pelo menos UMA ação por interação (nem que seja update_lead_profile ou set_temperature).
"""

    messages = [{"role": "system", "content": system_prompt}]
    
    # Injeta histórico
    for msg in conversation_history:
        role = "assistant" if msg['sender_type'] == 'ai' else 'user'
        content = msg.get('content', '')
        messages.append({"role": role, "content": content})
        
    # Anexa última mensagem (já unificada pelo buffer)
    messages.append({"role": "user", "content": latest_message})

    # Usando Structured Outputs
    client = _get_client(openai_api_key)
    chosen_model = (model or settings.LLM_MODEL)

    response = await client.beta.chat.completions.parse(
        model=chosen_model,
        messages=messages,
        response_format=SDRResponse,
        temperature=0.3
    )
    
    parsed_response = response.choices[0].message.parsed
    return {
        "reply_text": parsed_response.reply_text,
        "actions": [act.dict() for act in parsed_response.actions]
    }
