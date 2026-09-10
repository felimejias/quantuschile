import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# Usuario de autenticacion SMTP (cuenta Gmail con App Password autorizada)
GMAIL_AUTH_USER = os.environ.get("GMAIL_AUTH_USER", "felipe.mejias.g@gmail.com")

# Direccion de remitente visible y reply-to corporativo (Cloudflare Email Routing)
GMAIL_FROM_USER = os.environ.get("GMAIL_FROM_USER", os.environ.get("GMAIL_USER", "contacto@quantuschile.cl"))

GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "tlwz kgfx izft mvmo").strip("\"'")

def smtp_configured():
    """True si existe credencial SMTP para envios de correo."""
    return bool(os.environ.get("GMAIL_APP_PASSWORD", GMAIL_APP_PASSWORD))

def send_email(to_email, subject, body_html, attachments=None):
    """
    Envia un correo usando el servidor SMTP autorizado de Gmail con remitente corporativo @quantuschile.cl.
    """
    if not smtp_configured():
        print("Error al enviar correo: GMAIL_APP_PASSWORD no configurado.")
        return False

    auth_user = os.environ.get("GMAIL_AUTH_USER", GMAIL_AUTH_USER)
    from_user = os.environ.get("GMAIL_FROM_USER", GMAIL_FROM_USER)
    app_pass = os.environ.get("GMAIL_APP_PASSWORD", GMAIL_APP_PASSWORD).strip("\"'")

    msg = MIMEMultipart()
    msg['From'] = f"Quantus Chile <{from_user}>"
    msg['To'] = to_email
    msg['Reply-To'] = f"Quantus Chile <{from_user}>"
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body_html, 'html'))
    for path in attachments or []:
        if not path or not os.path.exists(path):
            continue
        with open(path, "rb") as file_obj:
            part = MIMEApplication(file_obj.read(), Name=os.path.basename(path))
        part["Content-Disposition"] = f'attachment; filename="{os.path.basename(path)}"'
        msg.attach(part)
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(auth_user, app_pass)
        text = msg.as_string()
        server.sendmail(auth_user, to_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        return False
