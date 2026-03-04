import traceback
try:
    from services.message_buffer import process_lead_buffer
    process_lead_buffer.apply_async(('tenant', 'lead'), countdown=5)
    print('Celery queued successfully!')
except Exception as e:
    traceback.print_exc()
