from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from models import Tenant, User
from api.deps import get_current_user
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx
import asyncio
from core.config import settings

router = APIRouter()

class AIConfigInput(BaseModel):
    greeting_message: Optional[str] = None
    tone: Optional[str] = None
    auto_schedule: Optional[bool] = None

class TenantUpdateInput(BaseModel):
    name: Optional[str] = None
    whatsapp_number: Optional[str] = None
    sla_hours: Optional[int] = None
    welcome_message: Optional[str] = None
    ai_config: Optional[AIConfigInput] = None
    quick_replies: Optional[list[str]] = None
    # We can expand score_weights, integrations, etc as needed

@router.get("/")
async def get_tenant_config(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Returns the tenant/company configuration for the settings dashboard.
    """
    tenant_id = current_user.tenant_id
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
        
    # Auto-sync whatsapp status from Evolution API since webhooks might fail on localhost
    if tenant.evolution_instance_id and (not tenant.whatsapp_number or tenant.whatsapp_number in ["Aguardando Conexão", "Pendente"]):
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(
                    f"{settings.EVOLUTION_API_URL}/instance/fetchInstances",
                    headers={"apikey": settings.EVOLUTION_API_KEY},
                    timeout=5.0
                )
                if res.status_code == 200:
                    instances = res.json()
                    inst = next((i for i in instances if i.get("name") == tenant.evolution_instance_id), None)
                    if inst and inst.get("connectionStatus") == "open":
                        owner = inst.get("ownerJid", "")
                        if owner and "@" in owner:
                            tenant.whatsapp_number = owner.split("@")[0]
                            db.commit()
        except:
            pass

    return {
        "id": tenant.id,
        "name": tenant.name,
        "whatsapp_number": tenant.whatsapp_number,
        "sla_hours": tenant.sla_hours,
        "ai_config": tenant.ai_config or {
            "greeting_message": "Olá! Sou o assistente comercial da empresa.",
            "tone": "consultivo"
        },
        "score_weights": tenant.score_weights,
        "welcome_message": tenant.welcome_message,
        "contract_template": tenant.contract_template,
        "integrations": tenant.integrations,
        "plan_limits": tenant.plan_limits,
        "quick_replies": tenant.quick_replies or []
    }

@router.put("/")
def update_tenant_config(payload: TenantUpdateInput, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Updates the tenant/company configuration from the settings dashboard.
    """
    tenant_id = current_user.tenant_id
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
        
    if payload.name is not None:
        tenant.name = payload.name
    if payload.whatsapp_number is not None:
        tenant.whatsapp_number = payload.whatsapp_number
    if payload.sla_hours is not None:
        tenant.sla_hours = payload.sla_hours
    if payload.welcome_message is not None:
        tenant.welcome_message = payload.welcome_message
    if payload.quick_replies is not None:
        tenant.quick_replies = payload.quick_replies
        
    # Merge nested JSON objects
    if payload.ai_config is not None:
        current_ai = tenant.ai_config or {}
        new_ai = payload.ai_config.dict(exclude_unset=True)
        tenant.ai_config = {**current_ai, **new_ai}

    db.commit()
    db.refresh(tenant)
    return {"status": "success", "message": "Configurações atualizadas com sucesso."}
