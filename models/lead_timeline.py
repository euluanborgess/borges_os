from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from models.base import Base

class LeadTimeline(Base):
    __tablename__ = "lead_timeline"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    lead_id = Column(String, ForeignKey("leads.id"), nullable=False, index=True)
    
    action = Column(String) # assigned, transferred, unassigned, moved_stage, manual_update
    user_id = Column(String, ForeignKey("users.id"), nullable=True) # Quem fez a ação
    
    # Metadata: ex: {"from_agent": "A", "to_agent": "B"} ou {"new_stage": "PAGO"}
    details = Column(JSON, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant")
    lead = relationship("Lead")
    user = relationship("User")
