import sqlite3
import hashlib
import uuid
import datetime
from pathlib import Path
import sys

# Inscribir ruta base de do
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from marketing.claims_matrix import UNIVERSALLY_BLOCKED_PHRASES

DB_PATH = BASE_DIR / "data" / "marketing.sqlite3"

ADS = [
    {
        "num": 1,
        "audience": "Herencia (personas naturales)",
        "title": "Tu nombre puede aparecer en el Diario Oficial y nunca enterarte",
        "body": "Procesos de herencia, posesión efectiva y notificaciones judiciales se publican ahí, no en tu correo. Si nadie está mirando, te puedes enterar meses después — o nunca. Vigila tu RUT.\n\nActivar mi radar → https://www.quantuschile.cl/do",
        "cta": "Activar mi radar → www.quantuschile.cl/do"
    },
    {
        "num": 2,
        "audience": "Quiebra / insolvencia (empresas)",
        "title": "Si un cliente o proveedor entra en insolvencia, ¿cómo te enteras?",
        "body": "Los procedimientos concursales se notifican por publicación oficial, no por una llamada de cortesía. Empresas que no vigilan a sus contrapartes se enteran cuando ya es tarde para actuar. Nosotros vigilamos por ti.\n\nVer radar Diario Oficial → https://www.quantuschile.cl/do",
        "cta": "Ver radar Diario Oficial → www.quantuschile.cl/do"
    },
    {
        "num": 3,
        "audience": "Demanda sin conocer el domicilio (personas naturales)",
        "title": "Puedes estar demandado y no saberlo",
        "body": "Cuando un tribunal no logra ubicar tu domicilio, la ley permite notificarte por un aviso público. Es legal, es válido, y corre el plazo aunque no lo hayas visto. Que no te pase.\n\nVigilar mi RUT → https://www.quantuschile.cl/do",
        "cta": "Vigilar mi RUT → www.quantuschile.cl/do"
    },
    {
        "num": 4,
        "audience": "Juntas y cambios societarios (empresas / socios)",
        "title": "Citaron a junta de accionistas y tú no estabas mirando",
        "body": "Convocatorias, aumentos de capital, disoluciones — se publican en el Diario Oficial con plazos legales que corren para todos los socios, se hayan enterado o no. Un radar activo te avisa el mismo día.\n\nActivar radar societario → https://www.quantuschile.cl/do",
        "cta": "Activar radar societario → www.quantuschile.cl/do"
    },
    {
        "num": 5,
        "audience": "Extravío de documentos (personas naturales / pymes)",
        "title": "Perdiste un pagaré o un documento de deuda. Ahora la publicación corre sola",
        "body": "El extravío de pagarés, letras de cambio o bonos se resuelve con publicación oficial — y ahí también aparecen los que te involucran sin que lo sepas. Entérate apenas sale, no cuando alguien más lo lea primero.\n\nVer cómo funciona → https://www.quantuschile.cl/do",
        "cta": "Ver cómo funciona → www.quantuschile.cl/do"
    },
    {
        "num": 6,
        "audience": "Dueños de pyme (empresas)",
        "title": "Tu empresa puede estar mencionada hoy y tú no lo sabes hasta el 1 o el 15",
        "body": "Las publicaciones oficiales salen en fechas fijas, dos veces al mes. Si no revisas exactamente esos días, hay una ventana donde cualquiera se entera antes que tú de algo que te afecta directamente.\n\nNo perder la fecha nunca más → https://www.quantuschile.cl/do",
        "cta": "No perder la fecha nunca más → www.quantuschile.cl/do"
    },
    {
        "num": 7,
        "audience": "Historia corta / dramatizada (personas naturales)",
        "title": "\"Me enteré de la herencia de mi tío ocho meses tarde\"",
        "body": "No por mala suerte. Porque nadie en la familia revisaba el Diario Oficial. La posesión efectiva y las notificaciones asociadas ya estaban publicadas — solo que nadie las vio a tiempo. Un radar sí las ve.\n\nActivar radar familiar → https://www.quantuschile.cl/do",
        "cta": "Activar radar familiar → www.quantuschile.cl/do"
    },
    {
        "num": 8,
        "audience": "Abogados / estudios jurídicos (profesionales)",
        "title": "Tus clientes esperan que tú veas esto primero",
        "body": "Revisar el Diario Oficial cliente por cliente, día por día, no escala. Automatiza la vigilancia por RUT y entérate de publicaciones relevantes antes que tu cliente te pregunte por qué no le avisaste.\n\nVer radar para estudios jurídicos → https://www.quantuschile.cl/do",
        "cta": "Ver radar para estudios jurídicos → www.quantuschile.cl/do"
    },
    {
        "num": 9,
        "audience": "Urgencia / plazo corto (empresas y personas)",
        "title": "Las publicaciones legales no esperan a que tengas tiempo de revisar",
        "body": "Salen el 1 y el 15 de cada mes, con plazos que empiezan a correr ese mismo día. Si tu método es 'revisar cuando me acuerdo', ya estás jugando en desventaja.\n\nAutomatizar mi vigilancia → https://www.quantuschile.cl/do",
        "cta": "Automatizar mi vigilancia → www.quantuschile.cl/do"
    },
    {
        "num": 10,
        "audience": "Costo cero como gancho (ambos públicos)",
        "title": "Vigilar tu RUT en el Diario Oficial no te cuesta nada. No hacerlo, sí.",
        "body": "Publicaciones judiciales, societarias, quiebras, herencias — todo pasa por ahí. Activa tu radar gratis y recibe el aviso apenas algo con tu nombre o tu empresa sale publicado.\n\nActivar → https://www.quantuschile.cl/do",
        "cta": "Activar → www.quantuschile.cl/do"
    }
]

# Horarios estratégicos de publicación (2 posts por día hábil, a las 09:30 y 15:30)
# Inicio: Martes 11 de Agosto de 2026
SCHEDULE_TIMES = [
    ("2026-08-11T09:30:00", "2026-08-11T15:30:00"), # Martes 11
    ("2026-08-12T09:30:00", "2026-08-12T15:30:00"), # Miércoles 12
    ("2026-08-13T09:30:00", "2026-08-13T15:30:00"), # Jueves 13
    ("2026-08-14T09:30:00", "2026-08-14T15:30:00"), # Viernes 14
    ("2026-08-17T09:30:00", "2026-08-17T15:30:00"), # Lunes 17
]

def audit_compliance(ad):
    text_to_check = (ad["title"] + " " + ad["body"]).lower()
    for phrase in UNIVERSALLY_BLOCKED_PHRASES:
        if phrase in text_to_check:
            raise ValueError(f"Anuncio #{ad['num']} viola la matriz de compliance: contiene la frase prohibida '{phrase}'")

def run():
    print("=== QUANTUS MARKETING CENTER — PROGRAMACIÓN ESTRATÉGICA LINKEDIN ===")
    
    # 1. Auditoría de Cumplimiento Legal
    for ad in ADS:
        audit_compliance(ad)
    print("✓ 1. Auditoría de Cumplimiento Legal (Ley 19.496 / Ley 21.719 / CARTA MAGNA): 10/10 Anuncios Aprobados 100% OK")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    now_iso = datetime.datetime.now().isoformat()
    campaign_id = "camp_linkedin_do_202608"
    
    # 2. Registrar/Actualizar Campaña
    c.execute("""
        INSERT INTO marketing_campaigns (id, tenant_id, name, service_category, target_audience, flow_type, status, created_by, created_at, updated_at)
        VALUES (?, 'quantus_chile', 'Radar Diario Oficial — Campaña LinkedIn B2B/B2C', 'diario_oficial', 'personas_y_empresas', 'flujo_a', 'active', 'felipe_mejias', ?, ?)
        ON CONFLICT(id) DO UPDATE SET updated_at=excluded.updated_at
    """, (campaign_id, now_iso, now_iso))
    
    scheduled_count = 0
    slot_idx = 0
    
    for i, ad in enumerate(ADS):
        content_id = f"cnt_linkedin_do_{ad['num']:02d}"
        content_text = f"{ad['title']}\n\n{ad['body']}"
        content_hash = hashlib.sha256(content_text.encode('utf-8')).hexdigest()
        
        # Insertar contenido
        c.execute("""
            INSERT INTO marketing_contents (id, campaign_id, channel, flow_type, content_type, title, body, destination_url, content_hash, status, created_at, updated_at)
            VALUES (?, ?, 'linkedin', 'flujo_a', 'post', ?, ?, 'https://www.quantuschile.cl/do', ?, 'approved', ?, ?)
            ON CONFLICT(id) DO UPDATE SET title=excluded.title, body=excluded.body, updated_at=excluded.updated_at
        """, (content_id, campaign_id, ad['title'], content_text, content_hash, now_iso, now_iso))
        
        # Calcular fecha programada (2 posts por día hábil)
        day_idx = i // 2
        time_idx = i % 2
        scheduled_at = SCHEDULE_TIMES[day_idx][time_idx]
        
        schedule_id = f"sch_linkedin_do_{ad['num']:02d}"
        idempotency_key = f"idemp_linkedin_{ad['num']:02d}_{scheduled_at[:10]}"
        
        c.execute("""
            INSERT INTO marketing_schedules (id, content_id, flow_type, channel, scheduled_at, idempotency_key, content_hash, status, retry_count, max_retries, created_at)
            VALUES (?, ?, 'flujo_a', 'linkedin', ?, ?, ?, 'scheduled', 0, 3, ?)
            ON CONFLICT(id) DO UPDATE SET scheduled_at=excluded.scheduled_at, status='scheduled'
        """, (schedule_id, content_id, scheduled_at, idempotency_key, content_hash, now_iso))
        
        scheduled_count += 1
        print(f"  • Post #{ad['num']:02d} [{ad['audience']}]: Programado para {scheduled_at} ({'Mañana 09:30' if time_idx==0 else 'Tarde 15:30'})")
    
    conn.commit()
    conn.close()
    
    print(f"\n✓ 2. Se han programado exitosamente {scheduled_count} anuncios en marketing.sqlite3 con Pacing Optimizado para Máximo Alcance en LinkedIn.")

if __name__ == "__main__":
    run()
