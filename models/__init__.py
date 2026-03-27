from models.base import Base
from models.tenant import Tenant
from models.lead import Lead
from models.pipeline import Pipeline, PipelineStage
from models.message import Message
from models.task_event import Task, Event
from models.user import User
from models.contract import Contract
from models.audit import AuditLog
from models.buffer import MessageBuffer
from models.order import Order
from models.lead_timeline import LeadTimeline
from models.ads import AdAccount, AdCampaign, AdMetric

# Importar novos modelos aqui para o Alembic reconhecê-los automaticamente.
