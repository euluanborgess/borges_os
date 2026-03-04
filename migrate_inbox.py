from core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE leads ADD COLUMN channel VARCHAR DEFAULT 'whatsapp'"))
        print("OK: channel added")
    except Exception as e:
        print(f"channel: {e}")
    
    try:
        conn.execute(text("ALTER TABLE leads ADD COLUMN unread_count INTEGER DEFAULT 0"))
        print("OK: unread_count added")
    except Exception as e:
        print(f"unread_count: {e}")
    
    conn.commit()
    print("Migration done")
