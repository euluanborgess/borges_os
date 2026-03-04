import asyncio
import traceback
from core.database import SessionLocal
from api.routes.webhooks import evolution_webhook

class MockRequest:
    async def json(self):
        return {
            'event': 'messages.upsert',
            'instance': 'antigravity',
            'data': {
                'key': {'remoteJid': '5511999999999@s.whatsapp.net', 'fromMe': False},
                'message': {'conversation': 'Teste simulado de sistema'}
            }
        }

async def run_test():
    db = SessionLocal()
    req = MockRequest()
    try:
        res = await evolution_webhook(req, db)
        print("WEBHOOK COMPLETED SUCCESSFULLY:")
        print(res)
    except Exception as e:
        print("WEBHOOK FAILED WITH EXCEPTION:")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_test())
