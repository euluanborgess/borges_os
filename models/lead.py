from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
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
    
    pipeline_stage = Column(String, default="novo")
    
    # Handoff flag
    is_paused_for_human = Column(Integer, default=0)
    
    # Multichannel & Unread tracking
    channel = Column(String, default="whatsapp")  # whatsapp, instagram, webchat
    unread_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    tenant = relationship("Tenant")
