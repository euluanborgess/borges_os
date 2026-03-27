import os
import httpx
from datetime import datetime
from models.tenant import Tenant

ASAAS_BASE_URL = os.getenv("ASAAS_BASE_URL", "https://sandbox.asaas.com/api/v3")

async def get_or_create_asaas_customer(tenant: Tenant, name: str, email: str, phone: str = None) -> str:
    """Gets or creates a customer in Asaas and returns their internal customer_id (cus_...)"""
    integrations = tenant.integrations or {}
    api_key = integrations.get("asaas_api_key")
    if not api_key:
        raise ValueError("Tenant não possui Asaas API Key configurada.")
        
    headers = {
        "access_token": api_key,
        "Content-Type": "application/json"
    }
    
    # 1. Tenta buscar pelo email ou telefone
    async with httpx.AsyncClient() as client:
        # Search by email first
        res = await client.get(f"{ASAAS_BASE_URL}/customers?email={email}", headers=headers)
        if res.status_code == 200:
            data = res.json()
            if data.get("data") and len(data["data"]) > 0:
                return data["data"][0]["id"]
                
        # 2. Se não achou, cria
        payload = {
            "name": name,
            "email": email,
            "mobilePhone": phone,
            "notificationDisabled": False
        }
        
        res_create = await client.post(f"{ASAAS_BASE_URL}/customers", json=payload, headers=headers)
        
        if res_create.status_code in [200, 201]:
            new_customer = res_create.json()
            return new_customer["id"]
        else:
            raise Exception(f"Erro ao criar cliente no Asaas: {res_create.text}")


async def create_asaas_payment(tenant: Tenant, customer_id: str, value: float, description: str, due_date: str) -> dict:
    """Creates a Pix/Credit Card payment link for the customer"""
    integrations = tenant.integrations or {}
    api_key = integrations.get("asaas_api_key")
    if not api_key:
        raise ValueError("Tenant não possui Asaas API Key configurada.")
        
    headers = {
        "access_token": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "customer": customer_id,
        "billingType": "UNDEFINED", # Lets user choose Pix, Boleto or Credit Card
        "value": value,
        "dueDate": due_date,
        "description": description
    }
    
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{ASAAS_BASE_URL}/payments", json=payload, headers=headers)
        if res.status_code in [200, 201]:
            return res.json()
        else:
            raise Exception(f"Erro ao criar cobrança no Asaas: {res.text}")
