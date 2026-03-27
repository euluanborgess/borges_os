import uuid
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from datetime import datetime
from .base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True)
    user_id = Column(String, index=True, nullable=True)
    action = Column(String)  # ex: 'move_pipeline', 'send_message', 'login'
    target_type = Column(String) # ex: 'lead', 'task'
    target_id = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
