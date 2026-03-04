from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from models.base import Base

class Task(Base):
    """
    Tarefas internas (Follow-up, Pedir documento, etc)
    """
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    lead_id = Column(String, ForeignKey("leads.id"), nullable=True, index=True)
    
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    is_completed = Column(Boolean, default=False)
    
    # NOVOS CAMPOS PARA O PAINEL DE TAREFAS (BASE44 MIGRAÇÃO)
    assigned_to = Column(String, nullable=True) # Ex: "Admin", "Corretor X"
    created_by = Column(String, nullable=True)  # Ex: "Admin"
    priority = Column(String, default="baixa")  # alta, media, baixa
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    tenant = relationship("Tenant")
    lead = relationship("Lead")

class Event(Base):
    """
    Agendamentos / Calendário (Substitui Google Calendar)
    """
    __tablename__ = "events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    lead_id = Column(String, ForeignKey("leads.id"), nullable=True, index=True)
    
    title = Column(String, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, default="scheduled") # scheduled, canceled, completed
    meeting_link = Column(String, nullable=True)
    
    # NOVOS CAMPOS CRM
    origin = Column(String, default="Manual") # WhatsApp, Site, Manual
    attendant = Column(String, nullable=True) # Nome da IA ou do Humano que marcou
    observations = Column(String, nullable=True) # Anotações ricas do Agendamento
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    tenant = relationship("Tenant")
    lead = relationship("Lead")
