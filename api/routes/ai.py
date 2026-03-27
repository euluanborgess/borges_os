from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from models import Lead, User, Contract, Event, Task
from api.deps import get_current_user
from services.llm_engine import _get_client
from core.config import settings
import json

router = APIRouter()

@router.post("/strategic-analysis")
async def strategic_analysis(
    prompt: str, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Realiza uma análise estratégica baseada nos dados do Tenant.
    """
    tenant_id = current_user.tenant_id
    
    # Coletar dados para o contexto
    leads = db.query(Lead).filter(Lead.tenant_id == tenant_id).all()
    contracts = db.query(Contract).filter(Contract.tenant_id == tenant_id).all()
    tasks = db.query(Task).filter(Task.tenant_id == tenant_id, Task.is_completed == False).all()
    
    context = {
        "total_leads": len(leads),
        "leads": [
            {"name": l.name, "phone": l.phone, "stage": l.pipeline_stage, "temp": l.temperature, "value": l.estimated_value}
            for l in leads
        ],
        "total_contracts": len(contracts),
        "contracts": [
            {"title": c.title, "value": c.value, "status": c.status}
            for c in contracts
        ],
        "pending_tasks": [
            {"title": t.title, "priority": t.priority}
            for t in tasks
        ]
    }

    system_prompt = f"""
Você é o Borges IA, Chief Intelligence Officer do sistema Borges OS.
Sua persona é inspirada em um assistente de elite estilo "Jarvis" ou "Friday".
Você fala de forma educada, eficiente e altamente inteligente. 
Sempre chame o usuário de "Senhor" ou "Senhora".

Sua missão é fornecer insights estratégicos e análises de dados para o gestor.
Aqui estão os dados atuais da operação (JSON):
{json.dumps(context, ensure_ascii=False)}

Ao responder:
1. Comece com uma saudação formal: "Olá Senhor/Senhora, preparei estas informações sobre sua operação."
2. Analise os pontos críticos (leads frios, metas de receita, tarefas atrasadas).
3. Seja tático e orientado a resultados.
4. Use formatação Markdown (negrito, listas, tabelas se necessário) para destacar pontos importantes.
"""

    try:
        print(f"[AI Analysis] Processing prompt for tenant {tenant_id}")
        client = _get_client()
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        print(f"[AI Analysis] Success")
        return {"status": "success", "response": response.choices[0].message.content}
    except Exception as e:
        import traceback
        print(f"AI Analysis Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao processar análise estratégica: {str(e)}")
