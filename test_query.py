import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import SessionLocal
from models.task_event import Event
from models.lead import Lead

def test_query():
    db = SessionLocal()
    try:
        query = db.query(Event, Lead).outerjoin(Lead, Event.lead_id == Lead.id).order_by(Event.start_time.asc()).all()
        results = []
        for event, lead in query:
            results.append({
                "id": event.id,
                "title": event.title,
                "start_time": event.start_time.isoformat() if event.start_time else None,
                "end_time": event.end_time.isoformat() if event.end_time else None,
                "status": event.status,
                "meeting_link": event.meeting_link,
                "origin": event.origin,
                "attendant": event.attendant,
                "observations": event.observations,
                "created_at": event.created_at.isoformat() if event.created_at else None,
                "lead": {
                    "id": lead.id if lead else None,
                    "name": lead.name if lead else "Leads Órfãos/Manual",
                    "whatsapp": lead.whatsapp if lead else ""
                }
            })
        print("Serialization success! Results:", len(results))
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_query()
