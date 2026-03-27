"""
Borges OS — Email Service
Envia emails HTML premium (convite, notificações) via SMTP.
Fallback: se SMTP não configurado, loga o link no console.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os


def get_smtp_config():
    return {
        "host": os.getenv("SMTP_HOST", ""),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": os.getenv("SMTP_USER", ""),
        "password": os.getenv("SMTP_PASSWORD", ""),
        "from_name": os.getenv("SMTP_FROM_NAME", "Borges OS"),
        "from_email": os.getenv("SMTP_FROM_EMAIL", "noreply@borgesos.com"),
    }


def send_invite_email(to_email: str, owner_name: str, company_name: str, invite_url: str) -> bool:
    """
    Envia email de convite premium para o dono da empresa finalizar o cadastro.
    Returns True se enviou, False se fallback (sem SMTP).
    """
    cfg = get_smtp_config()
    
    # Build full URL
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    full_url = f"{base_url}{invite_url}"
    
    html = _build_invite_html(owner_name, company_name, full_url)
    
    if not cfg["host"] or not cfg["user"]:
        print(f"\n{'='*60}")
        print(f"📧 EMAIL DE CONVITE (SMTP não configurado)")
        print(f"   Para: {to_email}")
        print(f"   Nome: {owner_name}")
        print(f"   Empresa: {company_name}")
        print(f"   Link: {full_url}")
        print(f"{'='*60}\n")
        return False
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🚀 {owner_name}, seu Borges OS está pronto!"
        msg["From"] = f"{cfg['from_name']} <{cfg['from_email']}>"
        msg["To"] = to_email
        
        msg.attach(MIMEText(html, "html"))
        
        port = cfg["port"]
        if port == 465:
            # SSL direto (porta 465)
            with smtplib.SMTP_SSL(cfg["host"], port) as server:
                server.login(cfg["user"], cfg["password"])
                server.sendmail(cfg["from_email"], to_email, msg.as_string())
        else:
            # STARTTLS (porta 587)
            with smtplib.SMTP(cfg["host"], port) as server:
                server.starttls()
                server.login(cfg["user"], cfg["password"])
                server.sendmail(cfg["from_email"], to_email, msg.as_string())
        
        print(f"✅ Email enviado para {to_email}")
        return True
    except Exception as e:
        print(f"❌ Erro ao enviar email: {e}")
        print(f"   Link de fallback: {full_url}")
        return False


def _build_invite_html(owner_name: str, company_name: str, invite_url: str) -> str:
    first_name = owner_name.split()[0] if owner_name else "Parceiro"
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background-color:#0a0a0f;font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#0a0a0f;padding:40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background:linear-gradient(135deg,#111118 0%,#0d1117 100%);border-radius:24px;border:1px solid #1e1e2e;overflow:hidden;">
                    
                    <!-- Header com gradiente -->
                    <tr>
                        <td style="background:linear-gradient(135deg,#06b6d4,#0e7490);padding:40px 40px 30px;text-align:center;">
                            <div style="font-size:28px;font-weight:800;color:#ffffff;letter-spacing:-0.5px;">
                                ⚡ Borges OS
                            </div>
                            <div style="font-size:12px;color:rgba(255,255,255,0.7);margin-top:8px;letter-spacing:2px;text-transform:uppercase;">
                                Inteligência Comercial com IA
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Body -->
                    <tr>
                        <td style="padding:40px;">
                            <h1 style="color:#ffffff;font-size:24px;margin:0 0 8px;font-weight:700;">
                                Olá, {first_name}! 👋
                            </h1>
                            <p style="color:#8b8b9e;font-size:15px;line-height:1.6;margin:0 0 24px;">
                                A empresa <strong style="color:#06b6d4;">{company_name}</strong> foi cadastrada no Borges OS.
                                Você está a um passo de transformar a gestão comercial da sua empresa com inteligência artificial.
                            </p>
                            
                            <!-- Features -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:32px;">
                                <tr>
                                    <td style="padding:12px 0;border-bottom:1px solid #1e1e2e;">
                                        <span style="color:#06b6d4;font-size:16px;margin-right:12px;">🤖</span>
                                        <span style="color:#ffffff;font-size:14px;">IA que atende, qualifica e agenda automaticamente</span>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding:12px 0;border-bottom:1px solid #1e1e2e;">
                                        <span style="color:#06b6d4;font-size:16px;margin-right:12px;">📊</span>
                                        <span style="color:#ffffff;font-size:14px;">Pipeline visual com score inteligente dos leads</span>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding:12px 0;">
                                        <span style="color:#06b6d4;font-size:16px;margin-right:12px;">💬</span>
                                        <span style="color:#ffffff;font-size:14px;">WhatsApp + Instagram integrados em um só lugar</span>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- CTA Button -->
                            <div style="text-align:center;margin:32px 0;">
                                <a href="{invite_url}" 
                                   style="display:inline-block;background:linear-gradient(135deg,#06b6d4,#0e7490);color:#ffffff;font-size:16px;font-weight:700;padding:16px 48px;border-radius:12px;text-decoration:none;letter-spacing:0.5px;box-shadow:0 4px 20px rgba(6,182,212,0.3);">
                                    🚀 Finalizar Meu Cadastro
                                </a>
                            </div>
                            
                            <p style="color:#5a5a6e;font-size:12px;text-align:center;margin-top:24px;">
                                Este link é exclusivo para você. Ao clicar, você definirá sua senha e terá acesso completo ao sistema.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding:24px 40px;border-top:1px solid #1e1e2e;text-align:center;">
                            <p style="color:#3a3a4e;font-size:11px;margin:0;">
                                Borges OS © 2026 · Plataforma de Inteligência Comercial
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
