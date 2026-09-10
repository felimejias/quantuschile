#!/usr/bin/env python3
"""
Quantus Enterprise LinkedIn Marketing & Advertising Automation Engine (120 Ads Rotation + ERP Featured Spotlight)
----------------------------------------------------------------------------------------------------------------
Motor integral de publicidad y publicaciones automatizadas para Quantus Chile SpA.
Carga y rota secuencial o intercaladamente los 120 anuncios canónicos (20 por módulo):

  MÓDULO 1: RADAR DEL DIARIO OFICIAL (https://www.quantuschile.cl/do)
  MÓDULO 2: RADAR DE LICITACIONES (MERCADO PÚBLICO) (https://www.quantuschile.cl/licitaciones)
  MÓDULO 3: RADAR DE REMATES DE PROPIEDADES (JUDICIALES) (https://www.quantuschile.cl/remates)
  MÓDULO 4: REGISTRA TU MARCA (VIGILANCIA INAPI) (https://www.quantuschile.cl/marcas)
  MÓDULO 5: LEY N° 21.719 (PROTECCIÓN DE DATOS PERSONALES) (https://www.quantuschile.cl/checklist-ley-21719)
  MÓDULO 6: QUANTUS ERP (PUNTO DE VENTA E INVENTARIO) (https://www.quantuschile.cl/punto-de-venta)

Publica cada 1 hora rotando automáticamente a través de la API oficial de LinkedIn o Webhook de Zapier.
Incorpora anuncio destacado de Quantus ERP con Imagen y autocompletado inteligente con IA (3 veces al día en horarios punta de Chile).
"""

import os
import sys
import json
import sqlite3
import datetime
import argparse
import urllib.request
import urllib.parse
import urllib.error

try:
    import zoneinfo
    TZ_SANTIAGO = zoneinfo.ZoneInfo("America/Santiago")
except Exception:
    TZ_SANTIAGO = datetime.timezone(datetime.timedelta(hours=-3))

# Directorios base
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

DATA_DIR = os.path.join(BASE_DIR, "data")
REMATES_DB = os.path.join(DATA_DIR, "remates_radar.sqlite3")
MARKETING_DB = os.path.join(DATA_DIR, "marketing.sqlite3")
ADS_120_PATH = os.path.join(DATA_DIR, "linkedin_ads_120.json")
TOKEN_PATH = os.path.join(DATA_DIR, "linkedin_token.json")
STATE_PATH = os.path.join(DATA_DIR, "linkedin_rotation_state.json")

# Horarios estratégicos en Chile (Santiago) para el post destacado de Quantus ERP con Imagen:
# 09:00 (Apertura de negocios y retail), 14:00 (Post-almuerzo / Sobremesa), 20:00 (Cierre de jornada comercial)
ERP_FEATURED_HOURS = [9, 14, 20]
ERP_FEATURED_IMAGE_PATH = os.path.join(DATA_DIR, "img", "erp_barcode_scanner.png")

FEATURED_ERP_AD = {
    "id": 999,
    "module_id": 6,
    "module_code": "ERP_BARCODE_IA",
    "module_name": "QUANTUS ERP (AUTOCOMPLETADO INTELIGENTE CON IA)",
    "num_in_module": "PROMO_PILOTO",
    "hook": "Escaneas un código de barras. La IA busca en múltiples fuentes y completa nombre, marca, categoría y contenido neto por ti.",
    "landing_url": "https://www.quantuschile.cl/punto-de-venta",
    "image_path": ERP_FEATURED_IMAGE_PATH,
    "media_title": "Quantus ERP - Escaneo Inteligente con IA",
    "full_commentary": """Escaneas un código de barras. La IA busca en múltiples fuentes y completa nombre, marca, categoría y contenido neto por ti. Tú solo confirmas costo, precio y stock.

Un clic después, el producto está disponible en tu tienda online y en la caja — con el margen ya calculado.

Así estamos ayudando a pymes chilenas (partiendo por una ferretería piloto en Rancagua) a dejar de perder tiempo cargando inventario a mano.

Si esto te suena familiar, hablemos. 

#Retail #PyME #Chile #TecnologíaLocal"""
}

def get_db():
    db_path = MARKETING_DB if os.path.exists(MARKETING_DB) else REMATES_DB
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_history_table(conn):
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS linkedin_post_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad_id INTEGER,
                module_id INTEGER,
                pillar_code TEXT,
                pillar_name TEXT,
                target_audience TEXT,
                title TEXT,
                commentary TEXT,
                landing_url TEXT,
                posted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                source_item_id INTEGER,
                http_status INTEGER,
                response_raw TEXT,
                post_urn TEXT
            )
        """)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(linkedin_post_history)")
        cols = [col[1] for col in cur.fetchall()]
        for col_name in ["ad_id", "module_id", "pillar_code", "pillar_name", "landing_url", "source_item_id", "post_urn"]:
            if col_name not in cols:
                try:
                    conn.execute(f"ALTER TABLE linkedin_post_history ADD COLUMN {col_name} TEXT")
                except Exception:
                    pass

def load_all_ads():
    if not os.path.exists(ADS_120_PATH):
        raise FileNotFoundError(f"No se encontró el archivo {ADS_120_PATH}. Ejecuta scripts/build_linkedin_ads_120.py")
    with open(ADS_120_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def build_interleaved_order(ads):
    """
    Genera un orden intercalado para rotar un módulo distinto cada hora:
    Hora 1: Módulo 1 #1, Hora 2: Módulo 2 #1, ..., Hora 6: Módulo 6 #1,
    Hora 7: Módulo 1 #2, Hora 8: Módulo 2 #2, etc. (120 horas = 5 días de ciclo perfecto).
    """
    modules = {}
    for ad in ads:
        m_id = ad["module_id"]
        if m_id not in modules:
            modules[m_id] = []
        modules[m_id].append(ad)

    interleaved = []
    max_len = max(len(v) for v in modules.values())
    for item_idx in range(max_len):
        for m_id in sorted(modules.keys()):
            if item_idx < len(modules[m_id]):
                interleaved.append(modules[m_id][item_idx])
    return interleaved

def get_stored_token():
    if not os.path.exists(TOKEN_PATH):
        return None
    try:
        with open(TOKEN_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def get_user_profile(access_token):
    url = "https://api.linkedin.com/v2/userinfo"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "QuantusMarketing/1.0 (Macintosh; Intel Mac OS X 10_15_7)"
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

def upload_linkedin_image(access_token, author_urn, image_path):
    """
    Inicializa y sube una imagen binaria a LinkedIn via REST API v202604.
    """
    if not image_path or not os.path.exists(image_path):
        print(f"⚠️ Archivo de imagen no encontrado: {image_path}")
        return None

    try:
        init_url = "https://api.linkedin.com/rest/images?action=initializeUpload"
        init_payload = {
            "initializeUploadRequest": {
                "owner": author_urn
            }
        }
        headers_api = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "LinkedIn-Version": "202604",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        req_init = urllib.request.Request(
            init_url,
            data=json.dumps(init_payload).encode("utf-8"),
            headers=headers_api
        )
        with urllib.request.urlopen(req_init, timeout=20) as resp_init:
            init_res = json.loads(resp_init.read().decode("utf-8"))
            upload_url = init_res["value"]["uploadUrl"]
            image_urn = init_res["value"]["image"]

        with open(image_path, "rb") as f:
            image_bytes = f.read()

        req_upload = urllib.request.Request(
            upload_url,
            data=image_bytes,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "image/png"
            },
            method="PUT"
        )
        with urllib.request.urlopen(req_upload, timeout=30) as resp_up:
            if resp_up.status in [200, 201]:
                print(f"🖼️ Imagen binaria subida a LinkedIn exitosamente ({image_urn})")
                return image_urn
    except Exception as e:
        print(f"⚠️ Error subiendo imagen a LinkedIn: {e}")
        return None

def publish_to_linkedin(access_token, author_urn, commentary, image_path=None, media_title="Quantus Chile"):
    url = "https://api.linkedin.com/rest/posts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "LinkedIn-Version": "202604",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    payload = {
        "author": author_urn,
        "commentary": commentary,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "lifecycleState": "PUBLISHED"
    }

    if image_path and os.path.exists(image_path):
        img_urn = upload_linkedin_image(access_token, author_urn, image_path)
        if img_urn:
            payload["content"] = {
                "media": {
                    "title": media_title or "Quantus Chile",
                    "id": img_urn
                }
            }
            print(f"📎 Post vinculado con imagen URN: {img_urn}")

    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req, timeout=25) as resp:
        post_urn = resp.headers.get("x-restli-id") or resp.headers.get("X-Restli-Id") or "urn:li:share:published"
        raw_body = resp.read().decode("utf-8")
        return resp.status, post_urn, raw_body

def publish_to_zapier(webhook_url, title, commentary, landing_url):
    payload = {
        "title": title,
        "text": commentary,
        "url": landing_url,
        "source": "Quantus Chile LinkedIn Marketing Engine"
    }
    req = urllib.request.Request(
        webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw_body = resp.read().decode("utf-8")
        return resp.status, "zapier_webhook_dispatched", raw_body

def get_rotation_state():
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"total_published": 0, "last_index": -1, "last_posted_at": None}

def save_rotation_state(state):
    try:
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"⚠️ Error guardando estado de rotación: {e}")

def main():
    parser = argparse.ArgumentParser(description="Quantus Enterprise LinkedIn Marketing Engine (120 Ads + Featured ERP Spotlight)")
    parser.add_argument("--ad-id", type=int, help="Forzar un ID de anuncio específico (1 a 120)")
    parser.add_argument("--module", type=int, choices=range(1, 7), help="Forzar un módulo específico (1 a 6)")
    parser.add_argument("--order", choices=["interleaved", "sequential"], default="interleaved", help="Modo de rotación (interleaved = 1 módulo distinto cada hora; sequential = 1 al 120)")
    parser.add_argument("--interval-hours", type=float, default=1.0, help="Intervalo mínimo entre publicaciones en horas (default 1.0 hr)")
    parser.add_argument("--featured-erp", action="store_true", help="Forzar la publicación del anuncio destacado ERP con Imagen")
    parser.add_argument("--force", action="store_true", help="Publicar sin respetar el intervalo mínimo de espera")
    parser.add_argument("--dry-run", action="store_true", help="Generar texto y simular sin publicar a LinkedIn")
    args = parser.parse_args()

    conn = get_db()
    init_history_table(conn)
    ads = load_all_ads()

    ordered_ads = build_interleaved_order(ads) if args.order == "interleaved" else ads
    rotation_state = get_rotation_state()

    # 1. Verificar último post para evitar saturación (a menos que use --force)
    if not args.force and not args.dry_run:
        cur = conn.cursor()
        cur.execute("SELECT posted_at FROM linkedin_post_history ORDER BY id DESC LIMIT 1")
        last_row = cur.fetchone()
        last_time_str = last_row[0] if (last_row and last_row[0]) else rotation_state.get("last_posted_at")
        if last_time_str:
            try:
                last_time = datetime.datetime.fromisoformat(last_time_str)
                diff_hours = (datetime.datetime.now() - last_time).total_seconds() / 3600.0
                if diff_hours < args.interval_hours:
                    print(f"⏳ Post omitido: Última publicación fue hace {diff_hours:.2f} hrs (mínimo {args.interval_hours:.1f} hrs). Usa --force para forzar.")
                    return
            except Exception:
                pass

    # 2. Determinar si corresponde anuncio destacado de ERP o rotación normal de 120
    now_santiago = datetime.datetime.now(TZ_SANTIAGO)
    santiago_hour = now_santiago.hour
    today_str = now_santiago.strftime("%Y-%m-%d")
    current_slot_key = f"{today_str}_h{santiago_hour}"

    is_erp_slot = False
    if args.featured_erp:
        is_erp_slot = True
    elif not args.ad_id and not args.module:
        # Si la hora actual en Chile corresponde a uno de los 3 bloques estratégicos
        # y aún no se ha emitido en este bloque hoy:
        if santiago_hour in ERP_FEATURED_HOURS and rotation_state.get("last_featured_erp_slot") != current_slot_key:
            is_erp_slot = True

    if is_erp_slot:
        selected_ad = FEATURED_ERP_AD
        is_featured = True
        current_rotation_idx = rotation_state.get("last_index", -1)
    elif args.ad_id:
        selected_ad = next((a for a in ads if a["id"] == args.ad_id), ads[0])
        current_rotation_idx = ordered_ads.index(selected_ad) if selected_ad in ordered_ads else 0
        is_featured = False
    elif args.module:
        module_ads = [a for a in ordered_ads if a["module_id"] == args.module]
        selected_ad = module_ads[0] if module_ads else ads[0]
        current_rotation_idx = ordered_ads.index(selected_ad)
        is_featured = False
    else:
        # Flujo regular de rotación de las 120 piezas
        last_idx = rotation_state.get("last_index", -1)
        current_rotation_idx = (last_idx + 1) % len(ordered_ads)
        selected_ad = ordered_ads[current_rotation_idx]
        is_featured = False

    post_title = f"[{selected_ad['module_code']} #{selected_ad['num_in_module']}] {selected_ad['hook'][:80]}"
    post_commentary = selected_ad["full_commentary"]
    landing_url = selected_ad["landing_url"]
    image_to_attach = selected_ad.get("image_path")
    media_title = selected_ad.get("media_title", post_title)

    print(f"\n=======================================================")
    if is_featured:
        print(f"⭐ ANUNCIO DESTACADO ERP CON IMAGEN [SPOTLIGHT 3x DÍA]")
    else:
        print(f"🚀 ANUNCIO SELECCIONADO [{current_rotation_idx + 1}/120]")
    print(f"📌 MÓDULO {selected_ad['module_id']}: {selected_ad['module_name']} (Pieza #{selected_ad['num_in_module']})")
    print(f"🎯 HOOK: {selected_ad['hook']}")
    print(f"🔗 LANDING URL: {landing_url}")
    if image_to_attach:
        print(f"🖼️ IMAGEN ADJUNTA: {image_to_attach}")
    print(f"=======================================================\n")
    print(post_commentary)
    print(f"\n=======================================================\n")

    if args.dry_run:
        print("🔍 Modo --dry-run activado. Contenido verificado exitosamente (no enviado a LinkedIn).")
        return

    # 3. Obtener Configuración / Token de LinkedIn
    config = {}
    config_path = os.path.join(DATA_DIR, "linkedin_config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as cf:
                config = json.load(cf)
        except Exception:
            pass

    token_info = get_stored_token()
    access_token = (token_info.get("access_token") if token_info else None) or os.getenv("LINKEDIN_ACCESS_TOKEN")
    zapier_webhook = os.getenv("ZAPIER_LINKEDIN_WEBHOOK") or os.getenv("ZAPIER_LINKEDIN_WEBHOOK_URL") or config.get("zapier_webhook")

    if not access_token and not zapier_webhook:
        auth_url = "https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=" + config.get("client_id", "77stfy5lo365vx") + "&redirect_uri=" + urllib.parse.quote(config.get("redirect_uri", "https://www.quantuschile.cl/marketing/api/auth/linkedin/callback")) + "&state=quantus_auth&scope=w_member_social+openid+profile+email"
        print("❌ Error: No existe un token de LinkedIn en data/linkedin_token.json ni webhook de Zapier configurado.")
        print(f"\n👉 Para autorizar tu cuenta de LinkedIn con 1 clic, abre este enlace en tu navegador:\n{auth_url}\n")
        return

    now_iso = datetime.datetime.now().isoformat()

    # 4. Despacho por API Oficial de LinkedIn
    if access_token:
        try:
            profile = get_user_profile(access_token)
            author_urn = f"urn:li:person:{profile.get('sub', profile.get('id', 'authorized'))}"
            print(f"👤 Conectado a LinkedIn como: {profile.get('name', 'Usuario Autorizado')} ({author_urn})")
        except Exception as e:
            print(f"⚠️ Aviso al consultar perfil de LinkedIn: {e}")
            author_urn = os.getenv("LINKEDIN_AUTHOR_URN") or "urn:li:person:authorized"

        target_authors = [
            {"type": "PERSON", "urn": author_urn, "label": f"Perfil Personal ({profile.get('name', 'Felipe') if 'profile' in locals() else 'Felipe'})"}
        ]

        org_urn = config.get("org_urn") or os.getenv("LINKEDIN_ORG_URN") or os.getenv("LINKEDIN_AUTHOR_URN")
        if org_urn:
            if not org_urn.startswith("urn:li:organization:"):
                org_urn = f"urn:li:organization:{org_urn}"
            target_authors.append({"type": "ORGANIZATION", "urn": org_urn, "label": "Página de Empresa Quantus Chile SpA"})

        for target in target_authors:
            print(f"\n📡 Despachando hacia: {target['label']} ({target['urn']})...")
            try:
                status, post_urn, raw_resp = publish_to_linkedin(
                    access_token,
                    target["urn"],
                    post_commentary,
                    image_path=image_to_attach,
                    media_title=media_title
                )
                print(f"✅ ¡PUBLICADO CON ÉXITO EN {target['type']}! HTTP {status}")
                print(f"📌 Post URN: {post_urn}")

                with conn:
                    conn.execute("""
                        INSERT INTO linkedin_post_history 
                        (ad_id, module_id, pillar_code, pillar_name, target_audience, title, commentary, landing_url, http_status, response_raw, post_urn)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        selected_ad["id"],
                        selected_ad["module_id"],
                        selected_ad["module_code"],
                        f"{selected_ad['module_name']} [{target['type']}]",
                        selected_ad["module_name"],
                        post_title,
                        post_commentary,
                        landing_url,
                        status,
                        raw_resp,
                        post_urn
                    ))
                print(f"💾 Registro guardado en base de datos para {target['label']}.")

            except urllib.error.HTTPError as e:
                err_msg = e.read().decode("utf-8", errors="ignore")
                print(f"❌ Error HTTP {e.code} al publicar en {target['label']}: {err_msg}")
            except Exception as e:
                print(f"❌ Error inesperado al publicar en {target['label']}: {e}")

    # 5. Despacho alternativo por Webhook de Zapier
    elif zapier_webhook:
        print(f"\n📡 Despachando publicación a Zapier Webhook...")
        try:
            status, post_urn, raw_resp = publish_to_zapier(zapier_webhook, post_title, post_commentary, landing_url)
            print(f"✅ Publicación enviada con éxito a Zapier (HTTP {status})")
            with conn:
                conn.execute("""
                    INSERT INTO linkedin_post_history 
                    (ad_id, module_id, pillar_code, pillar_name, target_audience, title, commentary, landing_url, http_status, response_raw, post_urn)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    selected_ad["id"],
                    selected_ad["module_id"],
                    selected_ad["module_code"],
                    f"{selected_ad['module_name']} [ZAPIER_WEBHOOK]",
                    selected_ad["module_name"],
                    post_title,
                    post_commentary,
                    landing_url,
                    status,
                    raw_resp,
                    post_urn
                ))
            print("💾 Registro guardado en base de datos.")
        except Exception as e:
            print(f"❌ Error al enviar a Zapier: {e}")

    # Actualizar estado de rotación
    if is_featured:
        rotation_state["last_featured_erp_slot"] = current_slot_key
        rotation_state["last_posted_at"] = now_iso
        rotation_state["total_published"] = rotation_state.get("total_published", 0) + 1
        save_rotation_state(rotation_state)
        print(f"⭐ Publicación destacada ERP con Imagen registrada. Cadencia de las 120 intacta (siguiente regular: #{(current_rotation_idx + 1) % len(ordered_ads) + 1}/120).")
    else:
        rotation_state["last_index"] = current_rotation_idx
        rotation_state["last_ad_id"] = selected_ad["id"]
        rotation_state["last_posted_at"] = now_iso
        rotation_state["total_published"] = rotation_state.get("total_published", 0) + 1
        save_rotation_state(rotation_state)
        print(f"🔄 Estado de rotación actualizado: Próximo anuncio será el índice {(current_rotation_idx + 1) % len(ordered_ads) + 1}/120.")

if __name__ == "__main__":
    main()
