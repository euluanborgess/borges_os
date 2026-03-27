"""Quick test: SMTP porta 587 STARTTLS"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

host = "mail.agenciaborges.com.br"
port = 587
user = "contato@agenciaborges.com.br"
password = "Luan35133!"

print("=== Teste SMTP porta 587 (STARTTLS) ===")
try:
    server = smtplib.SMTP(host, port, timeout=15)
    server.starttls()
    server.login(user, password)
    print(f"Login SMTP OK! Conectado a {host}:{port}")
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Teste Borges OS - SMTP"
    msg["From"] = f"Borges OS <{user}>"
    msg["To"] = "atendimentocapitaojack@gmail.com"
    msg.attach(MIMEText("<h1>SMTP funcionando!</h1><p>Teste do Borges OS via porta 587.</p>", "html"))
    
    server.sendmail(user, "atendimentocapitaojack@gmail.com", msg.as_string())
    print("Email de teste ENVIADO para atendimentocapitaojack@gmail.com")
    server.quit()
except Exception as e:
    print(f"ERRO SMTP: {e}")
