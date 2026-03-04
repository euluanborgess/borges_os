import json
from sqlalchemy.orm import Session
from models import Lead, Task, Event, Pipeline, PipelineStage

class ActionResolver:
    """
    Recebe as 'actions' geradas pelo LLM e executa as mudanças no Banco de Dados (CRM).
    """
    
    def __init__(self, db: Session, tenant_id: str, lead_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.lead_id = lead_id
        self.lead = db.query(Lead).filter(Lead.id == lead_id, Lead.tenant_id == tenant_id).first()
        
    def execute_all(self, actions: list):
        if not self.lead:
            print(f"Erro: Lead {self.lead_id} não encontrado no banco.")
            return
            
        for action in actions:
            try:
                self._route_action(action)
            except Exception as e:
                print(f"Erro ao executar action {action}: {e}")
                
        self.db.commit()

    def _route_action(self, action: dict):
        action_type = action.get("type")
        key = action.get("key")
        value = action.get("value")
        
        if action_type == "update_lead_profile":
            if key and value:
                # O SQLAlchemy JSON type as vezes requer que recriemos o dicionário
                profile = dict(self.lead.profile_data) if self.lead.profile_data else {}
                profile[key] = value
                self.lead.profile_data = profile
                
                # Se a IA descobrir o nome real, injeta direto na coluna principal para Roteamento UI
                if key.lower() in ["nome", "name", "client_name"]:
                    self.lead.name = value
                
                
        elif action_type == "set_lead_temperature":
            if value in ["frio", "morno", "quente"]:
                self.lead.temperature = value
                
        elif action_type == "set_lead_score":
            try:
                self.lead.score = int(value)
            except (ValueError, TypeError):
                pass
                
        elif action_type == "add_tag":
            if value:
                tags = list(self.lead.tags) if self.lead.tags else []
                if value not in tags:
                    tags.append(value)
                    self.lead.tags = tags
                    
        elif action_type == "move_pipeline_stage":
            if value:
                # Normaliza para lowercase para dar match com o Enum do Frontend
                self.lead.pipeline_stage = str(value).lower().strip()
                
        elif action_type == "create_task":
            # Exemplo action: type="create_task", key="Lembrete", value="Ligar amanha"
            new_task = Task(
                tenant_id=self.tenant_id,
                lead_id=self.lead_id,
                title=key or "Tarefa gerada pela IA",
                description=value
            )
            self.db.add(new_task)
            
        elif action_type == "schedule_meeting":
            # Exemplo action: type="schedule_meeting", key="Consultoria", value="2026-02-25T14:00"
            if value:
                from datetime import datetime
                try:
                    start_t = datetime.fromisoformat(value)
                    # Exemplo padrão: reunião de 1 hora
                    from datetime import timedelta
                    end_t = start_t + timedelta(hours=1)
                    
                    new_event = Event(
                        tenant_id=self.tenant_id,
                        lead_id=self.lead_id,
                        title=key or "Reunião Agendada pela IA",
                        start_time=start_t,
                        end_time=end_t,
                        origin="WhatsApp",
                        attendant="Borges IA" # Assinatura da IA na originação do CRM
                    )
                    self.db.add(new_event)
                    
                    # Auto-Avança o pipeline para garantir consistência
                    self.lead.pipeline_stage = "reuniao"
                except Exception as e:
                    print(f"Erro ao parsear data de agendamento: {value} - {e}")
            
        elif action_type == "handoff_to_human":
            self.lead.is_paused_for_human = 1
            # Disparar alerta via WS para o painel focar neste lead
            import asyncio
            from services.websocket_manager import manager
            asyncio.create_task(
                manager.broadcast_to_tenant(self.tenant_id, {
                    "type": "human_handoff_requested",
                    "lead_id": self.lead_id,
                    "lead_phone": self.lead.phone,
                    "message": "Este lead solicitou atendimento humano."
                })
            )
