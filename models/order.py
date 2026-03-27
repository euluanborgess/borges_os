from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Float, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from models.base import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    lead_id = Column(String, ForeignKey("leads.id"), nullable=False, index=True)
    
    amount = Column(Float, nullable=False, default=0.0)
    status = Column(String, default="pending") # pending, paid, cancelled, refunded
    items = Column(JSON, default=list) # [{"name": "Produto A", "qty": 1, "price": 100}]
    
    external_id = Column(String, nullable=True) # ID do gateway de pagamento ou ERP
    payment_method = Column(String, nullable=True) # pix, credit_card, boleto
    
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    tenant = relationship("Tenant")
    lead = relationship("Lead")
