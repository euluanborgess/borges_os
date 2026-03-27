import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import SessionLocal
from models.user import User
from core.security import get_password_hash

def reset_pwd():
    db = SessionLocal()
    admin = db.query(User).filter(User.email == 'admin@borges.com').first()
    if admin:
        admin.hashed_password = get_password_hash('admin123')
        db.commit()
        print('Senha resetada com sucesso para admin123')
    else:
        print('Admin nao encontrado')

if __name__ == '__main__':
    reset_pwd()
