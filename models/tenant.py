from sqlalchemy import Column, String, DateTime, Integer, JSON
from sqlalchemy.sql import func
import uuid
from models.base import Base

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    evolution_instance_id = Column(String, nullable=True) # Ligação com a instância do WhatsApp
    
    # NOVOS CAMPOS ADICIONADOS PARA A PÁGINA DE CONFIGURAÇÕES (BASE44 MIGRAÇÃO)
    whatsapp_number = Column(String, nullable=True)
    sla_hours = Column(Integer, default=24)
    welcome_message = Column(String, nullable=True)
    ai_config = Column(JSON, nullable=True) # AI Persona & Tone
    knowledge_base = Column(JSON, nullable=True) # Corporate info, address, products
    billing_info = Column(JSON, nullable=True) # CNPJ, Plan Value, Due Date
    score_weights = Column(JSON, nullable=True)
    contract_template = Column(String, nullable=True)
    integrations = Column(JSON, nullable=True)
    plan_limits = Column(JSON, nullable=True)
    quick_replies = Column(JSON, nullable=True) # Catálogo de respostas rápidas do WhatsApp/Inbox
    
    # [META ADS CAPI] Integração de Pixel Server-Side
    meta_pixel_id = Column(String, nullable=True)
    meta_capi_token = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
