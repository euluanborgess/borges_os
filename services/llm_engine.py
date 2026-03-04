from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from typing import List, Optional
from core.config import settings
import json

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

class ActionDef(BaseModel):
    type: str = Field(description="O nome da ação (ex: update_lead_profile, schedule_meeting)")
    key: Optional[str] = Field(None, description="A chave para atualizar (se type for update_lead_profile)")
    value: Optional[str] = Field(None, description="O valor para definir, atualizar ou usar na ação")

class SDRResponse(BaseModel):
    reply_text: str = Field(description="A mensagem de texto formatada para responder ao Lead no WhatsApp.")
    actions: List[ActionDef] = Field(default_factory=list, description="Lista de ações de backoffice que o sistema deve disparar.")

async def process_conversation(tenant_context: str, lead_profile: dict, conversation_history: list, latest_message: str):
    """
    Envia a conversa consolidada para o LLM.
    Retorna a resposta (texto pro lead) e as actions (para nossa API executar local).
    """
    from datetime import datetime
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    system_prompt = f"""
Você é o SDR inteligente (IA) atuando pelo WhatsApp.
Data e Hora Atual do Servidor: {current_time}
Aqui estão as regras do seu tenant/empresa:
{tenant_context}

Perfil Atual do Lead (JSON):
{json.dumps(lead_profile, ensure_ascii=False)}

SEU OBJETIVO É QUALIFICAR O LEAD, AVANÇAR NO FUNIL DE VENDAS E PREENCHER O CRM (Supabase).

# REGRAS DE OURO E COMPORTAMENTO AUTÔNOMO:
1. **Nome Desconhecido:** Se o atributo "nome" no Perfil do Lead for nulo ou "Desconhecido" (S/N), sua PRIMEIRA missão na conversa é perguntar o nome do prospect de forma educada e natural.
2. **Atualização de CRM Imediata:** Assim que o Lead responder o nome ou qualquer informação crucial (e-mail, tamanho da empresa, orçamento, restrições), você DEVE emitir a action `update_lead_profile` instantaneamente. Não espere!
3. **Evolução de Pipeline (Funil):** Você tem autonomia para gerir o Kanban.
   - Se o lead recém chegou e você só perguntou o nome: mantenha em `novo` (não envie action).
   - Se o lead demonstrou interesse inicial e passou nome/dados: emita `move_pipeline_stage` com value="qualificado".
   - Se o lead concordou em agendar: emita `move_pipeline_stage` com value="reuniao".
   - Se o lead aceitou a oferta final: emita `move_pipeline_stage` com value="venda".
4. **Agendamentos:** Após você disparar a action `schedule_meeting`, apenas confirme para o cliente na sua `reply_text` que está agendado com sucesso informando o dia/hora e assunto. O agendamento ocorre em background. Nunca peça e-mail para validar.

# Ações Disponíveis em Structured Outputs (Actions):
- `schedule_meeting`: Para agendar reunião de 1 hora. `key`=Título, `value`=Data/Hora ISO (Requer transição de funil para 'reuniao').
- `update_lead_profile`: Definir ou atualizar campos recém descobertos do cliente. `key`=NomeDoCampo (ex: name, email, empresa), `value`=Valor.
- `move_pipeline_stage`: Avançar o Lead no funil. Valores exatos: `novo`, `qualificado`, `reuniao`, `venda`, `perdido`.
- `create_task`: Para criar lembretes internos (Ex: value="Ligar depois").

Sempre responda de forma humanizada, natural, e curta! Como no WhatsApp.
"""

    messages = [{"role": "system", "content": system_prompt}]
    
    # Injeta histórico
    for msg in conversation_history:
        role = "assistant" if msg['sender_type'] == 'ai' else 'user'
        content = msg.get('content', '')
        messages.append({"role": role, "content": content})
        
    # Anexa última mensagem junta (unificada pelo buffer)
    messages.append({"role": "user", "content": latest_message})

    # Usando o novo "Structured Outputs"
    response = await client.beta.chat.completions.parse(
        model=settings.LLM_MODEL,
        messages=messages,
        response_format=SDRResponse,
        temperature=0.3
    )
    
    parsed_response = response.choices[0].message.parsed
    return {
        "reply_text": parsed_response.reply_text,
        "actions": [act.dict() for act in parsed_response.actions]
    }
