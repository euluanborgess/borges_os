from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.user import User

engine = create_engine('sqlite:///borges_os.db')
session = Session(engine)
users = session.query(User).filter(User.invite_token != None).all()
if not users:
    print("Nenhum convite pendente encontrado.")
else:
    for u in users:
        print(f"Email: {u.email}")
        print(f"Link:  http://localhost:8000/register?token={u.invite_token}")
        print("---")
session.close()
