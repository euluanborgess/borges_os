from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from models.base import Base

class Lead(Base):
    __tablename__ = "leads"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    
    name = Column(String, nullable=True)
    phone = Column(String, nullable=False, index=True) # Número WhatsApp
    
    # Classificações da IA
    temperature = Column(String, default="frio") # frio, morno, quente
    score = Column(Integer, default=0)
    tags = Column(JSON, default=list) # ["urgente", "preco"]
    
    # CRM Profile construído pela IA no decorrer da conversa
    profile_data = Column(JSON, default=dict) # {"empresa": "X", "orcamento": "10k"}

    # CRM fields (v1)
    email = Column(String, nullable=True)
    origin = Column(String, default="whatsapp")  # whatsapp, instagram, meta_ads, organico...
    responsible = Column(String, nullable=True)  # SDR/Closer name/id (simple for v1)
    next_step = Column(String, nullable=True)
    estimated_value = Column(Float, default=0.0)
    closed_value = Column(Float, default=0.0)
    last_contact_at = Column(DateTime(timezone=True), nullable=True)

    pipeline_stage = Column(String, default="novo")
    
    # Handoff flag
    is_paused_for_human = Column(Integer, default=0)
    
    # Multichannel & Unread tracking
    channel = Column(String, default="whatsapp")  # whatsapp, instagram, webchat
    unread_count = Column(Integer, default=0)
    
    # [MULTI-AGENT] - Fila e Atribuição
    assigned_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    internal_notes = Column(Text, nullable=True)

    # [UTM TRACKING E META ADS] - Rastreamento de origem de anúncios
    utm_source = Column(String, nullable=True)      # google, meta, instagram
    utm_medium = Column(String, nullable=True)       # cpc, cpm, social
    utm_campaign = Column(String, nullable=True)     # nome_da_campanha
    utm_content = Column(String, nullable=True)      # identificador do criativo
    ad_creative_id = Column(String, nullable=True)   # ID do criativo no gerenciador
    ad_source = Column(String, nullable=True)        # origin visual no inbox: facebook, instagram, etc
    ad_campaign_name = Column(String, nullable=True) # Nome real da campanha puxado do face
    ad_creative_url = Column(String, nullable=True)  # URL da Thumbnail para preview

    # [INBOX] - Última mensagem para preview e ordenação
    last_message = Column(String, nullable=True)
    last_message_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    tenant = relationship("Tenant")

