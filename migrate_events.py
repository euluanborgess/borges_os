import sqlite3
import os

db_path = "borges_os.db" # Verificando se é sqlite local
if os.path.exists(db_path):
    print("Conectando ao banco SQLite local para aplicar a migração...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE events ADD COLUMN origin VARCHAR DEFAULT 'Manual'")
        print("Coluna 'origin' adicionada.")
    except Exception as e:
        print(f"Aviso origin: {e}")
        
    try:
        cursor.execute("ALTER TABLE events ADD COLUMN attendant VARCHAR")
        print("Coluna 'attendant' adicionada.")
    except Exception as e:
        print(f"Aviso attendant: {e}")
        
    try:
        cursor.execute("ALTER TABLE events ADD COLUMN observations VARCHAR")
        print("Coluna 'observations' adicionada.")
    except Exception as e:
        print(f"Aviso observations: {e}")
        
    conn.commit()
    conn.close()
    print("Migração concluída.")
else:
    # Se for Postgres, podemos usar SQLAlchemy
    from core.database import engine
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE events ADD COLUMN origin VARCHAR DEFAULT 'Manual'"))
            print("Coluna 'origin' adicionada no Postgres.")
        except Exception as e:
            print(f"Aviso origin: {e}")
            
        try:
            conn.execute(text("ALTER TABLE events ADD COLUMN attendant VARCHAR"))
            print("Coluna 'attendant' adicionada no Postgres.")
        except Exception as e:
            print(f"Aviso attendant: {e}")
            
        try:
            conn.execute(text("ALTER TABLE events ADD COLUMN observations VARCHAR"))
            print("Coluna 'observations' adicionada no Postgres.")
        except Exception as e:
            print(f"Aviso observations: {e}")
        
        conn.commit()
        print("Migração Postgres concluída.")
