from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import func
from core.database import get_db
from models.tenant import Tenant
from api.deps import require_role
from typing import List, Optional
import httpx
from core.config import settings

router = APIRouter()

EVOLUTION_API_URL = "https://cosmicstarfish-evolution.cloudfy.live"
EVOLUTION_API_KEY = "bMQLdgHiveJZOejgVQqCMEY0zUSGalNh"

@router.post("/whatsapp/connect")
async def whatsapp_connect(data: dict = Body(...), db: Session = Depends(get_db)):
    tenant_id = data.get("tenant_id")
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    
    # Se o tenant já tem um ID de instância, tentamos usar ele, senão geramos um
    instance_name = tenant.evolution_instance_id if (tenant.evolution_instance_id and not tenant.evolution_instance_id.startswith('insta_')) else f"borges_{str(tenant_id)[:8]}"
    
    async with httpx.AsyncClient() as client:
        try:
            # 1. Tentar buscar a instância para ver se existe
            res = await client.get(
                f"{EVOLUTION_API_URL}/instance/fetchInstances",
                headers={"apikey": EVOLUTION_API_KEY},
                timeout=10.0
            )
            instances = res.json()
            existing = next((i for i in instances if i['name'] == instance_name), None)
            
            # 2. Se não existir, criar
            if not existing:
                create_res = await client.post(
                    f"{EVOLUTION_API_URL}/instance/create",
                    headers={"apikey": EVOLUTION_API_KEY, "Content-Type": "application/json"},
                    json={
                        "instanceName": instance_name,
                        "integration": "WHATSAPP-BAILEYS"
                    },
                    timeout=10.0
                )
            
            # 3. Gerar/Buscar QR Code
            qr_res = await client.get(
                f"{EVOLUTION_API_URL}/instance/connect/{instance_name}",
                headers={"apikey": EVOLUTION_API_KEY},
                timeout=15.0
            )
            if qr_res.status_code == 200:
                qr_data = qr_res.json()
                # Atualizar o evolution_instance_id no banco apenas se for o gerado agora
                tenant.evolution_instance_id = instance_name
                db.commit()
                
                return {
                    "status": "success",
                    "qrcode": qr_data.get("base64") or qr_data.get("code"),
                    "instance": instance_name
                }
            else:
                qr_data = qr_res.json()
                # Se já estiver aberto, retornar o status de conectado
                if qr_data.get("message") == "Connection is already open":
                    tenant.evolution_instance_id = instance_name
                    db.commit()
                    return {"status": "success", "message": "Conexão já estabelecida.", "instance": instance_name}
                
                return {"status": "error", "detail": qr_data.get("message", "Falha ao obter QR Code")}
                
        except Exception as e:
            raise HTTPException(status_code=500, detail="Falha na comunicação com Evolution API")

@router.post("/whatsapp/disconnect")
async def whatsapp_disconnect(data: dict = Body(...), db: Session = Depends(get_db)):
    tenant_id = data.get("tenant_id")
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    if tenant and tenant.evolution_instance_id:
        instance_name = tenant.evolution_instance_id
        async with httpx.AsyncClient() as client:
            try:
                await client.delete(
                    f"{EVOLUTION_API_URL}/instance/logout/{instance_name}",
                    headers={"apikey": EVOLUTION_API_KEY},
                    timeout=10.0
                )
                await client.delete(
                    f"{EVOLUTION_API_URL}/instance/delete/{instance_name}",
                    headers={"apikey": EVOLUTION_API_KEY},
                    timeout=10.0
                )
            except: pass
            
        tenant.whatsapp_number = "Aguardando Conexão"
        tenant.evolution_instance_id = None
        db.commit()
        
    return {"status": "success", "message": "Desconectado com sucesso."}

@router.post("/instagram/connect")
def instagram_connect(data: dict = Body(...), db: Session = Depends(get_db)):
    # Simula o início do fluxo de conexão
    tenant_id = data.get("tenant_id")
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if tenant:
        # Marcamos como 'pendente_insta' para o polling saber que iniciou
        tenant.evolution_instance_id = (tenant.evolution_instance_id or "") + "_pending_insta"
        db.commit()
        
    return {
        "status": "success", 
        "login_url": "https://www.instagram.com/accounts/login/",
        "message": "Redirecionando para login do Instagram."
    }

@router.post("/instagram/confirm")
def instagram_confirm(data: dict = Body(...), db: Session = Depends(get_db)):
    tenant_id = data.get("tenant_id")
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if tenant:
        # Marcamos como conectado de forma definitiva para o front-end reconhecer no F5
        tenant.evolution_instance_id = "insta_connected_" + str(tenant_id)[:8]
        # Atualizamos o campo integrations para persistir o estado
        integ = dict(tenant.integrations) if tenant.integrations else {}
        integ["instagram_connected"] = True
        tenant.integrations = integ
        db.commit()
        return {"status": "success", "message": "Instagram conectado com sucesso!"}
    raise HTTPException(status_code=404, detail="Tenant não encontrado")

@router.post("/tenants")
def create_tenant(
    data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["super_admin"]))
):
    import uuid as uuid_mod
    name = data.get("name")
    owner_name = data.get("owner_name", data.get("admin_name", "Administrador"))
    owner_email = data.get("owner_email", data.get("admin_email"))
    owner_phone = data.get("owner_phone", "")
    cnpj = data.get("cnpj", "")
    address = data.get("address", "")
    plan_value = data.get("plan_value", 0)
    setup_value = data.get("setup_value", 0)
    
    if not name or not owner_email:
        raise HTTPException(status_code=400, detail="Nome da empresa e email do responsável são obrigatórios")

    # Check if email already exists
    from models.user import User
    existing = db.query(User).filter(User.email == owner_email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Este email já está cadastrado no sistema")
        
    # 1. Criar Tenant com dados completos
    new_tenant = Tenant(
        name=name,
        billing_info={
            "cnpj": cnpj,
            "owner_name": owner_name,
            "owner_phone": owner_phone,
            "plan_value": plan_value,
            "setup_value": setup_value
        },
        knowledge_base={
            "physical_address": address
        }
    )
    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)
    
    # 2. Gerar token de convite
    invite_token = str(uuid_mod.uuid4())
    
    # 3. Criar Admin do Tenant (inativo até finalizar cadastro)
    from core.security import get_password_hash
    new_user = User(
        tenant_id=new_tenant.id,
        full_name=owner_name,
        email=owner_email,
        hashed_password=get_password_hash(str(uuid_mod.uuid4())),  # placeholder until registration
        role="company_admin",
        is_active=False,
        first_login=True,
        invite_token=invite_token
    )
    db.add(new_user)
    db.commit()
    
    # 4. Tentar enviar email de convite
    invite_url = f"/register?token={invite_token}"
    email_sent = False
    try:
        from services.email_service import send_invite_email
        email_sent = send_invite_email(owner_email, owner_name, name, invite_url)
    except Exception as e:
        print(f"Email não enviado (configure SMTP no .env): {e}")
    
    return {
        "status": "success", 
        "message": f"Empresa '{name}' criada com sucesso!",
        "tenant_id": str(new_tenant.id),
        "invite_url": invite_url,
        "invite_token": invite_token,
        "email_sent": email_sent
    }

@router.post("/tenants/{tenant_id}/resend-invite")
def resend_invite(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["super_admin"]))
):
    """Reenvia o email de convite para o admin da empresa."""
    import uuid as uuid_mod
    from models.user import User
    
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    
    # Buscar o admin do tenant
    admin_user = db.query(User).filter(
        User.tenant_id == tenant_id,
        User.role == "company_admin"
    ).first()
    
    if not admin_user:
        raise HTTPException(status_code=404, detail="Admin da empresa não encontrado")
    
    # Se o user já está ativo, não precisa de convite
    if admin_user.is_active and not admin_user.invite_token:
        return {
            "status": "info",
            "message": "Este usuário já ativou a conta. Não é necessário reenviar convite.",
            "email": admin_user.email
        }
    
    # Gerar novo token se não tiver ou o antigo já foi usado
    if not admin_user.invite_token:
        admin_user.invite_token = str(uuid_mod.uuid4())
        admin_user.is_active = False
        db.commit()
    
    invite_url = f"/register?token={admin_user.invite_token}"
    
    # Tentar enviar email
    email_sent = False
    try:
        from services.email_service import send_invite_email
        owner_name = admin_user.full_name or "Administrador"
        email_sent = send_invite_email(admin_user.email, owner_name, tenant.name, invite_url)
    except Exception as e:
        print(f"Erro ao reenviar email: {e}")
    
    return {
        "status": "success",
        "message": f"Convite reenviado para {admin_user.email}!",
        "invite_url": invite_url,
        "invite_token": admin_user.invite_token,
        "email_sent": email_sent
    }

@router.put("/tenants/{tenant_id}/edit")
def edit_tenant(
    tenant_id: str,
    data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["super_admin"]))
):
    """Edita os dados cadastrais da empresa (nome, dono, CNPJ, etc)."""
    from models.user import User
    
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    
    # Atualizar nome da empresa
    if data.get("name"):
        tenant.name = data["name"]
    
    # Atualizar billing_info (CNPJ, telefone, etc)
    billing = dict(tenant.billing_info) if tenant.billing_info else {}
    if "cnpj" in data: billing["cnpj"] = data["cnpj"]
    if "owner_name" in data: billing["owner_name"] = data["owner_name"]
    if "owner_phone" in data: billing["owner_phone"] = data["owner_phone"]
    if "plan_value" in data: billing["plan_value"] = data["plan_value"]
    if "setup_value" in data: billing["setup_value"] = data["setup_value"]
    tenant.billing_info = billing
    
    # Atualizar endereço no knowledge_base
    if "address" in data:
        kb = dict(tenant.knowledge_base) if tenant.knowledge_base else {}
        kb["physical_address"] = data["address"]
        tenant.knowledge_base = kb
    
    # Atualizar dados do admin user (nome e email)
    admin_user = db.query(User).filter(
        User.tenant_id == tenant_id,
        User.role == "company_admin"
    ).first()
    
    if admin_user:
        if data.get("owner_name"):
            admin_user.full_name = data["owner_name"]
        if data.get("owner_email") and data["owner_email"] != admin_user.email:
            # Verificar se o novo email já existe
            existing = db.query(User).filter(User.email == data["owner_email"]).first()
            if existing and existing.id != admin_user.id:
                raise HTTPException(status_code=400, detail="Este email já está em uso")
            admin_user.email = data["owner_email"]
    
    db.commit()
    
    return {
        "status": "success",
        "message": f"Dados da empresa '{tenant.name}' atualizados!"
    }

@router.get("/tenants/{tenant_id}")
async def get_tenant_detail(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["super_admin"]))
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    
    # [FIX] Sincronizar status real com a Evolution API antes de retornar os detalhes
    if tenant.evolution_instance_id and not tenant.evolution_instance_id.startswith('insta_'):
        async with httpx.AsyncClient() as client:
            try:
                res = await client.get(
                    f"{EVOLUTION_API_URL}/instance/connectionState/{tenant.evolution_instance_id}",
                    headers={"apikey": EVOLUTION_API_KEY},
                    timeout=5.0
                )
                if res.status_code == 200:
                    state_data = res.json()
                    status = state_data.get("instance", {}).get("state")
                    if status == "open":
                        # Se na Evolution está aberto mas no banco não tem o número, tentamos pegar o número
                        if not tenant.whatsapp_number or tenant.whatsapp_number == "Aguardando Conexão":
                            res_info = await client.get(
                                f"{EVOLUTION_API_URL}/instance/fetchInstances",
                                headers={"apikey": EVOLUTION_API_KEY}
                            )
                            instances = res_info.json()
                            this_inst = next((i for i in instances if i['name'] == tenant.evolution_instance_id), None)
                            if this_inst and this_inst.get('ownerJid'):
                                tenant.whatsapp_number = this_inst['ownerJid'].split('@')[0]
                                db.commit()
            except Exception as e:
                print(f"Sync Status Error: {e}")

    # Adicionando métricas reais para o detalhe
    from models.lead import Lead
    from models.user import User
    total_leads = db.query(func.count(Lead.id)).filter(Lead.tenant_id == tenant.id).scalar() or 0
    hot_leads = db.query(func.count(Lead.id)).filter(Lead.tenant_id == tenant.id, Lead.temperature == "quente").scalar() or 0
    estimated_revenue = db.query(func.sum(Lead.estimated_value)).filter(Lead.tenant_id == tenant.id).scalar() or 0.0

    # Buscar admin do tenant para retornar email
    admin_user = db.query(User).filter(
        User.tenant_id == tenant.id,
        User.role == "company_admin"
    ).first()

    return {
        "status": "success",
        "data": {
            "id": str(tenant.id),
            "name": tenant.name,
            "whatsapp_number": tenant.whatsapp_number or "Aguardando Conexão",
            "evolution_instance_id": tenant.evolution_instance_id,
            "instagram_connected": False,
            "admin_email": admin_user.email if admin_user else "",
            "admin_name": admin_user.full_name if admin_user else "",
            "invite_pending": bool(admin_user and admin_user.invite_token),
            "metrics": {
                "total_leads": total_leads,
                "hot_leads": hot_leads,
                "estimated_revenue": float(estimated_revenue)
            },
            "billing_info": tenant.billing_info or {},
            "ai_config": tenant.ai_config or {},
            "knowledge_base": tenant.knowledge_base or {},
            "integrations": tenant.integrations or {}
        }
    }

@router.put("/tenants/{tenant_id}/config")
def update_tenant_config_super(
    tenant_id: str,
    data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["super_admin"]))
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    
    # Atualizar campos principais
    if "whatsapp_number" in data:
        tenant.whatsapp_number = data["whatsapp_number"]
    if "sla_hours" in data:
        tenant.sla_hours = data["sla_hours"]
    if "meta_pixel_id" in data:
        tenant.meta_pixel_id = data["meta_pixel_id"]
    if "meta_capi_token" in data:
        tenant.meta_capi_token = data["meta_capi_token"]
        
    # Atualizar JSONs
    # Billing
    billing_fields = ["cnpj", "email", "plan_value", "setup_value", "due_date"]
    current_billing = dict(tenant.billing_info) if tenant.billing_info else {}
    for f in billing_fields:
        if f in data: current_billing[f] = data[f]
    tenant.billing_info = current_billing
    
    # AI Config
    ai_fields = ["agent_name", "agent_tone", "agent_goal", "system_prompt", "auto_audio"]
    current_ai = dict(tenant.ai_config) if tenant.ai_config else {}
    for f in ai_fields:
        if f in data: current_ai[f] = data[f]
    tenant.ai_config = current_ai
    
    # Knowledge Base
    kb_fields = [
        "company_name", "products_services", "address", "business_hours",
        "faq", "pricing", "differentials", "extra_instructions",
        # compat legado
        "business_niche", "working_hours", "physical_address", "objection_handling"
    ]
    current_kb = dict(tenant.knowledge_base) if tenant.knowledge_base else {}
    for f in kb_fields:
        if f in data: current_kb[f] = data[f]
    tenant.knowledge_base = current_kb
    
    # Integrations (API KEYS)
    integ_fields = ["evolution_api_url", "evolution_api_key", "openai_api_key", "asaas_api_key", "llm_model"]
    current_integ = dict(tenant.integrations) if tenant.integrations else {}
    for f in integ_fields:
        if f in data: current_integ[f] = data[f]
    tenant.integrations = current_integ
    
    db.commit()
    return {"status": "success", "message": "Configurações do Tenant atualizadas"}

@router.get("/tenants")
def list_tenants(
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["super_admin"]))
):
    try:
        tenants = db.query(Tenant).all()
        
        total_mrr = 0.0
        total_setup = 0.0
        
        tenant_list = []
        for t in tenants:
            # Pegar valores das colunas dinamicamente
            mrr = 0.0
            setup = 0.0
            
            try:
                if hasattr(t, 'plan_value'):
                    mrr = float(t.plan_value or 0)
                if hasattr(t, 'setup_value'):
                    setup = float(t.setup_value or 0)
            except:
                pass
                
            if mrr == 0 and t.billing_info and isinstance(t.billing_info, dict):
                mrr = float(t.billing_info.get("plan_value", 0))
                setup = float(t.billing_info.get("setup_value", 0))
            
            total_mrr += mrr
            total_setup += setup
            
            tenant_list.append({
                "id": str(t.id),
                "name": t.name,
                "whatsapp_number": t.whatsapp_number or "Aguardando Conexão",
                "evolution_instance_id": t.evolution_instance_id,
                "plan_value": mrr,
                "setup_value": setup
            })
        
        return {
            "status": "success",
            "data": tenant_list,
            "aggregates": {
                "total_tenants": len(tenants),
                "total_mrr": total_mrr,
                "total_setup": total_setup
            }
        }
    except Exception as e:
        print(f"CRITICAL ERROR IN SUPER ADMIN: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
