import sqlite3
import datetime
import json
import logging
from pathlib import Path
import sys

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from marketing.linkedin_client import get_stored_token, get_user_profile, post_share

DB_PATH = BASE_DIR / "data" / "marketing.sqlite3"
LOG_PATH = BASE_DIR / "logs" / "linkedin_dispatcher.log"

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def run_dispatch():
    if not DB_PATH.exists():
        print("Base de datos de marketing no encontrada.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    now_iso = datetime.datetime.now().isoformat()
    
    # Buscar publicaciones programadas cuya fecha ya llegó o pasó
    c.execute("""
        SELECT s.id, s.content_id, c.title, c.body, c.destination_url, s.retry_count, s.max_retries
        FROM marketing_schedules s
        JOIN marketing_contents c ON s.content_id = c.id
        WHERE s.channel = 'linkedin'
          AND s.status = 'scheduled'
          AND s.scheduled_at <= ?
        ORDER BY s.scheduled_at ASC
    """, (now_iso,))
    
    pending_posts = c.fetchall()
    
    if not pending_posts:
        print(f"[{now_iso}] No hay publicaciones pendientes en este momento.")
        return
        
    print(f"[{now_iso}] Se encontraron {len(pending_posts)} publicación(es) pendiente(s) para LinkedIn.")
    
    token_info = get_stored_token()
    if not token_info or not token_info.get("access_token"):
        print("ERROR: No hay token de acceso de LinkedIn activo. Registra uno en /marketing/linkedin/autorizar")
        return
        
    access_token = token_info["access_token"]
    try:
        profile = get_user_profile(access_token)
        author_urn = profile.get("sub") or profile.get("id") or "urn:li:person:authorized"
        if not author_urn.startswith("urn:li:"):
            author_urn = f"urn:li:person:{author_urn}"
    except Exception as e:
        print(f"Error al obtener perfil de usuario: {e}")
        author_urn = "urn:li:person:authorized"

    for schedule_id, content_id, title, body, dest_url, retry_count, max_retries in pending_posts:
        print(f"  -> Publicando [{schedule_id}]: {title}...")
        try:
            res = post_share(access_token, author_urn, body, title=title, target_url=dest_url)
            post_urn = res.get("id") or res.get("value", {}).get("id") or "published_ok"
            
            c.execute("""
                UPDATE marketing_schedules
                SET status = 'published', published_at = ?, external_post_id = ?
                WHERE id = ?
            """, (datetime.datetime.now().isoformat(), post_urn, schedule_id))
            conn.commit()
            print(f"     ✓ Publicado con éxito en LinkedIn! ID Post: {post_urn}")
            logging.info(f"Publicado OK [{schedule_id}]: {post_urn}")
            
        except Exception as err:
            err_msg = str(err)
            new_retries = retry_count + 1
            new_status = 'failed' if new_retries >= max_retries else 'scheduled'
            
            c.execute("""
                UPDATE marketing_schedules
                SET retry_count = ?, status = ?, last_error = ?, last_error_at = ?
                WHERE id = ?
            """, (new_retries, new_status, err_msg, datetime.datetime.now().isoformat(), schedule_id))
            conn.commit()
            print(f"     ❌ Error al publicar [{schedule_id}]: {err_msg}")
            logging.error(f"Error [{schedule_id}]: {err_msg}")

    conn.close()

if __name__ == "__main__":
    run_dispatch()
