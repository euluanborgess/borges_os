import json
from sqlalchemy.orm import Session
from models import Lead, Task, Event, Pipeline, PipelineStage, Contract

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
                
        # Auto-update score after any profile update
        from services.scoring_service import calculate_lead_score
        self.lead.score = calculate_lead_score(self.db, self.lead)
        
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
                new_stage = str(value).lower().strip()
                self.lead.pipeline_stage = new_stage

                # Minimal onboarding automation on close
                if new_stage in ("fechado", "venda", "closed"):
                    # Create onboarding tasks
                    try:
                        self.db.add(Task(
                            tenant_id=self.tenant_id,
                            lead_id=self.lead_id,
                            title="Onboarding: coletar dados do cliente",
                            description="Coletar dados necessários e iniciar onboarding.",
                            assigned_to=self.lead.responsible,
                            priority="alta",
                        ))
                        self.db.add(Task(
                            tenant_id=self.tenant_id,
                            lead_id=self.lead_id,
                            title="Onboarding: enviar boas-vindas",
                            description="Enviar mensagem de boas-vindas pós-fechamento.",
                            assigned_to=self.lead.responsible,
                            priority="media",
                        ))
                    except Exception as e:
                        print(f"Falha ao criar tasks de onboarding: {e}")

                    # Generate contract using new Contract model
                    try:
                        new_contract = Contract(
                            tenant_id=self.tenant_id,
                            lead_id=self.lead_id,
                            title=f"Contrato de Venda - {self.lead.name or self.lead.phone}",
                            value=(self.lead.closed_value or self.lead.estimated_value or 0.0),
                            status="draft",
                            duration_months=12
                        )
                        self.db.add(new_contract)
                    except Exception as e:
                        print(f"Falha ao gerar contrato no DB: {e}")

                    # Send welcome message (best-effort)
                    try:
                        from models import Tenant
                        tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
                        if tenant and tenant.welcome_message and tenant.evolution_instance_id and self.lead.phone:
                            import asyncio
                            from services.evolution_sender import send_whatsapp_message
                            integ = tenant.integrations or {}
                            asyncio.run(
                                send_whatsapp_message(
                                    tenant.evolution_instance_id,
                                    self.lead.phone,
                                    tenant.welcome_message,
                                    evolution_url=integ.get("evolution_api_url"),
                                    evolution_api_key=integ.get("evolution_api_key"),
                                )
                            )
                    except Exception as e:
                        print(f"Falha ao enviar boas-vindas: {e}")
                
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
            
        elif action_type == "register_sale_conversion":
            # Exemplo action: type="register_sale_conversion", value="1500.0"
            try:
                sale_value = float(value) if value else 0.0
                self.lead.closed_value = sale_value
                self.lead.pipeline_stage = "venda"
                
                from models import Tenant
                from services.meta_capi_service import send_purchase_event
                
                tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
                if tenant and tenant.meta_pixel_id and tenant.meta_capi_token:
                    lead_data = {
                        "phone": self.lead.phone,
                        "email": self.lead.email,
                        "id": self.lead.id
                    }
                    # O disparo roda de forma blocante rapida, ou usando Celery futuramente.
                    send_purchase_event(
                        lead_data=lead_data,
                        value=sale_value,
                        meta_pixel_id=tenant.meta_pixel_id,
                        meta_capi_token=tenant.meta_capi_token
                    )
            except Exception as e:
                print(f"Erro ao disparar conversão de venda: {e}")
