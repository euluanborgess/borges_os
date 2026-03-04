from sqlalchemy import Column, String, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from models.base import Base

class Message(Base):
    """
    Representa o histórico de interações (WhatsApp) consolidadas.
    A engine de buffer salvará aqui.
    """
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    lead_id = Column(String, ForeignKey("leads.id"), nullable=False, index=True)
    
    sender_type = Column(String, nullable=False) # 'lead', 'ai', 'human'
    content = Column(Text, nullable=True) # O texto da mensagem/transcrição
    media_url = Column(String, nullable=True) # Se for áudio/imagem e tiver link
    media_type = Column(String, nullable=True) # 'audio', 'image', 'document'
    
    metadata_json = Column(JSON, default=dict) # Para id da evolution API, etc
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    tenant = relationship("Tenant")
    lead = relationship("Lead")
