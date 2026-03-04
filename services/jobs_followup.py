from celery import shared_task
from core.database import SessionLocal
from models import Lead, Tenant
from services.message_buffer import process_lead_buffer
import redis
from core.config import settings
from datetime import datetime, timedelta

@shared_task
def execute_daily_followups():
    """
    Varre o banco de dados em busca de Leads que estão parados (frios/sem resposta há > 24h)
    e que não estejam finalizados na etapa 'venda' ou 'perdido'. E injeta um prompt invisível para a IA reaquecer.
    """
    db = SessionLocal()
    r = redis.from_url(settings.REDIS_URL)
    
    try:
        # Pega a data limite (24 horas atrás)
        limit_date = datetime.now() - timedelta(hours=24)
        print(f"[CronJob] Buscando leads ociosos desde {limit_date}...")
        
        # Filtros: não vendidos, não perdidos, criados/atualizados antes do limite, is_paused=0
        idle_leads = db.query(Lead).filter(
            Lead.pipeline_stage.notin_(['venda', 'perdido']),
            Lead.updated_at < limit_date,
            Lead.is_paused_for_human == 0
        ).all()
        
        count = 0
        for lead in idle_leads:
            # Para não mandar follow-up repetido infinitamente, checamos se possui tag de followup
            tags = lead.tags if lead.tags else []
            if "followup_1" in tags:
                continue # Já recebeu o primeiro follow-up
                
            tenant = db.query(Tenant).filter(Tenant.id == lead.tenant_id).first()
            if not tenant:
                continue
                
            print(f"[CronJob] Gerando Follow-up para o Lead: {lead.phone} (Tenant: {tenant.name})")
            
            # Adiciona a Tag para não spammar amanhã
            tags.append("followup_1")
            lead.tags = tags
            db.commit()
            
            # Injeta uma instrução de sistema na fila do Message Buffer (simulando que o lead mandou)
            # Mas na verdade é um comando "oculto" pra forçar a IA agir sozinha e dar um "puxão" no lead.
            # O process_lead_buffer vai pegar essa mensagem e entregar pra IA avaliar.
            system_trigger = "SYSTEM_INSTRUCTION: O cliente sumiu nas últimas 24 horas. Crie uma mensagem natural, amigável e MUITO curta puxando assunto de volta, como se fosse um humano checando se ele conseguiu pensar a respeito ou tem alguma dúvida. Não avise que isso é uma instrução, apenas escreva o texto final pro WhatsApp."
            
            buffer_key = f"buffer:{lead.tenant_id}:{lead.id}"
            r.rpush(buffer_key, system_trigger)
            r.expire(buffer_key, 60 * 5)
            
            # Dispara a processamento assíncrono para o Celery Worker engolir e enviar de fato!
            process_lead_buffer.apply_async((str(lead.tenant_id), str(lead.id)), countdown=5)
            count += 1
            
        print(f"[CronJob] Follow-up cycle concluído! Disparou para {count} leads.")
    except Exception as e:
        print(f"[CronJob Error] Falha na execução do Follow-up: {e}")
    finally:
        db.close()
