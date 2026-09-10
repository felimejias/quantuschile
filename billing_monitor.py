import os
import json
import time
from datetime import datetime, timedelta
from mailer import send_email
from dotenv import load_dotenv

load_dotenv()

PEOPLE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'do_people.json')

def load_json(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def check_billing():
    print("[Billing Monitor] Iniciando revisión de suscripciones...")
    people = load_json(PEOPLE_FILE)
    hoy = datetime.now().date()
    cambios_realizados = False
    
    for person in people:
        nombre = person.get('nombre_completo', '')
        estado = person.get('estado', 'inactivo')
        fecha_str = person.get('fecha_vencimiento', '')
        email_destino = person.get('alertar_a', '')
        
        if estado != 'activo' or not fecha_str or not email_destino:
            continue
            
        try:
            fecha_vencimiento = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            dias_restantes = (fecha_vencimiento - hoy).days
            
            if dias_restantes == 3:
                print(f"[{nombre}] ¡Vence en 3 días! Enviando recordatorio...")
                subject = f"Aviso de Vencimiento: Vigilancia Diario Oficial de {nombre}"
                body = (
                    f"Hola,<br><br>"
                    f"Te informamos que tu plan de vigilancia del Diario Oficial para <b>{nombre}</b> "
                    f"caducará en exactamente <b>3 días</b> ({fecha_str}).<br><br>"
                    f"Para mantener tu protección activa y seguir recibiendo alertas tempranas, "
                    f"por favor realiza la transferencia de renovación y envíanos el comprobante.<br><br>"
                    f"Planes disponibles:<br>"
                    f"- 1 Mes: $1.000<br>"
                    f"- 12 Meses: $10.000<br>"
                    f"- 24 Meses: $24.000<br><br>"
                    f"Saludos,<br>"
                    f"<b>Quantus Legal Bot</b>"
                )
                send_email(email_destino, subject, body)
                send_email("felipe.mejias.g@gmail.com", f"[SISTEMA] Recordatorio de cobro enviado a {email_destino} por {nombre}", "Aviso automático enviado.")
                
            elif dias_restantes <= 0:
                print(f"[{nombre}] ¡Suscripción expirada! Desactivando...")
                person['estado'] = 'vencido'
                cambios_realizados = True
                
                subject = f"Servicio Suspendido: Vigilancia Diario Oficial de {nombre}"
                body = (
                    f"Hola,<br><br>"
                    f"Te informamos que tu plan de vigilancia para <b>{nombre}</b> ha expirado.<br><br>"
                    f"Nuestro radar de inteligencia artificial ya no está monitoreando tu nombre en el Diario Oficial. "
                    f"Si deseas reactivar la protección, por favor realiza el pago de renovación.<br><br>"
                    f"Saludos,<br>"
                    f"<b>Quantus Legal Bot</b>"
                )
                send_email(email_destino, subject, body)
                send_email("felipe.mejias.g@gmail.com", f"[SISTEMA] Cliente Desactivado: {nombre}", f"Se desactivó a {nombre} por no pago.")
                
        except Exception as e:
            print(f"[Billing Monitor] Error procesando fechas para {nombre}: {e}")
            
    if cambios_realizados:
        save_json(PEOPLE_FILE, people)
        print("[Billing Monitor] Base de datos actualizada con suspensiones.")
        
    print("[Billing Monitor] Revisión de facturación finalizada.")

if __name__ == "__main__":
    check_billing()
