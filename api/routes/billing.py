from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from core.database import get_db
from api.deps import get_current_user
from models.user import User
from models.lead import Lead
from models.tenant import Tenant
from services.asaas_service import get_or_create_asaas_customer, create_asaas_payment
from services.evolution_sender import send_whatsapp_message
from datetime import datetime, timedelta

router = APIRouter()

class ChargeRequest(BaseModel):
    lead_id: str
    value: float
    description: str
    due_date: Optional[str] = None # format YYYY-MM-DD

@router.post("/charge")
async def generate_charge(
    req: ChargeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Load Lead
        lead = db.query(Lead).filter(Lead.id == req.lead_id, Lead.tenant_id == current_user.tenant_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead não encontrado no seu tenant.")
            
        # Load Tenant
        tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
        
        # Check config
        integrations = tenant.integrations or {}
        if not integrations.get("asaas_api_key"):
            raise HTTPException(status_code=400, detail="Chave de API do Asaas não configurada. Peça ao Super Admin para configurar.")
            
        # Due Date Default to Today
        due_date = req.due_date
        if not due_date:
            due_date = datetime.now().strftime("%Y-%m-%d")

        # 1. Obter ou Criar Cliente no Asaas
        # Nome padrão se o lead não tiver nome
        customer_name = lead.name or f"Lead {lead.identifier}"
        # Se não tiver e-mail, usamos um email placeholder (Asaas precisa ou do email ou celular válido, mas um email fictício resolve)
        customer_email = lead.email or f"{lead.id}@borgesos.local"
        customer_phone = lead.phone
        
        # Limpar o phone para o Asaas (+55...)
        if customer_phone and customer_phone.startswith("+"):
            customer_phone = customer_phone[1:] # Asaas prefere sem o + na doc, mas varia.
            
        customer_id = await get_or_create_asaas_customer(
            tenant=tenant,
            name=customer_name,
            email=customer_email,
            phone=customer_phone
        )
        
        # 2. Criar Cobrança Pix/CreditCard genérica
        payment = await create_asaas_payment(
            tenant=tenant,
            customer_id=customer_id,
            value=req.value,
            description=req.description,
            due_date=due_date
        )
        
        # O invoiceUrl é o link completo para o cara pagar. O pixCopiaECola também é retornado para PIX dps.
        invoice_url = payment.get("invoiceUrl")
        
        # Enviar WhatsApp via Evolution se o tenant tiver instância e o lead tiver telefone
        if tenant.evolution_instance_id and lead.phone:
            remote_jid = lead.phone
            if not "@s.whatsapp.net" in remote_jid:
                remote_jid = f"{remote_jid}@s.whatsapp.net"
                
            msg_text = f"💳 *Nova Cobrança Gerada*\n\nOlá {customer_name},\nSegue o link para pagamento referente a: *{req.description}*.\n\nValor: R$ {req.value:.2f}\nVencimento: {due_date}\n\n👉 Acesse o link seguro para pagar via PIX, Boleto ou Cartão:\n{invoice_url}"
            
            # Integração Evolution
            await send_whatsapp_message(
                instance_name=tenant.evolution_instance_id,
                remote_jid=remote_jid,
                text=msg_text,
                evolution_url=integrations.get("evolution_api_url"),
                evolution_api_key=integrations.get("evolution_api_key")
            )
        
        return {
            "status": "success",
            "message": "Cobrança gerada com sucesso!",
            "data": {
                "invoiceUrl": invoice_url,
                "asaas_payment_id": payment.get("id"),
                "value": payment.get("value"),
                "dueDate": payment.get("dueDate"),
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
