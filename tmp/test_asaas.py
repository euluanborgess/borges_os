import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database import SessionLocal
from models.tenant import Tenant
from models.lead import Lead
from models.user import User
from services.asaas_service import get_or_create_asaas_customer, create_asaas_payment

async def test_asaas_integration():
    db = SessionLocal()
    try:
        # Pega o primeiro tenant que tem chave do Asaas
        tenant = db.query(Tenant).filter(Tenant.integrations.op('->>')('asaas_api_key') != None).first()
        
        if not tenant:
            print("❌ Nenhum Tenant encontrado com Chave de API do Asaas configurada no JSON integrations.")
            print("Para testar, configure no banco de dados primeiro.")
            return

        print(f"✅ Usando Tenant: {tenant.name} (ID: {tenant.id})")
        api_key = tenant.integrations.get('asaas_api_key')
        print(f"🔑 Chave Asaas encontrada: {api_key[:10]}...")

        # Pega ou cria um lead fake para testar
        lead = db.query(Lead).filter(Lead.tenant_id == tenant.id).first()
        if not lead:
            print("⚠️ Criando um lead de teste no banco...")
            lead = Lead(
                tenant_id=tenant.id,
                name="Cliente Teste Asaas API",
                phone="5511999999999",
                email="teste.venda.asaas@borgesos.local"
            )
            db.add(lead)
            db.commit()
            db.refresh(lead)

        print(f"👤 Usando Lead: {lead.name} (ID: {lead.id})")

        print("\n--- TESTE 1: CRIAR/BUSCAR CLIENTE NO ASAAS ---")
        customer_id = await get_or_create_asaas_customer(
            tenant=tenant,
            name=lead.name,
            email=lead.email,
            phone=lead.phone
        )
        print(f"✅ Cliente Asaas Retornado/Criado ID: {customer_id}")

        print("\n--- TESTE 2: GERAR COBRANÇA (PIX/BOLETO) DE R$ 1,00 ---")
        payment = await create_asaas_payment(
            tenant=tenant,
            customer_id=customer_id,
            value=1.00,
            description="Teste Integração Borges OS V2",
            due_date="2026-12-31"
        )
        print(f"✅ Fatura Asaas Gerada!")
        print(f"📄 ID do Pagamento: {payment.get('id')}")
        print(f"🔗 Link de Pagamento (InvoiceUrl): {payment.get('invoiceUrl')}")
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE O TESTE:\n{e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_asaas_integration())
