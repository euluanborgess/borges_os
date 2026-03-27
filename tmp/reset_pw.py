import sqlite3
from core.security import get_password_hash

conn = sqlite3.connect('borges_os.db')
c = conn.cursor()
pwd = get_password_hash('123456')
c.execute("UPDATE users SET hashed_password = ? WHERE email = 'atendimentocapitaojack@gmail.com'", (pwd,))
conn.commit()
conn.close()
print('Senha atualizada para 123456')
