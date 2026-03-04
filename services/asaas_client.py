import os
import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AsaasClient:
    def __init__(self):
        # Allow sandbox vs production via env var
        self.base_url = os.getenv("ASAAS_API_URL", "https://api-sandbox.asaas.com/v3")
        self.api_key = os.getenv("ASAAS_API_KEY", "")
        self.headers = {
            "access_token": self.api_key,
            "Content-Type": "application/json"
        }

    def _request(self, method: str, endpoint: str, data: dict = None) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            logger.warning("ASAAS_API_KEY não configurada. Simulando sucesso no mock Asaas.")
            return {"id": f"mock_{endpoint.replace('/', '_')}_{datetime.now().timestamp()}"}

        url = f"{self.base_url}/{endpoint}"
        try:
            with httpx.Client() as client:
                response = client.request(method, url, headers=self.headers, json=data)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro na API do Asaas [{e.response.status_code}]: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Erro de conexão com Asaas: {str(e)}")
            return None

    def create_customer(self, name: str, email: str, cpf_cnpj: str, phone: str = "") -> Optional[str]:
        """Cria um cliente no Asaas e retorna o customer_id"""
        payload = {
            "name": name,
            "email": email,
            "cpfCnpj": cpf_cnpj,
            "phone": phone,
            "notificationDisabled": False
        }
        res = self._request("POST", "customers", payload)
        return res.get("id") if res else None

    def create_subscription(self, customer_id: str, value: float, description: str = "Mensalidade SaaS") -> Optional[str]:
        """Cria uma assinatura mensal com cobrança via cartão, pix ou boleto (Asaas define o formato padrão)."""
        # Define next due date to today + 30 days
        next_due = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        payload = {
            "customer": customer_id,
            "billingType": "UNDEFINED", # Deixa o cliente escolher Pix, Cartão ou Boleto
            "value": value,
            "nextDueDate": next_due,
            "cycle": "MONTHLY",
            "description": description
        }
        res = self._request("POST", "subscriptions", payload)
        return res.get("id") if res else None

    def create_payment(self, customer_id: str, value: float, description: str = "Taxa de Implantação / Setup") -> Optional[str]:
        """Cria uma cobrança avulsa para pagamento único"""
        # Define due date to today + 3 days
        due_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")

        payload = {
            "customer": customer_id,
            "billingType": "UNDEFINED",
            "value": value,
            "dueDate": due_date,
            "description": description
        }
        res = self._request("POST", "payments", payload)
        return res.get("id") if res else None

asaas_client = AsaasClient()
