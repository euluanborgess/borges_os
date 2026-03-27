import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from datetime import datetime
from .base import Base

class MessageBuffer(Base):
    __tablename__ = "message_buffer"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True)
    lead_id = Column(String, index=True)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
