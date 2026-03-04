from core.celery_app import celery_app
print('Broker URL:', celery_app.conf.broker_url)
