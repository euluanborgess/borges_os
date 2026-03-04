from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.database import get_db
from models import Tenant, User, Lead
from api.deps import get_current_user, require_role
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy import func
from passlib.context import CryptContext
from sqlalchemy.orm.attributes import flag_modified
from services.asaas_client import asaas_client
import httpx
import logging
import os

router = APIRouter()
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class TenantCreateInput(BaseModel):
    name: str
    admin_email: EmailStr
    admin_password: str
    admin_name: str

class EvolutionConnectInput(BaseModel):
    tenant_id: str

class TenantConfigUpdateInput(BaseModel):
    system_prompt: Optional[str] = None
    whatsapp_number: Optional[str] = None
    sla_hours: Optional[int] = None
    
    # Billing
    cnpj: Optional[str] = None
    email: Optional[str] = None
    plan_value: Optional[float] = None
    setup_value: Optional[float] = None
    due_date: Optional[int] = None
    
    # AI Persona
    agent_name: Optional[str] = None
    agent_tone: Optional[str] = None
    agent_goal: Optional[str] = None
    
    # Knowledge Base
    business_niche: Optional[str] = None
    working_hours: Optional[str] = None
    physical_address: Optional[str] = None
    products_services: Optional[str] = None
    objection_handling: Optional[str] = None
    
    # Integrations
    evolution_api_url: Optional[str] = None
    evolution_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

@router.post("/tenants", status_code=status.HTTP_201_CREATED)
def create_new_tenant(
    payload: TenantCreateInput, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role(["super_admin"]))
):
    """
    Onboarding de nova empresa. Cria o Tenant e o seu primeiro usuário Administrador.
    """
    # 1. Verificar se o e-mail do admin já existe globalmente
    existing_user = db.query(User).filter(User.email == payload.admin_email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Este e-mail já está em uso no sistema.")

    # 2. Criar a nova empresa (Tenant)
    new_tenant = Tenant(
        name=payload.name,
        whatsapp_number="Aguardando Conexão"
    )
    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)

    # 3. Criar o Vendedor Gestor (Tenant Admin)
    hashed_password = pwd_context.hash(payload.admin_password)
    new_admin = User(
        tenant_id=new_tenant.id,
        email=payload.admin_email,
        full_name=payload.admin_name,
        hashed_password=hashed_password,
        role="tenant_admin",
        is_active=True
    )
    db.add(new_admin)
    db.commit()
    
    # 4. (Opcional) Poderíamos injetar um Pipeline/Leads padrão aqui.

    return {
        "status": "success", 
        "message": f"Empresa '{payload.name}' criada com sucesso!",
        "tenant_id": new_tenant.id
    }

@router.get("/tenants")
def list_all_tenants(
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role(["super_admin"]))
):
    """
    Lista todas as empresas do SaaS para o Dashboard do Super Admin.
    """
    tenants = db.query(Tenant).all()
    results = []
    
    total_mrr = 0.0
    total_setup = 0.0
    
    for t in tenants:
        billing = t.billing_info or {}
        p_val = float(billing.get("plan_value", 0) or 0)
        s_val = float(billing.get("setup_value", 0) or 0)
        
        # MRR/ARR is global always
        total_mrr += p_val
        
        # Setup is strictly temporal (if filter provided)
        include_setup = True
        if month and year and t.created_at:
            if t.created_at.month != month or t.created_at.year != year:
                include_setup = False
                
        if include_setup:
            total_setup += s_val
        
        results.append({
            "id": t.id,
            "name": t.name,
            "whatsapp_number": t.whatsapp_number,
            "plan_value": p_val,
            "setup_value": s_val,
            "created_at": t.created_at.isoformat() if t.created_at else None
        })
        
    return {
        "status": "success", 
        "data": results,
        "aggregates": {
            "total_mrr": total_mrr,
            "total_setup": total_setup,
            "total_tenants": len(tenants)
        }
    }


@router.get("/tenants/{tenant_id}")
def get_tenant_details(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["super_admin"]))
):
    """
    Retorna os detalhes precisos de uma empresa cliente.
    (Métricas, prompts de IA, configs diversas).
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    # Metrics
    total_leads = db.query(func.count(Lead.id)).filter(Lead.tenant_id == tenant_id).scalar() or 0
    hot_leads = db.query(func.count(Lead.id)).filter(Lead.tenant_id == tenant_id, Lead.temperature == 'quente').scalar() or 0

    return {
        "status": "success",
        "data": {
            "id": tenant.id,
            "name": tenant.name,
            "whatsapp_number": tenant.whatsapp_number,
            "ai_config": tenant.ai_config or {},
            "knowledge_base": tenant.knowledge_base or {},
            "billing_info": tenant.billing_info or {},
            "integrations": tenant.integrations or {},
            "sla_hours": tenant.sla_hours,
            "metrics": {
                "total_leads": total_leads,
                "hot_leads": hot_leads,
                "estimated_revenue": hot_leads * 150  # Mock logic for UI
            }
        }
    }


@router.put("/tenants/{tenant_id}/config")
def update_tenant_config(
    tenant_id: str,
    payload: TenantConfigUpdateInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["super_admin"]))
):
    """
    Atualiza as chaves da API e o prompt Global da IA para uma empresa específica.
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    if payload.whatsapp_number is not None:
        tenant.whatsapp_number = payload.whatsapp_number
    if payload.sla_hours is not None:
        tenant.sla_hours = payload.sla_hours
    
    ai_c = tenant.ai_config or {}
    kb = tenant.knowledge_base or {}
    bill = tenant.billing_info or {}
    integ = tenant.integrations or {}

    # AI Persona updates
    if payload.system_prompt is not None: ai_c["system_prompt"] = payload.system_prompt
    if payload.agent_name is not None: ai_c["agent_name"] = payload.agent_name
    if payload.agent_tone is not None: ai_c["agent_tone"] = payload.agent_tone
    if payload.agent_goal is not None: ai_c["agent_goal"] = payload.agent_goal

    # Knowledge Base updates
    if payload.business_niche is not None: kb["business_niche"] = payload.business_niche
    if payload.working_hours is not None: kb["working_hours"] = payload.working_hours
    if payload.physical_address is not None: kb["physical_address"] = payload.physical_address
    if payload.products_services is not None: kb["products_services"] = payload.products_services
    if payload.objection_handling is not None: kb["objection_handling"] = payload.objection_handling

    # Billing updates
    if payload.cnpj is not None: bill["cnpj"] = payload.cnpj
    if payload.email is not None: bill["email"] = payload.email
    if payload.plan_value is not None: bill["plan_value"] = payload.plan_value
    if payload.setup_value is not None: bill["setup_value"] = payload.setup_value
    if payload.due_date is not None: bill["due_date"] = payload.due_date

    # Integration updates
    if payload.evolution_api_url is not None: integ["evolution_api_url"] = payload.evolution_api_url
    if payload.evolution_api_key is not None: integ["evolution_api_key"] = payload.evolution_api_key
    if payload.openai_api_key is not None: integ["openai_api_key"] = payload.openai_api_key

    # Reassign JSON clones to trigger SQLAlchemy change tracking
    tenant.ai_config = ai_c.copy()
    tenant.knowledge_base = kb.copy()
    tenant.billing_info = bill.copy()
    tenant.integrations = integ.copy()
    
    flag_modified(tenant, "ai_config")
    flag_modified(tenant, "knowledge_base")
    flag_modified(tenant, "billing_info")
    flag_modified(tenant, "integrations")

    db.commit()
    
    return {
        "status": "success",
        "message": "Configurações da empresa atualizadas."
    }

@router.post("/tenants/{tenant_id}/asaas/generate")
def generate_asaas_billing(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["super_admin"]))
):
    """
    Cria Cliente, Assinatura (MRR) e Cobrança Avulsa (Setup) no Asaas.
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")

    bill = tenant.billing_info or {}
    email = bill.get("email")
    if not email:
        raise HTTPException(400, "O e-mail do cliente é obrigatório para gerar faturas interligadas com o Asaas.")

    # 1. Get or Create Asaas Customer
    customer_id = bill.get("asaas_customer_id")
    if not customer_id:
        customer_id = asaas_client.create_customer(
            name=tenant.name,
            email=email,
            cpf_cnpj=bill.get("cnpj", ""),
            phone=tenant.whatsapp_number
        )
        if not customer_id:
            raise HTTPException(500, "Falha na comunicação com o Asaas Client para criar o Assinante.")
            
        bill["asaas_customer_id"] = customer_id
        tenant.billing_info = bill.copy()
        flag_modified(tenant, "billing_info")
        db.commit()

    # 2. Create MRR Subscription
    plan_val = float(bill.get("plan_value", 0) or 0)
    if plan_val > 0 and not bill.get("asaas_subscription_id"):
        sub_id = asaas_client.create_subscription(customer_id, plan_val)
        if sub_id:
            bill["asaas_subscription_id"] = sub_id
            tenant.billing_info = bill.copy()
            flag_modified(tenant, "billing_info")
            db.commit()

    # 3. Create One-Off Setup Charge
    setup_val = float(bill.get("setup_value", 0) or 0)
    if setup_val > 0 and not bill.get("asaas_setup_payment_id"):
        pay_id = asaas_client.create_payment(customer_id, setup_val)
        if pay_id:
            bill["asaas_setup_payment_id"] = pay_id
            tenant.billing_info = bill.copy()
            flag_modified(tenant, "billing_info")
            db.commit()

    return {
        "status": "success", 
        "message": "Cobranças geradas e sincronizadas com o Asaas via API!"
    }

@router.post("/whatsapp/connect")
async def connect_whatsapp_evolution(
    payload: EvolutionConnectInput, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role(["super_admin"]))
):
    """
    Consome a Evolution API para criar a instância (se não existir) e pedir o QRCode Base64.
    """
    tenant = db.query(Tenant).filter(Tenant.id == payload.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")

    # Integration Fields
    integ = tenant.integrations or {}
    
    # Evolution API REAL INTEGRATION
    # Pull specific tenant configs first, fallback to global defaults only if missing
    raw_url = integ.get("evolution_api_url") or os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
    raw_key = integ.get("evolution_api_key") or os.getenv("EVOLUTION_API_KEY", "global-api-key-evolution")
    
    # Clean up any trailing/leading whitespace and slashes from UI inputs
    EVOLUTION_URL = raw_url.strip().rstrip('/')
    EVOLUTION_GLOBAL_KEY = raw_key.strip()
    
    instance_name = f"borges_{tenant.id[0:8]}" 
    headers = {"apikey": EVOLUTION_GLOBAL_KEY}
    
    print("====== DEBUG EVOLUTION API CONNECT ======")
    print(f"URL: [{EVOLUTION_URL}]")
    print(f"KEY: [{EVOLUTION_GLOBAL_KEY}]")
    print(f"TENANT INTEGRATIONS JSON: {integ}")
    print("=========================================")
    
    import httpx
    
    # Evolution API initialization can be slow (spins up baileys engine)
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # 1. Tentar criar a instância (ignora se ja existir)
            create_res = await client.post(
                f"{EVOLUTION_URL}/instance/create",
                json={
                    "instanceName": instance_name, 
                    "token": instance_name,
                    "qrcode": True,
                    "integration": "WHATSAPP-BAILEYS",
                    "webhook": {
                        "enabled": True,
                        "url": f"http://host.docker.internal:8000/api/v1/webhooks/evolution",
                        "webhookByEvents": False,
                        "webhookBase64": False,
                        "events": ["MESSAGES_UPSERT", "CONNECTION_UPDATE"]
                    }
                },
                headers=headers
            )
            
            if create_res.status_code == 401:
                raise HTTPException(status_code=400, detail="Chave da Evolution API Recusada (Global/Apikey Inválida).")
            elif create_res.status_code == 403:
                # 403 pode significar "Forbidden" por apiKey errada, OU "Route is already in use"
                if "already in use" not in create_res.text.lower():
                    raise HTTPException(status_code=400, detail="Chave da Evolution API Recusada (Global/Apikey Inválida).")
                # Se for already in use, apenas ignora e segue para o step 2
                
            # 2. Requisitar o Base64 do QR Code para conexão
            response = await client.get(
                f"{EVOLUTION_URL}/instance/connect/{instance_name}",
                headers=headers
            )
            data = response.json()
            
            if response.status_code not in [200, 201]:
                errmsg = data.get("error", "Erro ao conectar") if isinstance(data, dict) else str(data)
                raise HTTPException(status_code=400, detail=f"Evolution API Retornou: {errmsg}")
                
            # 3. Retornar QR Code Base64
            if "base64" in data:
                 return {
                     "status": "success", 
                     "message": "Evolution API chamada com sucesso.",
                     "qrcode": data["base64"], 
                     "instance": instance_name
                 }
            else:
                # Já conectada? Vamos tentar buscar o JID (número) que a Evolution salvou
                 profile_num = None
                 try:
                     inst_res = await client.get(
                         f"{EVOLUTION_URL}/instance/fetchInstances?instanceName={instance_name}",
                         headers=headers
                     )
                     inst_data = inst_res.json()
                     if inst_data and isinstance(inst_data, list):
                         owner_jid = inst_data[0].get("ownerJid", "")
                         if owner_jid:
                             profile_num = owner_jid.split("@")[0]
                             tenant.whatsapp_number = profile_num
                             
                 except Exception as e:
                     print("AVISO: Falha ao buscar número da instância conectada:", e)

                 # Salva as info importantes do webhook / connection no DB
                 tenant.evolution_instance_id = instance_name
                 db.commit()

                 msg = f"Conectado com sucesso! ({profile_num})" if profile_num else "Instância já estabelecida ou QR Code indisponível."
                 return {
                     "status": "success", 
                     "qrcode": None, 
                     "message": msg,
                     "whatsapp_number": profile_num
                 }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Falha ao conectar na Evolution API: {str(e)}")
