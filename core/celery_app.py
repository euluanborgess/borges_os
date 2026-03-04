import os
import sys

# Garante que a raiz do projeto esteja no path, independentemente de como o Celery foi chamado
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from celery import Celery
from core.config import settings

celery_app = Celery(
    "borges_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["services.message_buffer", "services.jobs_followup"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=False,  # Alinhamento pro Brasil e CRON nativo local
)

from celery.schedules import crontab

# Celery Beat Cronjobs
celery_app.conf.beat_schedule = {
    "daily_followup_scanner": {
        "task": "services.jobs_followup.execute_daily_followups",
        # Varre o banco de hora em hora pra checar quem passou da janela de 24h
        "schedule": crontab(minute="0"),
    },
}
