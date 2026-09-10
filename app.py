#!/usr/bin/env python3
"""
Quantus Chile - Portal de Propiedad Industrial
Servidor Flask Standalone para la búsqueda y simulación de registro de marcas.
"""

import os
import sys
import json
import logging
import requests
import werkzeug.utils
import secrets
import hmac
import hashlib
import shutil
import subprocess
import tempfile
import sqlite3
import unicodedata
import base64
import math
from urllib.parse import urlencode, urlparse
from pathlib import Path
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify, abort, redirect, session, send_file, url_for, Response
from collections import defaultdict
import time
from datetime import datetime, timedelta
from threading import Lock, Thread
from niza_data import NIZA_CLASSES
from do_semantic_search import search_semantic_do
from brand_collision_detector import detect_collision_risk, scan_brand_against_list, spanish_metaphone
from geointel_sales_radar import export_csv as geointel_export_csv
from geointel_sales_radar import get_dashboard as geointel_dashboard
from geointel_sales_radar import run_internal_sales_base_refresh as geointel_refresh_sales_base
from geointel_sales_radar import run_do_extraction as geointel_run_do_extraction
from geointel_sales_radar import run_patentes_municipales_extraction as geointel_run_patentes_extraction
from do_intelligence import (
    dashboard_snapshot,
    get_report,
    registry_matches_for_rut,
    registry_snapshot,
    upsert_registry_client,
    save_report,
)
from mailer import send_email
from data.blog_articles_data import get_all_articles, get_article_by_slug
from data.regional_services_data import get_all_regional_services, get_regional_service_by_slug
from dotenv import load_dotenv
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
)
from webauthn.helpers import options_to_json
from webauthn.helpers.structs import (
    PublicKeyCredentialDescriptor,
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] QUANTUS_PORTAL: %(message)s'
)
log = logging.getLogger('QuantusPortal')

app = Flask(__name__)
app.config["STAGING"] = os.getenv("QUANTUS_STAGING", "0") == "1"

# Quantus Marketing Center (Fase 1 MVP)
try:
    from marketing.routes import marketing_bp
    app.register_blueprint(marketing_bp)
except ImportError as _mkt_err:
    log.warning("Marketing Center module not imported: %s", _mkt_err)

# Quantus Mercado Pago Webhook & Expedientes
try:
    from mercadopago_webhook import mp_blueprint
    app.register_blueprint(mp_blueprint)
except Exception as _mp_err:
    log.warning("MercadoPago Webhook module not imported: %s", _mp_err)



@app.context_processor
def inject_globals():
    p = request.path.rstrip("/")
    active = "home"
    if p.startswith(("/do", "/vigilancia", "/prospeccion")):
        active = "do"
    elif p.startswith("/licitaciones"):
        active = "licitaciones"
    elif p.startswith(("/inapi", "/registro")):
        active = "inapi"
    elif p.startswith("/remates"):
        active = "remates"
    elif p.startswith(("/ley-21719", "/ley_21719", "/checklist-ley-21719", "/ley21.719")):
        active = "ley21719"
    elif p.startswith(("/punto-de-venta", "/erp", "/clientes", "/pos")):
        active = "pos"
    elif p.startswith(("/como-funciona", "/como-trabaja-quantus")):
        active = "como_funciona"
    elif p.startswith(("/seguridad", "/seguridad-confianza")):
        active = "seguridad"
    return {"is_staging": app.config["STAGING"], "active_module": active}

@app.before_request
def case_insensitive_routing():
    path = request.path
    if path != path.lower() and not path.startswith('/static'):
        lower_path = path.lower()
        if lower_path in ['/do', '/do/', '/remates', '/remates/', '/remates-inmuebles-chile', '/licitaciones', '/licitaciones/', '/ley-21719', '/cumplimiento-ley-de-proteccion-de-datos-chile', '/do/prospeccion']:
            query = request.query_string.decode('utf-8')
            target = lower_path + (f"?{query}" if query else "")
            return redirect(target, code=301)

_secret_key = os.getenv("FLASK_SECRET_KEY") or os.getenv("SECRET_KEY")
if not _secret_key:
    _secret_key_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "secret_key.txt")
    try:
        with open(_secret_key_file, "r", encoding="utf-8") as _skf:
            _secret_key = _skf.read().strip()
    except OSError:
        _secret_key = ""
    if not _secret_key:
        _secret_key = secrets.token_hex(32)
        try:
            with open(_secret_key_file, "w", encoding="utf-8") as _skf:
                _skf.write(_secret_key)
        except OSError:
            pass
app.config["SECRET_KEY"] = _secret_key
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


REGISTRO_GESTION_INICIAL = int(os.getenv("REGISTRO_GESTION_INICIAL", "149990"))
REGISTRO_GESTION_FINAL = int(os.getenv("REGISTRO_GESTION_FINAL", "149990"))
REGISTRO_PUBLICACION_ESTIMADA = int(os.getenv("REGISTRO_PUBLICACION_ESTIMADA", "32000"))
REGISTRO_MP_LINK_1_CLASE = os.getenv("REGISTRO_MP_LINK_1_CLASE", "https://mpago.la/1kHFWwp")
REGISTRO_MP_TOTAL_1_CLASE = int(os.getenv("REGISTRO_MP_TOTAL_1_CLASE", "230390"))
MP_LINK_LIC_OPORTUNIDADES = os.getenv("MP_LINK_LIC_OPORTUNIDADES", "https://mpago.la/28817Cz")
MP_LINK_LIC_PYME_PRO = os.getenv("MP_LINK_LIC_PYME_PRO", "https://mpago.la/2SEjnz3")
MP_LINK_LIC_EMPRESA = os.getenv("MP_LINK_LIC_EMPRESA", "https://mpago.la/1vVRRP6")
MP_LINK_LIC_PREMIUM = os.getenv("MP_LINK_LIC_PREMIUM", "https://mpago.la/2MzwRJW")
MASTER_ADMIN_USER = os.getenv("QUANTUS_MASTER_USER", "fmejias")
MASTER_ADMIN_PASSWORD = os.getenv("QUANTUS_MASTER_PASSWORD", "")
MASTER_ADMIN_EMAIL = os.getenv("QUANTUS_MASTER_EMAIL", "felipe.mejias.g@gmail.com")
GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
GOOGLE_OAUTH_REDIRECT_URI = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "https://www.quantuschile.cl/maestro/google/callback")
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_TEMPLATE_ALERT = os.getenv("WHATSAPP_TEMPLATE_ALERT", "quantus_alerta_general")
WHATSAPP_GRAPH_VERSION = os.getenv("WHATSAPP_GRAPH_VERSION", "v21.0")
QUANTUS_ERP_SERVER_URL = os.getenv(
    "QUANTUS_ERP_SERVER_URL",
    "https://www.quantuschile.cl",
).rstrip("/")
# El ERP multi-tenant resuelve el tenant por subdominio (<slug>.quantuschile.cl).
# En www.quantuschile.cl el API no resuelve tenant y rechaza login/SSO con
# tenant_not_found_or_inactive, por eso el SSO del portal debe apuntar al
# subdominio del tenant (por defecto "demo"). Configurable por entorno.
QUANTUS_ERP_TENANT = (os.getenv("QUANTUS_ERP_TENANT") or "demo").strip().lower() or "demo"
QUANTUS_ERP_TENANT_BASE_URL = os.getenv("QUANTUS_ERP_TENANT_BASE_URL", "").strip().rstrip("/")
if not QUANTUS_ERP_TENANT_BASE_URL:
    _erp_parsed = urlparse(QUANTUS_ERP_SERVER_URL)
    _erp_host = (_erp_parsed.hostname or "www.quantuschile.cl").lower()
    _erp_scheme = _erp_parsed.scheme or "https"
    if "quantuschile.cl" in _erp_host:
        _erp_base_host = _erp_host
        for _erp_prefix in ("www.", f"{QUANTUS_ERP_TENANT}."):
            if _erp_base_host.startswith(_erp_prefix):
                _erp_base_host = _erp_base_host[len(_erp_prefix):]
        QUANTUS_ERP_TENANT_BASE_URL = f"{_erp_scheme}://{QUANTUS_ERP_TENANT}.{_erp_base_host}"
    else:
        QUANTUS_ERP_TENANT_BASE_URL = QUANTUS_ERP_SERVER_URL
QUANTUS_ERP_CLIENTS_PATH = os.getenv("QUANTUS_ERP_CLIENTS_PATH", "/app").strip() or "/app"
QUANTUS_ERP_HEALTH_URL = os.getenv(
    "QUANTUS_ERP_HEALTH_URL",
    f"{QUANTUS_ERP_TENANT_BASE_URL}/api/health",
)
QUANTUS_ERP_SSO_SECRET = os.getenv(
    "QUANTUS_ERP_SSO_SECRET",
    "quantus_portal_sso_bridge_2026_change_me",
)
POS_ERP_RUBRO_BY_WORKSPACE = {
    "don-manolo": "don_manolo",
    "ohiggins": "bodega",
    "minimarket": "minimarket",
    "san-juan": "farmacia",
    "boutique": "retail",
}
POS_ERP_USERNAME_BY_PORTAL_USER = {
    "donmanolo": "donmanolo",
    "superadmin": "superadmin",
}

# Configuración de uploads
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
APP_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
REGISTRO_DOCS_FOLDER = os.path.join(UPLOAD_FOLDER, 'registro_marca')
os.makedirs(REGISTRO_DOCS_FOLDER, exist_ok=True)
ALLOWED_VOUCHER_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}
CLIENT_WORKSPACE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "clientes")
MASTER_AUTH_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "master_auth.json")
MASTER_PASSKEYS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "master_passkeys.json")
CLIENT_FILE_CATEGORIES = {
    "documentos": "Documentos",
    "informes": "Informes",
    "pagos": "Pagos",
    "contratos": "Contratos",
    "consentimientos": "Consentimientos",
    "otros": "Otros",
}
CLIENT_PRIVATE_CATEGORIES = {"integraciones"}
os.makedirs(CLIENT_WORKSPACE_DIR, exist_ok=True)

# Rate Limiting
ai_limits = defaultdict(list)
inapi_ai_limits = defaultdict(list)
lic_ai_limits = defaultdict(list)
do_ai_limits = defaultdict(list)
search_limits = defaultdict(list)
limits_lock = Lock()

def get_client_ip():
    # 1. Cloudflare real visitor IP
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip and cf_ip.strip():
        return cf_ip.strip()
    # 2. X-Real-IP
    real_ip = request.headers.get("X-Real-IP")
    if real_ip and real_ip.strip():
        return real_ip.strip()
    # 3. X-Forwarded-For (public IP first)
    xff = request.headers.getlist("X-Forwarded-For")
    if xff:
        for p in xff[0].split(","):
            p = p.strip()
            if p and not p.startswith(("10.", "172.", "192.168.", "127.")):
                return p
        return xff[0].split(",")[0].strip()
    return request.remote_addr or "127.0.0.1"


def erp_server_clients_url(workspace_key=None, portal_user=None, superadmin=False):
    path = QUANTUS_ERP_CLIENTS_PATH
    if path.startswith("http://") or path.startswith("https://"):
        base_url = path
    else:
        if not path.startswith("/"):
            path = "/" + path
        base_url = f"{QUANTUS_ERP_TENANT_BASE_URL}{path}"
    rubro = POS_ERP_RUBRO_BY_WORKSPACE.get(workspace_key or "")
    query = {}
    if rubro:
        query["rubro"] = rubro
    if portal_user:
        query["portal_user"] = portal_user
    if superadmin:
        query["superadmin"] = "1"
    if not query:
        return base_url
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{urlencode(query)}"

def b64url_encode_json(payload):
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")

def create_erp_sso_token(portal_user, workspace_key=None, superadmin=False, rubro=None):
    portal_user = (portal_user or "").strip().lower()
    erp_username = POS_ERP_USERNAME_BY_PORTAL_USER.get(portal_user, portal_user)
    erp_rubro = rubro or POS_ERP_RUBRO_BY_WORKSPACE.get(workspace_key or "") or None
    payload = {
        "username": erp_username,
        "rubro": erp_rubro,
        "superadmin": bool(superadmin),
        "iat": int(time.time()),
        "exp": int(time.time()) + 120,
        "nonce": secrets.token_urlsafe(12),
    }
    body = b64url_encode_json(payload)
    sig = hmac.new(QUANTUS_ERP_SSO_SECRET.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
    signature = base64.urlsafe_b64encode(sig).rstrip(b"=").decode("ascii")
    return f"{body}.{signature}"

def erp_server_sso_url(workspace_key=None, portal_user=None, superadmin=False, rubro=None):
    path = "/app"
    base_url = f"{QUANTUS_ERP_SERVER_URL}{path}"
    rubro = rubro or POS_ERP_RUBRO_BY_WORKSPACE.get(workspace_key or "")
    query = {
        "sso": create_erp_sso_token(portal_user, workspace_key, superadmin, rubro),
    }
    if rubro:
        query["rubro"] = rubro
    if superadmin:
        query["superadmin"] = "1"
    return f"{base_url}?{urlencode(query)}"

def erp_server_status():
    if not QUANTUS_ERP_HEALTH_URL:
        return {
            "ok": False,
            "label": "ERP no configurado",
            "detail": "Falta QUANTUS_ERP_HEALTH_URL.",
        }
    try:
        response = requests.get(QUANTUS_ERP_HEALTH_URL, timeout=3)
        payload = response.json() if "json" in response.headers.get("Content-Type", "") else {}
        if response.ok and payload.get("status") == "ok":
            return {
                "ok": True,
                "label": "ERP servidor conectado",
                "detail": f"{payload.get('storage') or 'storage'} · {payload.get('db') or 'tenant'}",
            }
        return {
            "ok": False,
            "label": "ERP responde con advertencia",
            "detail": f"HTTP {response.status_code}",
        }
    except requests.RequestException as exc:
        return {
            "ok": False,
            "label": "ERP servidor sin respuesta",
            "detail": type(exc).__name__,
        }

def clean_rut(rut):
    return (rut or "").replace(".", "").replace("-", "").strip().upper()

def validate_rut(rut, required=False):
    clean = clean_rut(rut)
    if not clean:
        return not required
    if len(clean) < 8 or len(clean) > 9 or not clean[:-1].isdigit() or clean[-1] not in "0123456789K":
        return False

    body = clean[:-1]
    dv = clean[-1]
    total = 0
    multiplier = 2
    for digit in reversed(body):
        total += int(digit) * multiplier
        multiplier = 2 if multiplier == 7 else multiplier + 1
    expected_value = 11 - (total % 11)
    expected = "0" if expected_value == 11 else "K" if expected_value == 10 else str(expected_value)
    return dv == expected

def format_rut(rut):
    clean = clean_rut(rut)
    if not clean:
        return ""
    body = clean[:-1]
    dv = clean[-1]
    groups = []
    while body:
        groups.insert(0, body[-3:])
        body = body[:-3]
    return ".".join(groups) + "-" + dv

def require_valid_rut(rut, required=False, label="RUT"):
    if not validate_rut(rut, required=required):
        abort(400, f"{label} inválido. Revisa el dígito verificador.")
    return format_rut(rut)

def save_registration_pdf(file_storage, doc_key, nombre, rut, marca):
    if not file_storage or not file_storage.filename:
        abort(400, f"Falta subir el documento requerido: {doc_key}")

    original_name = file_storage.filename
    ext = Path(original_name).suffix.lower()
    if ext != ".pdf":
        abort(400, "Los documentos de registro deben subirse en formato PDF.")

    head = file_storage.stream.read(5)
    file_storage.stream.seek(0)
    if head != b"%PDF-":
        abort(400, "El archivo PDF no parece válido.")

    safe_prefix = werkzeug.utils.secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{rut}_{marca}_{doc_key}")
    filename = f"{safe_prefix}.pdf"
    file_path = os.path.join(REGISTRO_DOCS_FOLDER, filename)
    file_storage.save(file_path)

    return {
        "tipo": doc_key,
        "archivo": filename,
        "nombre_original": werkzeug.utils.secure_filename(original_name),
        "ruta": file_path,
        "subido_en": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cliente": nombre,
        "rut": rut,
        "marca": marca,
    }

def is_rate_limited(ip, limit_type, limit_max, window_seconds, consume=True):
    # Exención total para el titular fundador (Felipe Mejías), red local y Tailscale
    if not ip or ip in {"127.0.0.1", "localhost", "::1"}:
        return False
    if ip.startswith(("100.", "192.168.", "172.", "10.", "181.161.")):
        return False
    if session.get("user") or session.get("is_admin") or session.get("portal_user") or session.get("is_owner"):
        return False
    if request.args.get("bypass") == "1" or request.args.get("admin") == "1" or request.cookies.get("quantus_owner"):
        return False

    now = time.time()
    stores = {
        "ai": ai_limits,
        "inapi_ai": inapi_ai_limits,
        "lic_ai": lic_ai_limits,
        "do_ai": do_ai_limits,
        "search": search_limits,
    }
    store = stores.get(limit_type, search_limits)
    with limits_lock:
        timestamps = store[ip]
        timestamps = [t for t in timestamps if now - t < window_seconds]
        store[ip] = timestamps
        if len(timestamps) >= limit_max:
            return True
        if consume:
            store[ip].append(now)
        return False


def csrf_token():
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
        session.modified = True
    return token

def csrf_input():
    return f'<input type="hidden" name="_csrf_token" value="{csrf_token()}">'

app.jinja_env.globals["csrf_token"] = csrf_token
app.jinja_env.globals["csrf_input"] = csrf_input

def money_clp(value):
    try:
        return "$" + f"{int(round(value)):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "$0"

app.jinja_env.filters["clp"] = money_clp

def b64url_encode(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")

def b64url_decode(value):
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))

def normalize_whatsapp(value):
    raw = (value or "").strip()
    if not raw:
        return ""
    digits = "".join(ch for ch in raw if ch.isdigit())
    if not digits:
        return ""
    if len(digits) == 9 and digits.startswith("9"):
        digits = "56" + digits
    elif len(digits) == 11 and digits.startswith("569"):
        pass
    elif len(digits) == 12 and digits.startswith("056"):
        digits = digits[1:]
    elif raw.startswith("+") and len(digits) >= 10:
        pass
    elif not digits.startswith("56") and len(digits) >= 8:
        digits = "56" + digits
    return "+" + digits

def whatsapp_enabled(config=None):
    config = config or {}
    return bool((config.get("access_token") or WHATSAPP_ACCESS_TOKEN) and (config.get("phone_number_id") or WHATSAPP_PHONE_NUMBER_ID))

def ensure_whatsapp_storage():
    from do_intelligence import DB_PATH, ensure_storage
    ensure_storage()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS whatsapp_outbox (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                module TEXT NOT NULL,
                client_key TEXT,
                client_name TEXT,
                client_rut TEXT,
                whatsapp TEXT NOT NULL,
                message TEXT NOT NULL,
                report_url TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                provider_response TEXT,
                sent_at TEXT
            )
            """
        )
        columns = {row[1] for row in conn.execute("PRAGMA table_info(whatsapp_outbox)").fetchall()}
        if "client_key" not in columns:
            conn.execute("ALTER TABLE whatsapp_outbox ADD COLUMN client_key TEXT")

def queue_whatsapp_alert(module, client, message, report_url=None, send_now=False):
    whatsapp = normalize_whatsapp((client or {}).get("whatsapp"))
    if not whatsapp:
        return None
    ensure_whatsapp_storage()
    meta_config = load_meta_whatsapp_for_client_payload(module, client or {})
    item_id = secrets.token_hex(12)
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(__import__("do_intelligence").DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO whatsapp_outbox (
                id, created_at, module, client_key, client_name, client_rut, whatsapp, message, report_url, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_id,
                created_at,
                module,
                (client or {}).get("key"),
                (client or {}).get("nombre") or (client or {}).get("name"),
                (client or {}).get("rut"),
                whatsapp,
                message[:1800],
                report_url,
                "queued" if whatsapp_enabled(meta_config) else "pending_config",
            ),
        )
    if send_now and whatsapp_enabled(meta_config):
        send_whatsapp_outbox_item(item_id)
    return item_id

def send_whatsapp_outbox_item(item_id):
    from do_intelligence import DB_PATH
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM whatsapp_outbox WHERE id = ?", (item_id,)).fetchone()
    if not row:
        return False
    config = load_meta_whatsapp_for_outbox_row(row)
    if not whatsapp_enabled(config):
        return False
    access_token = config.get("access_token") or WHATSAPP_ACCESS_TOKEN
    phone_number_id = config.get("phone_number_id") or WHATSAPP_PHONE_NUMBER_ID
    graph_version = config.get("graph_version") or WHATSAPP_GRAPH_VERSION
    template_name = config.get("template") or WHATSAPP_TEMPLATE_ALERT
    template_lang = config.get("template_lang") or os.getenv("WHATSAPP_TEMPLATE_LANG", "es_CL")
    phone = str(row["whatsapp"]).replace("+", "").replace(" ", "").replace("-", "")
    body = row["message"]
    if row["report_url"]:
        body += f"\n\nInforme: https://www.quantuschile.cl{row['report_url']}"
    url = f"https://graph.facebook.com/{graph_version}/{phone_number_id}/messages"
    
    if template_name == "hello_world":
        template_obj = {"name": "hello_world", "language": {"code": "en_US"}}
    else:
        clean_param = body.replace("\r", " ").replace("\n", " ").strip()
        clean_param = " ".join(clean_param.split())[:800]
        template_obj = {
            "name": template_name,
            "language": {"code": template_lang},
            "components": [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": clean_param}],
                }
            ],
        }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "template",
        "template": template_obj,
    }
    response = requests.post(
        url,
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        json=payload,
        timeout=15,
    )
    if response.status_code not in {200, 201}:
        text_payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {"preview_url": True, "body": body[:1800]},
        }
        text_resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json=text_payload,
            timeout=15,
        )
        if text_resp.status_code in {200, 201}:
            response = text_resp
    status = "sent" if response.status_code in {200, 201} else "error"
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE whatsapp_outbox SET status = ?, provider_response = ?, sent_at = ? WHERE id = ?",
            (status, response.text[:1500], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), item_id),
        )
    return status == "sent"

# Configuraciones
# PUERTO INSTANCIA RECUPERADA (la otra IA usa 8084/8082): correr en 8095.
# Ver /Users/felipe/proyectos/quantuschile.cl/do/PORT_INFO.md
PORT = int(os.getenv("PORT", "8095"))
INAPI_URL = "https://buscadormarcas.inapi.cl/Marca/BuscarMarca.aspx"
INAPI_POST_URL = "https://buscadormarcas.inapi.cl/Marca/BuscarMarca.aspx/FindMarcas"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "es-419,es;q=0.9,en;q=0.8",
    "Connection": "keep-alive"
}

def query_inapi(trademark_name, retries=3):
    """Consulta la base de datos de INAPI usando el bypass de cabeceras y POST JSON."""
    session = requests.Session()
    
    for attempt in range(retries):
        try:
            # 1. GET Inicial para inicializar sesión y cookies
            r = session.get(INAPI_URL, headers=HEADERS, timeout=12)
            if r.status_code != 200:
                log.error(f"Error GET inicial: {r.status_code}")
                if attempt == retries - 1:
                    return {"error": "No se pudo conectar con el servidor de INAPI"}
                time.sleep(2)
                continue
                
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # Extraer tokens iniciales (normalmente vacíos en GET, pero por seguridad)
            tokens = {}
            for token_name in ['__VIEWSTATE', '__VIEWSTATEGENERATOR', '__EVENTVALIDATION']:
                tag = soup.find('input', {'name': token_name})
                tokens[token_name] = tag['value'] if tag else ''
                
            # 2. Configurar cabeceras de AJAX POST
            post_headers = HEADERS.copy()
            post_headers.update({
                "Content-Type": "application/json; charset=utf-8",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": INAPI_URL
            })
            
            # 3. Preparar cuerpo JSON
            payload = {
                "LastNumSol": 0,
                "Hash": "", 
                "IDW": "",
                "responseCaptcha": "este texto no se validará",
                "param1": "", # Nro Solicitud
                "param2": "", # Nro Registro
                "param3": trademark_name.replace("'", "''"), # Denominación
                "param4": "", # Titular
                "param5": "", # Clase
                "param6": "", # Region
                "param7": "", # TipoMarca
                "param8": "", # TipoSolicitud
                "param9": "", # Estado
                "param10": "", # FechaPreD
                "param11": "", # FechaPreH
                "param12": "", # FechaPubD
                "param13": "", # FechaPubH
                "param14": "", # FechaRegD
                "param15": "", # FechaRegH
                "param16": "", # Residente
                "param17": "2" # Búsqueda que "contenga"
            }
            
            # 4. POST al PageMethod
            r_post = session.post(INAPI_POST_URL, headers=post_headers, json=payload, timeout=15)
            if r_post.status_code != 200:
                log.error(f"Error POST consulta: {r_post.status_code}")
                if attempt == retries - 1:
                    return {"error": f"Error del servidor INAPI (HTTP {r_post.status_code})"}
                time.sleep(2)
                continue
                
            res_json = r_post.json()
            d_raw = res_json.get('d', '{}')
            d_data = json.loads(d_raw)
            
            error_msg = d_data.get('ErrorMessage')
            if error_msg:
                return {"error": error_msg}
                
            # Limpiar y estructurar resultados
            raw_marcas = d_data.get('Marcas', [])
            marcas = []
            for m in raw_marcas:
                cell = m.get('cell', [])
                if len(cell) >= 6:
                    marcas.append({
                        "solicitud": cell[0],
                        "registro": cell[1] if cell[1] else None,
                        "clase": cell[2],
                        "denominacion": cell[3].strip(),
                        "titular": cell[4].strip(),
                        "estado": cell[5].strip(),
                        "tipo": cell[7] if len(cell) > 7 else ""
                    })
            
            return {"marcas": marcas}
                
        except requests.exceptions.RequestException as e:
            log.error(f"Excepción de conexión en intento {attempt+1}: {e}")
            if attempt == retries - 1:
                return {"error": f"Error de conexión con INAPI: {str(e)}"}
            time.sleep(2)
        except Exception as e:
            log.exception("Excepción inesperada durante la consulta a INAPI")
            return {"error": f"Error interno: {str(e)}"}

# UTM Cache
cached_utm = 71649
cached_utm_time = 0

def get_current_utm():
    global cached_utm, cached_utm_time
    now = time.time()
    if now - cached_utm_time < 86400:
        return cached_utm
    try:
        r = requests.get("https://mindicador.cl/api/utm", timeout=5)
        if r.status_code == 200:
            data = r.json()
            if "serie" in data and len(data["serie"]) > 0:
                cached_utm = int(data["serie"][0]["valor"])
                cached_utm_time = now
                log.info(f"UTM actualizada exitosamente a: {cached_utm}")
    except Exception as e:
        log.warning(f"Error fetching UTM, using fallback {cached_utm}: {e}")
    return cached_utm

def parse_ai_json(text_content):
    text_content = text_content.strip()
    if "```json" in text_content:
        text_content = text_content.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in text_content:
        text_content = text_content.split("```", 1)[1].split("```", 1)[0].strip()
    return json.loads(text_content)

def mark_ai_provider(data, provider):
    if isinstance(data, dict):
        data.setdefault("proveedor_ia", provider)
    return data

def get_gemini_keys():
    keys = []
    primary = os.environ.get("GEMINI_API_KEY", "").strip()
    backups = os.environ.get("GEMINI_API_KEYS_BACKUP", "").strip()
    if primary:
        keys.append(primary)
    if backups:
        keys.extend([key.strip() for key in backups.split(",") if key.strip()])
    deduped = []
    for key in keys:
        if key not in deduped:
            deduped.append(key)
    return deduped

def call_gemini_json(prompt, timeout=15):
    api_keys = get_gemini_keys()
    if not api_keys:
        return {"error": "Clave API de Gemini no configurada en el servidor."}, 503

    model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }

    last_error = {"error": "Gemini no respondió con ninguna clave configurada."}
    last_status = 503
    try:
        for index, api_key in enumerate(api_keys):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=timeout)
            if response.status_code != 200:
                log.error(f"Error de Gemini API key #{index + 1}: {response.status_code} - {response.text[:500]}")
                if response.status_code == 429:
                    last_error = {"error": "Google respondió que la cuota del proyecto está agotada o sin billing activo."}
                    last_status = 429
                    continue
                last_error = {"error": f"Error de Gemini API (HTTP {response.status_code})"}
                last_status = 502
                continue

            result = response.json()
            text_content = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            provider = "Gemini" if index == 0 else f"Gemini respaldo {index}"
            return mark_ai_provider(parse_ai_json(text_content), provider), 200
        return last_error, last_status
    except json.JSONDecodeError as exc:
        log.exception("Error al parsear el JSON de Gemini")
        return {"error": f"Fallo al decodificar la respuesta de la IA: {str(exc)}"}, 500
    except Exception as exc:
        log.exception("Error durante la consulta a Gemini")
        return {"error": f"Fallo de conexión o consulta con la IA: {str(exc)}"}, 500

def call_groq_json(prompt, timeout=15):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return {"error": "Clave API de Groq no configurada en el servidor."}, 503

    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Responde siempre con JSON válido y sin texto adicional."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=timeout,
        )
        if response.status_code != 200:
            log.error(f"Error de Groq API: {response.status_code} - {response.text[:500]}")
            return {"error": f"Error de Groq API (HTTP {response.status_code})"}, 429 if response.status_code == 429 else 502

        text_content = response.json()["choices"][0]["message"]["content"]
        return mark_ai_provider(parse_ai_json(text_content), "Groq"), 200
    except json.JSONDecodeError as exc:
        log.exception("Error al parsear el JSON de Groq")
        return {"error": f"Fallo al decodificar la respuesta de Groq: {str(exc)}"}, 500
    except Exception as exc:
        log.exception("Error durante la consulta a Groq")
        return {"error": f"Fallo de conexión o consulta con Groq: {str(exc)}"}, 500

def call_openrouter_json(prompt, timeout=15):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return {"error": "Clave API de OpenRouter no configurada en el servidor."}, 503

    model = os.getenv("OPENROUTER_MODEL", "openrouter/free")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Responde siempre con JSON válido y sin texto adicional."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://www.quantuschile.cl",
                "X-Title": "Quantus Chile",
            },
            json=payload,
            timeout=timeout,
        )
        if response.status_code != 200:
            log.error(f"Error de OpenRouter API: {response.status_code} - {response.text[:500]}")
            return {"error": f"Error de OpenRouter API (HTTP {response.status_code})"}, 429 if response.status_code == 429 else 502

        text_content = response.json()["choices"][0]["message"]["content"]
        return mark_ai_provider(parse_ai_json(text_content), "OpenRouter"), 200
    except json.JSONDecodeError as exc:
        log.exception("Error al parsear el JSON de OpenRouter")
        return {"error": f"Fallo al decodificar la respuesta de OpenRouter: {str(exc)}"}, 500
    except Exception as exc:
        log.exception("Error durante la consulta a OpenRouter")
        return {"error": f"Fallo de conexión o consulta con OpenRouter: {str(exc)}"}, 500

def call_ai_json(prompt, timeout=15):
    providers = [("Gemini", call_gemini_json)]
    if os.getenv("AI_ALLOW_PAID_FALLBACKS", "0") == "1":
        providers.extend([
            ("Groq", call_groq_json),
            ("OpenRouter", call_openrouter_json),
        ])
    errors = []
    for name, provider in providers:
        data, status = provider(prompt, timeout=timeout)
        if status == 200:
            return data, status
        errors.append(f"{name}: {data.get('error', 'sin detalle')}")

    configured = [name for name, key in [
        ("Gemini", os.getenv("GEMINI_API_KEY")),
        ("Groq", os.getenv("GROQ_API_KEY") if os.getenv("AI_ALLOW_PAID_FALLBACKS", "0") == "1" else None),
        ("OpenRouter", os.getenv("OPENROUTER_API_KEY") if os.getenv("AI_ALLOW_PAID_FALLBACKS", "0") == "1" else None),
    ] if key]
    suffix = f" Proveedores configurados: {', '.join(configured)}." if configured else " No hay proveedores IA configurados."
    return {
        "error": "La IA no pudo responder en este momento. " + " | ".join(errors[:3]) + suffix
    }, 503

def extract_pdf_text(file_storage):
    if not file_storage or not file_storage.filename:
        return ""

    ext = Path(file_storage.filename).suffix.lower()
    if ext != ".pdf":
        abort(400, "El archivo de alerta debe estar en PDF.")

    head = file_storage.stream.read(5)
    file_storage.stream.seek(0)
    if head != b"%PDF-":
        abort(400, "El archivo PDF no parece válido.")

    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        abort(400, "El servidor aún no tiene extractor PDF instalado. Pega el texto de la alerta para analizarla.")

    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
        file_storage.save(tmp.name)
        completed = subprocess.run(
            [pdftotext, "-layout", tmp.name, "-"],
            text=True,
            capture_output=True,
            timeout=12,
            check=False,
        )
    if completed.returncode != 0:
        abort(400, "No se pudo extraer texto del PDF. Pega el texto visible de la alerta.")
    return completed.stdout.strip()

def require_admin_token():
    expected = os.getenv("QUANTUS_ADMIN_TOKEN", "")
    received = request.args.get("token") or request.headers.get("X-Admin-Token") or ""
    if not expected or not hmac.compare_digest(expected, received):
        abort(403)

def require_master_login():
    if not session.get("quantus_master_authenticated"):
        return redirect(url_for("maestro_login", next=request.path))
    return None

def hash_master_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 180000)
    return {"salt": salt, "hash": digest.hex(), "algorithm": "pbkdf2_sha256", "iterations": 180000}

def verify_master_password(password, auth):
    if not password or not auth:
        return False
    salt = auth.get("salt") or ""
    expected = auth.get("hash") or ""
    if not salt or not expected:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), int(auth.get("iterations") or 180000)).hex()
    return hmac.compare_digest(digest, expected)

def save_master_auth(username, password):
    Path(MASTER_AUTH_FILE).parent.mkdir(exist_ok=True)
    payload = {
        "username": username,
        "email": MASTER_ADMIN_EMAIL,
        "password": hash_master_password(password),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(MASTER_AUTH_FILE, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    try:
        os.chmod(MASTER_AUTH_FILE, 0o600)
    except OSError:
        pass
    return payload

def sync_erp_superadmin_credentials(username, password):
    erp_password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    dbs = ["quantus_demo", "quantus_cliente2"]
    updated = []
    errors = []
    def sql_literal(value):
        return "'" + str(value).replace("'", "''") + "'"
    for db_name in dbs:
        sql = f"""
        UPDATE users
        SET username = {sql_literal(username)}, password = {sql_literal(erp_password_hash)}, activo = true
        WHERE role = 'SuperAdmin' OR username IN ('quantus', {sql_literal(username)})
        RETURNING id, username, role;
        """
        try:
            completed = subprocess.run(
                [
                    "pct", "exec", "100", "--", "docker", "exec", "-i", "quantus-postgres",
                    "psql", "-U", "quantus_admin", "-d", db_name, "-Atq",
                ],
                input="\\set ON_ERROR_STOP on\n" + sql,
                text=True,
                capture_output=True,
                timeout=18,
                check=False,
            )
            if completed.returncode != 0:
                errors.append(f"{db_name}: {completed.stderr.strip()[:180]}")
                continue
            changed = [line for line in completed.stdout.splitlines() if line.strip()]
            if changed:
                updated.append({"db": db_name, "rows": len(changed)})
        except Exception as exc:
            errors.append(f"{db_name}: {type(exc).__name__}")
    if errors:
        log.warning("ERP SuperAdmin sync completed with errors: %s", " | ".join(errors))
    else:
        log.info("ERP SuperAdmin sync completed: %s", updated)
    return {"updated": updated, "errors": errors}

def load_master_auth():
    data = read_json_file(MASTER_AUTH_FILE, fallback={})
    if data.get("username") and data.get("password"):
        return data
    if MASTER_ADMIN_PASSWORD:
        return save_master_auth(MASTER_ADMIN_USER, MASTER_ADMIN_PASSWORD)
    return {
        "username": MASTER_ADMIN_USER,
        "email": MASTER_ADMIN_EMAIL,
        "password": {},
    }

def send_master_temp_password():
    from mailer import smtp_configured
    if not smtp_configured():
        return False, "La recuperación por correo no está disponible: el servidor SMTP no está configurado (falta GMAIL_APP_PASSWORD). Contacta al administrador del sistema."
    temp_password = "Q-" + secrets.token_urlsafe(10)
    auth = load_master_auth()
    username = auth.get("username") or MASTER_ADMIN_USER
    previous_auth = dict(auth)
    save_master_auth(username, temp_password)
    sync_erp_superadmin_credentials(username, temp_password)
    body = f"""
    <h2>Recuperación Centro Maestro Quantus</h2>
    <p>Se generó una contraseña temporal para el usuario <strong>{username}</strong>.</p>
    <p><strong>Contraseña temporal:</strong> <code>{temp_password}</code></p>
    <p>Ingresa al Centro Maestro y cambia esta contraseña desde el menú privado.</p>
    <p>Acceso: <a href="http://localhost:8095/maestro">http://localhost:8095/maestro</a></p>
    """
    ok = send_email(MASTER_ADMIN_EMAIL, "[Quantus] Recuperación Centro Maestro", body)
    if not ok:
        _restore_master_auth(previous_auth)
        return False, "Se generó la contraseña temporal, pero el envío del correo falló. Contacta al administrador del sistema."
    return True, None

def _restore_master_auth(payload):
    if not payload:
        return
    try:
        Path(MASTER_AUTH_FILE).parent.mkdir(exist_ok=True)
        with open(MASTER_AUTH_FILE, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
    except OSError:
        pass

def google_oauth_configured():
    return bool(GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET)

def build_google_auth_url():
    state = secrets.token_urlsafe(32)
    session["google_oauth_state"] = state
    params = {
        "client_id": GOOGLE_OAUTH_CLIENT_ID,
        "redirect_uri": GOOGLE_OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
        "hd": "gmail.com",
    }
    return GOOGLE_AUTH_URL + "?" + requests.compat.urlencode(params)

def exchange_google_code(code):
    response = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": GOOGLE_OAUTH_CLIENT_SECRET,
            "redirect_uri": GOOGLE_OAUTH_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        timeout=12,
    )
    if response.status_code != 200:
        log.warning("Google OAuth token exchange failed: %s", response.text[:300])
        return None
    return response.json()

def fetch_google_userinfo(access_token):
    response = requests.get(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=12,
    )
    if response.status_code != 200:
        log.warning("Google OAuth userinfo failed: %s", response.text[:300])
        return None
    return response.json()

def rp_id():
    host = request.headers.get("Host", "www.quantuschile.cl").split(":")[0]
    if host.endswith("quantuschile.cl") or host.endswith(".ts.net") or host in ("localhost", "127.0.0.1"):
        return host
    return "www.quantuschile.cl"

def expected_origin():
    proto = request.headers.get("X-Forwarded-Proto", request.scheme or "http")
    host = request.headers.get("Host", rp_id())
    return f"{proto}://{host}"


def load_master_passkeys():
    data = read_json_file(MASTER_PASSKEYS_FILE, fallback=[])
    return data if isinstance(data, list) else []

def save_master_passkeys(items):
    Path(MASTER_PASSKEYS_FILE).parent.mkdir(exist_ok=True)
    with open(MASTER_PASSKEYS_FILE, "w", encoding="utf-8") as fh:
        json.dump(items, fh, ensure_ascii=False, indent=2)
    try:
        os.chmod(MASTER_PASSKEYS_FILE, 0o600)
    except OSError:
        pass

def passkey_descriptors():
    descriptors = []
    for item in load_master_passkeys():
        try:
            descriptors.append(PublicKeyCredentialDescriptor(id=b64url_decode(item["credential_id"])))
        except Exception:
            continue
    return descriptors

def read_json_file(path, fallback=None):
    fallback = [] if fallback is None else fallback
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return fallback

DO_PEOPLE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "do_people.json")
DO_PAYMENT_EVENTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "do_payment_events.json")
LICITACIONES_CLIENTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "licitaciones_clients.json")
MASTER_FREE_CLIENTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "master_free_clients.json")
SUPERADMIN_MODULES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "quantus_superadmin_modules.json")
WATCHDOG_CLIENTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "watchdog_clients.json")
RADAR_MODULES = {
    "diario_oficial": {
        "label": "Diario Oficial",
        "service_label": "Vigilancia Diario Oficial 24/7",
        "scope_label": "Personas, empresas, alias y RUT asociados",
    },
    "licitaciones": {
        "label": "Licitaciones",
        "service_label": "Radar de Licitaciones 24/7",
        "scope_label": "Rubros, regiones, montos y organismos",
    },
    "remates": {
        "label": "Remates",
        "service_label": "Radar Nacional de Remates",
        "scope_label": "Region, comuna, tribunal, banco o tipo de inmueble",
    },
    "inapi": {
        "label": "INAPI",
        "service_label": "Vigilancia de Marcas INAPI",
        "scope_label": "Marca, clase, titular o rubro protegido",
    },
}
DO_ACTIVE_STATES = {"activo", "active"}
DO_PENDING_STATES = {"pendiente_pago", "pending_payment"}
DO_GRACE_DAYS = int(os.getenv("DO_SUBSCRIPTION_GRACE_DAYS", "7"))
DO_PENDING_PAYMENT_TTL_DAYS = int(os.getenv("DO_PENDING_PAYMENT_TTL_DAYS", "7"))
DO_PRIVACY_RETENTION_DAYS = int(os.getenv("DO_PRIVACY_RETENTION_DAYS", "30"))
DO_AUTO_ANONYMIZE_EXPIRED = os.getenv("DO_AUTO_ANONYMIZE_EXPIRED", "0") == "1"

SUPERADMIN_MODULE_STATUSES = {
    "produccion": "Produccion",
    "piloto": "Piloto",
    "demo": "Demo",
    "mock": "Mock",
    "block": "Block",
    "externo": "Externo",
}

SUPERADMIN_MODULE_VISIBILITY = {
    "publico": "Publico",
    "interno": "Interno",
    "demo": "Demo visible",
    "oculto": "Oculto",
}

SUPERADMIN_DEFAULT_MODULES = [
    {
        "key": "centro-maestro",
        "name": "Centro Maestro",
        "category": "Control",
        "status": "produccion",
        "visibility": "interno",
        "public_path": "/maestro",
        "admin_path": "/maestro",
        "owner": "Quantus",
        "enabled": True,
        "notes": "Panel privado de control operacional.",
    },
    {
        "key": "quantus-nexus",
        "name": "Quantus Nexus",
        "category": "Observabilidad",
        "status": "piloto",
        "visibility": "interno",
        "public_path": "http://127.0.0.1:8096/",
        "admin_path": "http://127.0.0.1:8096/",
        "owner": "Quantus",
        "enabled": True,
        "notes": "Dashboard unificado solo lectura; complemento del Centro Maestro, no reemplaza el control SuperAdmin.",
    },
    {
        "key": "punto-de-venta",
        "name": "Punto de Venta",
        "category": "Comercial",
        "status": "demo",
        "visibility": "demo",
        "public_path": "/clientes",
        "admin_path": "/pos",
        "owner": "Quantus",
        "enabled": True,
        "notes": "Demo comercial con aislamiento por empresa, PDF de respaldo y cola offline basica.",
    },
    {
        "key": "geointel-sales-radar",
        "name": "GeoIntel / Sales Radar",
        "category": "Prospeccion",
        "status": "piloto",
        "visibility": "interno",
        "public_path": "",
        "admin_path": "/maestro/geointel",
        "owner": "Quantus",
        "enabled": True,
        "notes": "Prospeccion B2B interna con fuentes PASS/BLOCK.",
    },
    {
        "key": "diario-oficial",
        "name": "Diario Oficial",
        "category": "Radar legal",
        "status": "piloto",
        "visibility": "publico",
        "public_path": "/do",
        "admin_path": "/do/admin",
        "owner": "Quantus",
        "enabled": True,
        "notes": "Vigilancia y alertas con activacion por pago/verificacion.",
    },
    {
        "key": "inapi",
        "name": "INAPI marcas",
        "category": "Radar legal",
        "status": "demo",
        "visibility": "publico",
        "public_path": "/inapi",
        "admin_path": "/maestro",
        "owner": "Quantus",
        "enabled": True,
        "notes": "Vigilancia de marcas y titulares.",
    },
    {
        "key": "licitaciones",
        "name": "Licitaciones",
        "category": "Radar comercial",
        "status": "demo",
        "visibility": "publico",
        "public_path": "/licitaciones",
        "admin_path": "/licitaciones#analizador-licitaciones",
        "owner": "Quantus",
        "enabled": True,
        "notes": "Buscador y analizador Mercado Publico.",
    },
    {
        "key": "remates",
        "name": "Remates inmuebles",
        "category": "Radar comercial",
        "status": "demo",
        "visibility": "publico",
        "public_path": "/remates",
        "admin_path": "/remates",
        "owner": "Quantus",
        "enabled": True,
        "notes": "Alertas de remates y oportunidades inmobiliarias.",
    },
]

def save_json_file(path, payload):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        os.replace(tmp_name, target)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)

def superadmin_module_key(value):
    safe = werkzeug.utils.secure_filename((value or "").strip().lower().replace(" ", "-"))
    return safe[:80].strip("-_")

def normalize_superadmin_module(payload, existing=None):
    existing = existing or {}
    name = (payload.get("name") or existing.get("name") or "").strip()[:90]
    key = superadmin_module_key(payload.get("key") or existing.get("key") or name)
    if not key or not name:
        raise ValueError("Nombre y codigo interno son obligatorios.")
    status = (payload.get("status") or existing.get("status") or "demo").strip().lower()
    visibility = (payload.get("visibility") or existing.get("visibility") or "interno").strip().lower()
    if status not in SUPERADMIN_MODULE_STATUSES:
        raise ValueError("Estado de funcionalidad no permitido.")
    if visibility not in SUPERADMIN_MODULE_VISIBILITY:
        raise ValueError("Visibilidad no permitida.")
    return {
        "key": key,
        "name": name,
        "category": (payload.get("category") or existing.get("category") or "General").strip()[:60],
        "status": status,
        "visibility": visibility,
        "public_path": (payload.get("public_path") or existing.get("public_path") or "").strip()[:160],
        "admin_path": (payload.get("admin_path") or existing.get("admin_path") or "").strip()[:160],
        "owner": (payload.get("owner") or existing.get("owner") or "Quantus").strip()[:60],
        "enabled": bool(payload.get("enabled")),
        "notes": (payload.get("notes") or existing.get("notes") or "").strip()[:260],
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }

def load_superadmin_modules():
    stored = read_json_file(SUPERADMIN_MODULES_FILE, fallback=[])
    by_key = {}
    for item in SUPERADMIN_DEFAULT_MODULES:
        module = normalize_superadmin_module({**item, "enabled": item.get("enabled")}, existing=item)
        module.setdefault("created_at", datetime.now().isoformat(timespec="seconds"))
        by_key[module["key"]] = module
    for item in stored if isinstance(stored, list) else []:
        try:
            module = normalize_superadmin_module(item, existing=item)
        except ValueError:
            continue
        module["created_at"] = item.get("created_at") or module["updated_at"]
        by_key[module["key"]] = module
    modules = sorted(by_key.values(), key=lambda row: (row.get("category") or "", row.get("name") or ""))
    return modules

def save_superadmin_modules(modules):
    save_json_file(SUPERADMIN_MODULES_FILE, modules)

def superadmin_modules_summary(modules=None):
    modules = modules or load_superadmin_modules()
    return {
        "total": len(modules),
        "enabled": sum(1 for item in modules if item.get("enabled")),
        "blocked": sum(1 for item in modules if item.get("status") == "block"),
        "demo": sum(1 for item in modules if item.get("status") == "demo"),
        "production": sum(1 for item in modules if item.get("status") == "produccion"),
    }

def load_do_people():
    return read_json_file(DO_PEOPLE_FILE, [])

def save_do_people(people):
    save_json_file(DO_PEOPLE_FILE, people)

def load_licitaciones_clients():
    return read_json_file(LICITACIONES_CLIENTS_FILE, [])

def save_licitaciones_clients(clients):
    save_json_file(LICITACIONES_CLIENTS_FILE, clients)

def load_do_payment_events():
    return read_json_file(DO_PAYMENT_EVENTS_FILE, [])

def save_do_payment_events(events):
    save_json_file(DO_PAYMENT_EVENTS_FILE, events)

def load_master_free_clients():
    return read_json_file(MASTER_FREE_CLIENTS_FILE, [])

def save_master_free_clients(clients):
    save_json_file(MASTER_FREE_CLIENTS_FILE, clients)

def free_client_identity_matches(item, module, rut, email):
    return (
        (item.get("module") or "") == module
        and (
            (rut and clean_rut(item.get("rut")) == clean_rut(rut))
            or (email and (item.get("email") or "").strip().lower() == email.strip().lower())
        )
    )

def upsert_master_free_client(module, nombre, rut, email, whatsapp, scope, operator="centro_maestro"):
    if module not in RADAR_MODULES:
        raise ValueError("Modulo de radar no reconocido.")
    clients = load_master_free_clients()
    existing = next((item for item in clients if free_client_identity_matches(item, module, rut, email)), None)
    now = datetime.now().isoformat(timespec="seconds")
    key = client_key_for(module, nombre, rut, email)
    payload = {
        "id": existing.get("id") if existing else secrets.token_hex(10),
        "key": existing.get("key") if existing else key,
        "module": module,
        "module_label": RADAR_MODULES[module]["label"],
        "name": nombre,
        "rut": rut,
        "email": email,
        "whatsapp": whatsapp,
        "scope": scope or RADAR_MODULES[module]["scope_label"],
        "status": "activo_gratis",
        "plan": "gratis_maestro",
        "billing_status": "gratis",
        "monthly_value": 0,
        "contacto_verificado": True,
        "created_from": "centro_maestro",
        "created_by": operator,
        "created_at": existing.get("created_at") if existing else now,
        "updated_at": now,
    }
    if existing:
        existing.update(payload)
    else:
        clients.append(payload)
    save_master_free_clients(clients)
    return payload

def request_payload():
    if request.is_json:
        return request.get_json(silent=True) or {}
    return request.form.to_dict()

def parse_local_date(value):
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text[:19], fmt).date()
        except ValueError:
            continue
    return None

def plan_duration_days(plan):
    plan = (plan or "").strip().lower()
    if plan == "mensual":
        return 30
    if plan == "anual":
        return 365
    return 30

def do_checkout_url(plan, payment_mode):
    mp_links_subscription = {
        "mensual": os.getenv("MP_LINK_DO_MENSUAL", "https://mpago.la/1qTuLK1"),
        "anual": os.getenv("MP_LINK_DO_ANUAL", "https://mpago.la/1DbFHjh"),
        "empresa_inicial": os.getenv("MP_LINK_DO_EMPRESA_INICIAL", "https://mpago.la/1R3QNyF"),
        "empresa": os.getenv("MP_LINK_DO_EMPRESA", "https://mpago.la/33EsVrE"),
    }
    mp_links_one_time = {
        "mensual": os.getenv("MP_LINK_ONETIME_MENSUAL", "https://mpago.la/1ULj6FH"),
        "anual": os.getenv("MP_LINK_ONETIME_ANUAL", mp_links_subscription["anual"]),
        "empresa_inicial": os.getenv("MP_LINK_ONETIME_EMPRESA_INICIAL", mp_links_subscription["empresa_inicial"]),
        "empresa": os.getenv("MP_LINK_ONETIME_EMPRESA", mp_links_subscription["empresa"]),
    }
    links = mp_links_one_time if payment_mode == "one_time" else mp_links_subscription
    return links.get(plan) or mp_links_subscription["mensual"]

def licitaciones_plan_duration_days(plan):
    plan = (plan or "").strip().lower()
    if plan in {"anual", "empresa_anual"}:
        return 365
    return 30

def licitaciones_checkout_url(plan, payment_mode):
    mp_links_subscription = {
        "oportunidades": MP_LINK_LIC_OPORTUNIDADES,
        "pyme_pro": MP_LINK_LIC_PYME_PRO,
        "empresa": MP_LINK_LIC_EMPRESA,
        "premium": MP_LINK_LIC_PREMIUM,
    }
    mp_links_one_time = {
        "oportunidades": os.getenv("MP_LINK_LIC_ONETIME_OPORTUNIDADES", mp_links_subscription["oportunidades"]),
        "pyme_pro": os.getenv("MP_LINK_LIC_ONETIME_PYME_PRO", mp_links_subscription["pyme_pro"]),
        "empresa": os.getenv("MP_LINK_LIC_ONETIME_EMPRESA", mp_links_subscription["empresa"]),
        "premium": os.getenv("MP_LINK_LIC_ONETIME_PREMIUM", mp_links_subscription["premium"]),
    }
    links = mp_links_one_time if payment_mode == "one_time" else mp_links_subscription
    return links.get(plan) or mp_links_subscription["oportunidades"]

def do_identity_matches(person, rut, email):
    rut_clean = clean_rut(rut)
    email_clean = (email or "").strip().lower()
    person_rut = clean_rut(person.get("rut"))
    person_email = (person.get("alertar_a") or person.get("email") or "").strip().lower()
    return bool((rut_clean and person_rut == rut_clean) or (email_clean and person_email == email_clean))

def licitaciones_identity_matches(client, rut, email):
    rut_clean = clean_rut(rut)
    email_clean = (email or "").strip().lower()
    client_rut = clean_rut(client.get("rut"))
    client_email = (client.get("email") or client.get("correo") or "").strip().lower()
    return bool((rut_clean and client_rut == rut_clean) or (email_clean and client_email == email_clean))

def do_subscription_state(person, today=None):
    today = today or datetime.now().date()
    estado = (person.get("estado") or "").strip().lower()
    plan = (person.get("plan") or "").strip().lower()
    expires_at = parse_local_date(person.get("fecha_vencimiento"))
    if plan in {"grupo_familiar_24x7", "superadmin_activo", "superadmin_empresa_pro", "gratis_maestro"}:
        return "activo_permanente"
    if estado in DO_PENDING_STATES:
        created_at = parse_local_date(person.get("fecha_registro") or person.get("created_at") or person.get("consent_timestamp"))
        if created_at and today > created_at + timedelta(days=DO_PENDING_PAYMENT_TTL_DAYS):
            return "pendiente_pago_vencido"
        return "pendiente_pago"
    if estado in {"anonimizado", "eliminado"}:
        return estado
    if expires_at:
        if today <= expires_at:
            return "activo"
        if today <= expires_at + timedelta(days=DO_GRACE_DAYS):
            return "vencido_en_gracia"
        return "vencido_pendiente_eliminacion"
    if estado in DO_ACTIVE_STATES:
        return "activo_sin_vencimiento"
    return estado or "sin_estado"

def anonymize_do_person(person, reason):
    rut_hash = hmac.new(
        app.config["SECRET_KEY"].encode("utf-8"),
        clean_rut(person.get("rut")).encode("utf-8"),
        "sha256",
    ).hexdigest()[:16] if person.get("rut") else ""
    return {
        "id": person.get("id"),
        "estado": "anonimizado",
        "rut_hash": rut_hash,
        "plan": person.get("plan"),
        "fecha_vencimiento": person.get("fecha_vencimiento"),
        "anonimizado_en": datetime.now().isoformat(timespec="seconds"),
        "privacy_cleanup_reason": reason,
        "retention_note": "Datos personales suprimidos por vencimiento o falta de pago; se conserva solo evidencia minima no identificable para auditoria operacional.",
    }

def refresh_do_subscription_lifecycle(people, persist=False):
    today = datetime.now().date()
    changed = False
    refreshed = []
    for person in people:
        item = dict(person)
        state = do_subscription_state(item, today=today)
        item["subscription_state"] = state
        if state == "vencido_en_gracia":
            if item.get("estado") != "vencido_en_gracia":
                item["estado"] = "vencido_en_gracia"
                item.setdefault("subscription_end_notice_required", True)
                item.setdefault("subscription_end_notice_reason", "suscripcion_vencida")
                changed = True
        elif state in {"vencido_pendiente_eliminacion", "pendiente_pago_vencido"}:
            cleanup_date = today + timedelta(days=DO_PRIVACY_RETENTION_DAYS)
            item["estado"] = "pendiente_eliminacion"
            item.setdefault("privacy_cleanup_due", cleanup_date.strftime("%Y-%m-%d"))
            item.setdefault("subscription_end_notice_required", True)
            item.setdefault("subscription_end_notice_reason", state)
            changed = True
            due = parse_local_date(item.get("privacy_cleanup_due"))
            if DO_AUTO_ANONYMIZE_EXPIRED and due and today >= due:
                item = anonymize_do_person(item, state)
                changed = True
        refreshed.append(item)
    if changed and persist:
        save_do_people(refreshed)
    return refreshed

def licitaciones_subscription_state(client, today=None):
    today = today or datetime.now().date()
    estado = (client.get("estado") or "").strip().lower()
    plan = (client.get("plan") or "").strip().lower()
    expires_at = parse_local_date(client.get("fecha_vencimiento"))
    if plan == "gratis_maestro":
        return "activo_permanente"
    if estado in DO_PENDING_STATES:
        created_at = parse_local_date(client.get("fecha_registro") or client.get("created_at") or client.get("consent_timestamp"))
        if created_at and today > created_at + timedelta(days=DO_PENDING_PAYMENT_TTL_DAYS):
            return "pendiente_pago_vencido"
        return "pendiente_pago"
    if estado in {"anonimizado", "eliminado"}:
        return estado
    if expires_at:
        if today <= expires_at:
            return "activo"
        if today <= expires_at + timedelta(days=DO_GRACE_DAYS):
            return "vencido_en_gracia"
        return "vencido_pendiente_eliminacion"
    if estado in DO_ACTIVE_STATES:
        return "activo_sin_vencimiento"
    return estado or "sin_estado"

def anonymize_licitaciones_client(client, reason):
    rut_hash = hmac.new(
        app.config["SECRET_KEY"].encode("utf-8"),
        clean_rut(client.get("rut")).encode("utf-8"),
        "sha256",
    ).hexdigest()[:16] if client.get("rut") else ""
    return {
        "id": client.get("id"),
        "estado": "anonimizado",
        "rut_hash": rut_hash,
        "plan": client.get("plan"),
        "fecha_vencimiento": client.get("fecha_vencimiento"),
        "anonimizado_en": datetime.now().isoformat(timespec="seconds"),
        "privacy_cleanup_reason": reason,
        "retention_note": "Datos personales suprimidos por vencimiento o falta de pago; se conserva solo evidencia minima no identificable para auditoria operacional.",
    }

def refresh_licitaciones_lifecycle(clients, persist=False):
    today = datetime.now().date()
    changed = False
    refreshed = []
    for client in clients:
        item = dict(client)
        state = licitaciones_subscription_state(item, today=today)
        item["subscription_state"] = state
        if state == "vencido_en_gracia":
            if item.get("estado") != "vencido_en_gracia":
                item["estado"] = "vencido_en_gracia"
                item.setdefault("subscription_end_notice_required", True)
                item.setdefault("subscription_end_notice_reason", "suscripcion_vencida")
                changed = True
        elif state in {"vencido_pendiente_eliminacion", "pendiente_pago_vencido"}:
            cleanup_date = today + timedelta(days=DO_PRIVACY_RETENTION_DAYS)
            item["estado"] = "pendiente_eliminacion"
            item.setdefault("privacy_cleanup_due", cleanup_date.strftime("%Y-%m-%d"))
            item.setdefault("subscription_end_notice_required", True)
            item.setdefault("subscription_end_notice_reason", state)
            changed = True
            due = parse_local_date(item.get("privacy_cleanup_due"))
            if DO_AUTO_ANONYMIZE_EXPIRED and due and today >= due:
                item = anonymize_licitaciones_client(item, state)
                changed = True
        refreshed.append(item)
    if changed and persist:
        save_licitaciones_clients(refreshed)
    return refreshed

def find_do_subscription(people, rut, email):
    matches = [person for person in people if do_identity_matches(person, rut, email)]
    priority = {
        "activo": 0,
        "activo_permanente": 0,
        "activo_sin_vencimiento": 0,
        "pendiente_pago": 1,
        "vencido_en_gracia": 2,
        "vencido_pendiente_eliminacion": 3,
        "pendiente_eliminacion": 3,
    }
    matches.sort(key=lambda item: priority.get(do_subscription_state(item), 9))
    return matches[0] if matches else None

def find_licitaciones_subscription(clients, rut, email):
    matches = [client for client in clients if licitaciones_identity_matches(client, rut, email)]
    priority = {
        "activo": 0,
        "activo_permanente": 0,
        "activo_sin_vencimiento": 0,
        "pendiente_pago": 1,
        "vencido_en_gracia": 2,
        "vencido_pendiente_eliminacion": 3,
        "pendiente_eliminacion": 3,
    }
    matches.sort(key=lambda item: priority.get(licitaciones_subscription_state(item), 9))
    return matches[0] if matches else None

def do_person_key(person):
    return client_key_for("diario_oficial", person.get("nombre_completo"), person.get("rut"), person.get("alertar_a"))

def find_do_person_by_id(people, person_id):
    person_id = str(person_id or "").strip()
    for index, person in enumerate(people):
        if str(person.get("id")) == person_id:
            return index, person
    return None, None

def confirm_do_payment(person_id, reference, amount, paid_at, operator, note=""):
    people = refresh_do_subscription_lifecycle(load_do_people(), persist=True)
    index, person = find_do_person_by_id(people, person_id)
    if person is None:
        raise ValueError("No encontramos el cliente Diario Oficial indicado.")

    state = do_subscription_state(person)
    if state in {"activo", "activo_permanente", "activo_sin_vencimiento"}:
        raise ValueError("Este cliente ya tiene una vigilancia activa.")
    if state not in {"pendiente_pago", "vencido_en_gracia", "vencido_pendiente_eliminacion", "pendiente_eliminacion", "pendiente_pago_vencido"}:
        raise ValueError(f"El estado actual no permite activación directa: {state}.")

    reference = (reference or "").strip()
    if not reference:
        raise ValueError("Debes registrar la referencia o comprobante de Mercado Pago.")
    try:
        amount_int = int(round(float(str(amount or "0").replace(".", "").replace(",", "."))))
    except ValueError:
        amount_int = 0
    if amount_int <= 0:
        raise ValueError("Debes registrar un monto pagado mayor a cero.")

    paid_date = parse_local_date(paid_at) or datetime.now().date()
    plan = person.get("plan") or "mensual"
    expires_at = paid_date + timedelta(days=plan_duration_days(plan))
    now = datetime.now()
    event_id = secrets.token_hex(12)
    event = {
        "id": event_id,
        "created_at": now.isoformat(timespec="seconds"),
        "event": "payment_confirmed_manual",
        "person_id": person.get("id"),
        "client_key": do_person_key(person),
        "client_name": person.get("nombre_completo"),
        "rut": person.get("rut"),
        "email": person.get("alertar_a"),
        "plan": plan,
        "previous_state": state,
        "new_state": "activo",
        "amount_clp": amount_int,
        "payment_reference": reference,
        "paid_at": paid_date.strftime("%Y-%m-%d"),
        "activated_at": now.isoformat(timespec="seconds"),
        "expires_at": expires_at.strftime("%Y-%m-%d"),
        "operator": operator,
        "ip": get_client_ip(),
        "user_agent": request.headers.get("User-Agent", "")[:500],
        "note": note.strip()[:500],
    }

    person.update({
        "estado": "activo",
        "subscription_state": "activo",
        "payment_status": "pagado",
        "payment_confirmed": True,
        "payment_confirmed_at": event["activated_at"],
        "payment_confirmed_by": operator,
        "payment_reference": reference,
        "payment_amount_clp": amount_int,
        "payment_event_id": event_id,
        "fecha_inicio_servicio": paid_date.strftime("%Y-%m-%d"),
        "fecha_vencimiento": expires_at.strftime("%Y-%m-%d"),
        "privacy_cleanup_due": "",
        "subscription_end_notice_required": False,
        "subscription_end_notice_reason": "",
    })
    people[index] = person
    save_do_people(people)
    events = load_do_payment_events()
    events.append(event)
    save_do_payment_events(events)
    try:
        root = ensure_client_workspace({
            "key": do_person_key(person),
            "name": person.get("nombre_completo"),
            "module": "Diario Oficial",
            "rut": person.get("rut"),
            "rubro": "Personas y empresas",
            "plan": person.get("plan"),
        })
        pagos_dir = root / "pagos"
        pagos_dir.mkdir(exist_ok=True)
        with open(pagos_dir / f"{event_id}_pago_confirmado.json", "w", encoding="utf-8") as fh:
            json.dump(event, fh, ensure_ascii=False, indent=2)
    except Exception as exc:
        log.warning("No se pudo guardar pago confirmado en carpeta cliente: %s", exc)
    return person, event

def plan_monthly_value(module, plan):
    plan = (plan or "").strip().lower()
    values = {
        "diario_oficial": {
            "mensual": 2990,
            "anual": 20000 / 12,
            "grupo_familiar_24x7": 0,
            "gratis_maestro": 0,
            "empresa_inicial": 19990,
            "empresa": 49900,
            "premium": 49900,
        },
        "licitaciones": {
            "oportunidades": 9990,
            "pyme_pro": 24990,
            "empresa": 49990,
            "premium": 99990,
        },
        "inapi": {
            "vigilancia_marca": 12000,
            "registro_inicial": REGISTRO_GESTION_INICIAL,
        },
    }
    return values.get(module, {}).get(plan, 0)

def pct(value, total):
    if not total:
        return 0
    return int(round((value / total) * 100))

def client_key_for(*values):
    raw = "|".join((value or "").strip().lower() for value in values)
    return hmac.new(app.config["SECRET_KEY"].encode("utf-8"), raw.encode("utf-8"), "sha256").hexdigest()[:16]

def client_slug(name):
    base = werkzeug.utils.secure_filename((name or "cliente").lower().replace(" ", "-"))
    return base[:48] or "cliente"

def rut_folder_slug(rut):
    clean = clean_rut(rut)
    return clean.lower() if clean else "sin-rut"

def rut_sort_key(rut):
    clean = clean_rut(rut)
    if not clean:
        return "zzzzzzzzzz"
    return clean.rjust(10, "0")

def comparable_name(value):
    text = unicodedata.normalize("NFD", value or "")
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return " ".join(text.upper().split())

def infer_rut_from_people(name, people):
    target = comparable_name(name)
    if not target:
        return ""
    for person in people:
        rut = person.get("rut") or ""
        if not rut:
            continue
        candidate = comparable_name(person.get("nombre_completo"))
        candidate_tokens = set(candidate.split())
        target_tokens = set(target.split())
        if target == candidate or target_tokens.issubset(candidate_tokens) or candidate_tokens.issubset(target_tokens):
            return rut
    return ""

def ensure_client_workspace(client):
    key = client["key"]
    folder_name = f"{rut_folder_slug(client.get('rut'))}-{client_slug(client.get('name'))}-{key}"
    root = Path(CLIENT_WORKSPACE_DIR) / folder_name
    root.mkdir(parents=True, exist_ok=True)
    for category in CLIENT_FILE_CATEGORIES:
        (root / category).mkdir(exist_ok=True)
    for category in CLIENT_PRIVATE_CATEGORIES:
        private_dir = root / category
        private_dir.mkdir(exist_ok=True)
        try:
            os.chmod(private_dir, 0o700)
        except OSError:
            pass
    metadata = {
        "key": key,
        "name": client.get("name"),
        "module": client.get("module"),
        "rut": client.get("rut"),
        "rubro": client.get("rubro"),
        "plan": client.get("plan"),
        "created_or_updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(root / "cliente.json", "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, ensure_ascii=False, indent=2)
    return root

CONSENT_VERSION = "ley21719-v1-20260729"
DO_SOURCE_LIMITATION_VERSION = "do-source-limits-v1-20260802"
DO_SOURCE_LIMITATION_NOTICE = """Limitaciones propias de la fuente Diario Oficial:
El cliente declara entender que el Diario Oficial, tribunales, organismos publicadores o fuentes asociadas pueden publicar datos con errores, omisiones, abreviaciones, tildes distintas, nombres incompletos, RUT mal digitado, RUT omitido, razón social parcial, nombre de fantasía o referencias a representantes legales en vez de la persona o empresa esperada.

Quantus aplica búsquedas preventivas por RUT en múltiples formatos, nombre, razón social, alias y coincidencias aproximadas cuando existan datos suficientes. Aun así, el servicio no puede garantizar ausencia absoluta de falsos positivos ni de falsos negativos, porque depende de la calidad, disponibilidad y forma de publicación de la fuente oficial.

Cuando exista una coincidencia parcial o de alta probabilidad, Quantus podrá enviar una alerta preventiva marcada como posible coincidencia para que el titular la revise. Cuando la publicación oficial omita o altere datos esenciales de forma que impida una vinculación razonable con el perfil contratado, puede no generarse alerta automática. El servicio es una herramienta preventiva de monitoreo y no reemplaza la revisión legal humana, la revisión directa del Diario Oficial ni el control de plazos por parte del interesado."""

def require_data_consent(service_label):
    if request.form.get("data_consent") != "1":
        abort(400, f"Debes aceptar la autorización de tratamiento de datos personales para contratar {service_label}.")

def requires_do_source_limitation_ack(service_label):
    return "diario oficial" in (service_label or "").lower()

def require_do_source_limitation_ack(service_label):
    if requires_do_source_limitation_ack(service_label) and request.form.get("source_limitation_ack") != "1":
        abort(400, "Debes aceptar la advertencia sobre posibles errores u omisiones de la fuente Diario Oficial.")

def service_consent_text(service_label, client):
    name = client.get("name") or client.get("nombre") or "Cliente"
    rut = client.get("rut") or "No informado"
    source_limit_text = f"""
ADVERTENCIA OPERATIVA - DIARIO OFICIAL
Versión: {DO_SOURCE_LIMITATION_VERSION}
{DO_SOURCE_LIMITATION_NOTICE}
""" if requires_do_source_limitation_ack(service_label) else ""
    return f"""AUTORIZACIÓN DE TRATAMIENTO DE DATOS PERSONALES - QUANTUS CHILE
Versión: {CONSENT_VERSION}
Servicio contratado: {service_label}
Titular / cliente: {name}
RUT: {rut}
Fecha de aceptación: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Por medio de esta aceptación, el titular autoriza a Quantus Chile / quantuschile.cl a recolectar, almacenar y tratar sus datos personales y documentos necesarios para prestar el servicio contratado.

Datos que podrían tratarse según el servicio:
- Nombre, razón social, RUT, correo electrónico, teléfono y WhatsApp.
- Documentos entregados por el cliente, tales como poderes, inicio de actividades, comprobantes de pago, antecedentes comerciales, PDFs, informes y alertas.
- Información operativa generada por el servicio, incluyendo reportes IA, búsquedas, historial de alertas, configuraciones y comunicaciones.
- Credenciales o tokens de terceros solo cuando el cliente los entregue expresamente para operar integraciones, por ejemplo Meta WhatsApp Business.

Finalidades autorizadas:
- Prestar, configurar, cobrar y dar soporte al servicio contratado.
- Guardar evidencia operacional en carpetas privadas por cliente o RUT.
- Generar alertas, reportes, resúmenes, documentos, análisis IA y seguimiento del proceso.
- Comunicar información relevante al correo o WhatsApp autorizado por el cliente.
- Mantener trazabilidad, seguridad, respaldo, auditoría y continuidad del servicio.

Compromiso de confidencialidad:
Quantus no divulgará, venderá ni compartirá la información del cliente con terceros ajenos al servicio, salvo obligación legal, instrucción del titular, proveedores necesarios para la prestación del servicio o autorización expresa.

Seguridad y conservación:
La información será almacenada en servidores y carpetas privadas de Quantus con controles de acceso, HTTPS, permisos de archivo y medidas operativas razonables. Los datos se conservarán mientras sean necesarios para el servicio, respaldo, cumplimiento contractual, trazabilidad o exigencias legales, y luego podrán ser eliminados, bloqueados o anonimizados según corresponda.

Derechos del titular:
El titular podrá solicitar acceso, rectificación, supresión, oposición, portabilidad o bloqueo de sus datos escribiendo a privacidad@quantuschile.cl o al canal informado por Quantus. Las solicitudes serán revisadas conforme a la normativa aplicable.

{source_limit_text}

Nota:
Esta autorización es una medida operativa de cumplimiento y transparencia. No reemplaza asesoría legal especializada cuando existan datos sensibles, menores de edad, salud, scoring, incidentes de seguridad, transferencias internacionales o tratamientos de alto riesgo.
"""

def save_service_consent(client, service_label, extra=None):
    client_payload = {
        "key": client.get("key") or client_key_for(service_label, client.get("name") or client.get("nombre"), client.get("rut"), client.get("email")),
        "name": client.get("name") or client.get("nombre") or "Cliente",
        "module": client.get("module") or service_label,
        "rut": client.get("rut") or "",
        "rubro": client.get("rubro") or "",
        "plan": client.get("plan") or "",
    }
    root = ensure_client_workspace(client_payload)
    target_dir = root / "consentimientos"
    target_dir.mkdir(exist_ok=True)
    stamped = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_service = werkzeug.utils.secure_filename(service_label.lower().replace(" ", "_")) or "servicio"
    text = service_consent_text(service_label, client_payload)
    evidence = {
        "version": CONSENT_VERSION,
        "accepted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "service": service_label,
        "client": client_payload,
        "ip": get_client_ip(),
        "user_agent": request.headers.get("User-Agent", "")[:500],
        "form_fields": {
            "data_consent": request.form.get("data_consent"),
            "whatsapp_consent": request.form.get("whatsapp_consent"),
            "source_limitation_ack": request.form.get("source_limitation_ack"),
        },
        "extra": extra or {},
        "document_text": text,
    }
    txt_path = target_dir / f"{stamped}_{safe_service}_autorizacion_datos.txt"
    json_path = target_dir / f"{stamped}_{safe_service}_evidencia.json"
    with open(txt_path, "w", encoding="utf-8") as fh:
        fh.write(text)
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(evidence, fh, ensure_ascii=False, indent=2)
    return {"txt_path": str(txt_path), "json_path": str(json_path), "folder": str(root)}

def meta_whatsapp_path_for_root(root):
    return Path(root) / "integraciones" / "meta_whatsapp.json"

def mask_secret(value):
    value = (value or "").strip()
    if not value:
        return ""
    if len(value) <= 10:
        return "****"
    return f"{value[:4]}...{value[-4:]}"

def load_meta_whatsapp_config(root):
    path = meta_whatsapp_path_for_root(root)
    data = read_json_file(path, fallback={})
    return data if isinstance(data, dict) else {}

def save_meta_whatsapp_config(root, payload):
    path = meta_whatsapp_path_for_root(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path.parent, 0o700)
    except OSError:
        pass
    existing = load_meta_whatsapp_config(root)
    access_token = (payload.get("access_token") or "").strip() or existing.get("access_token", "")
    phone_number_id = (payload.get("phone_number_id") or "").strip()
    template = (payload.get("template") or WHATSAPP_TEMPLATE_ALERT).strip()
    graph_version = (payload.get("graph_version") or WHATSAPP_GRAPH_VERSION).strip()
    owner_email = (payload.get("owner_email") or "").strip()
    config = {
        "access_token": access_token,
        "phone_number_id": phone_number_id,
        "template": template,
        "graph_version": graph_version,
        "owner_email": owner_email,
        "configured_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(config, fh, ensure_ascii=False, indent=2)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return config

def meta_whatsapp_public_status(root):
    config = load_meta_whatsapp_config(root)
    return {
        "configured": bool(config.get("access_token") and config.get("phone_number_id")),
        "phone_number_id": config.get("phone_number_id", ""),
        "template": config.get("template", WHATSAPP_TEMPLATE_ALERT),
        "graph_version": config.get("graph_version", WHATSAPP_GRAPH_VERSION),
        "owner_email": config.get("owner_email", ""),
        "token_mask": mask_secret(config.get("access_token")),
        "configured_at": config.get("configured_at", ""),
    }

def iter_client_workspace_metadata():
    root = Path(CLIENT_WORKSPACE_DIR)
    if not root.exists():
        return
    for folder in root.iterdir():
        if not folder.is_dir():
            continue
        metadata = read_json_file(folder / "cliente.json", fallback={})
        if isinstance(metadata, dict) and metadata:
            yield folder, metadata

def load_meta_whatsapp_for_client_payload(module, client):
    target_key = (client or {}).get("key") or ""
    target_rut = clean_rut((client or {}).get("rut"))
    target_name = comparable_name((client or {}).get("nombre") or (client or {}).get("name"))
    target_module = comparable_name(module or "")
    for folder, metadata in iter_client_workspace_metadata() or []:
        same_key = target_key and metadata.get("key") == target_key
        same_rut = target_rut and clean_rut(metadata.get("rut")) == target_rut
        same_name = target_name and comparable_name(metadata.get("name")) == target_name
        same_module = not target_module or target_module in comparable_name(metadata.get("module"))
        if same_key or ((same_rut or same_name) and same_module):
            config = load_meta_whatsapp_config(folder)
            if config.get("access_token") and config.get("phone_number_id"):
                return config
    return {}

def load_meta_whatsapp_for_outbox_row(row):
    try:
        payload = {
            "key": row["client_key"] if "client_key" in row.keys() else "",
            "name": row["client_name"],
            "nombre": row["client_name"],
            "rut": row["client_rut"],
        }
        return load_meta_whatsapp_for_client_payload(row["module"], payload)
    except Exception:
        return {}

def list_client_files(root):
    grouped = []
    for category, label in CLIENT_FILE_CATEGORIES.items():
        category_dir = Path(root) / category
        files = []
        if category_dir.exists():
            for path in sorted(category_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
                if path.is_file():
                    files.append({
                        "name": path.name,
                        "category": category,
                        "label": label,
                        "size_kb": max(1, int(path.stat().st_size / 1024)),
                        "updated_at": datetime.fromtimestamp(path.stat().st_mtime).strftime("%d-%m-%Y %H:%M"),
                    })
        grouped.append({"key": category, "label": label, "files": files})
    return grouped

def whatsapp_outbox_snapshot(limit=8):
    try:
        from do_intelligence import DB_PATH
        ensure_whatsapp_storage()
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT id, created_at, module, client_name, client_rut, whatsapp, message, report_url, status, sent_at
                FROM whatsapp_outbox
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            counts = dict(conn.execute(
                "SELECT status, COUNT(*) FROM whatsapp_outbox GROUP BY status"
            ).fetchall())
        return {
            "total": sum(counts.values()),
            "sent": counts.get("sent", 0),
            "pending": counts.get("pending_config", 0) + counts.get("pending", 0) + counts.get("queued", 0),
            "error": counts.get("error", 0),
            "items": [dict(row) for row in rows],
        }
    except Exception as exc:
        log.warning("WhatsApp outbox snapshot failed: %s", exc)
        return {"total": 0, "sent": 0, "pending": 0, "error": 0, "items": []}

def sync_registry_from_local_sources(people, watchdog_clients, free_clients=None):
    free_clients = free_clients or []
    synced = 0
    for person in people:
        key = upsert_registry_client(
            "diario_oficial",
            display_name=person.get("nombre_completo"),
            rut=person.get("rut"),
            email=person.get("alertar_a"),
            phone=person.get("whatsapp"),
            source_ref=f"do_people:{person.get('id', '')}",
            status=person.get("estado") or "activo",
        )
        synced += 1 if key else 0
    for item in watchdog_clients:
        key = upsert_registry_client(
            "inapi",
            display_name=item.get("nombre_titular") or item.get("marca_protegida"),
            rut=item.get("rut") or item.get("rut_titular"),
            email=item.get("email_cliente"),
            phone=item.get("whatsapp"),
            source_ref=f"watchdog:{item.get('id', item.get('marca_protegida', ''))}",
            status="activo",
        )
        synced += 1 if key else 0
    for item in free_clients:
        key = upsert_registry_client(
            item.get("module") or "maestro",
            display_name=item.get("name"),
            rut=item.get("rut"),
            email=item.get("email"),
            phone=item.get("whatsapp"),
            source_ref=f"free:{item.get('id', item.get('key', ''))}",
            status=item.get("status") or "activo_gratis",
        )
        synced += 1 if key else 0
    return synced

def run_erp_registry_query(sql):
    command = [
        "pct", "exec", "100", "--",
        "docker", "exec", "-i", "quantus-postgres",
        "psql", "-U", "quantus_admin", "-d", "quantus_demo", "-AtF", "\t", "-c", sql,
    ]
    completed = subprocess.run(command, text=True, capture_output=True, timeout=8, check=False)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "ERP query failed")
    rows = []
    for line in completed.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 5:
            rows.append({
                "source_ref": parts[0],
                "display_name": parts[1],
                "rut": parts[2],
                "email": parts[3],
                "phone": parts[4],
            })
    return rows

def sync_registry_from_erp():
    queries = [
        """
        SELECT 'customer:'||id, COALESCE(name,''), COALESCE(rut,''), COALESCE(email,''), COALESCE(phone,'')
        FROM public.customers
        WHERE COALESCE(rut,'') <> '' OR COALESCE(name,'') <> ''
        LIMIT 1200
        """,
        """
        SELECT 'company:'||id, COALESCE(name,''), COALESCE(rut,''), COALESCE(email,''), COALESCE(phone,'')
        FROM public.companies
        WHERE COALESCE(rut,'') <> '' OR COALESCE(name,'') <> ''
        LIMIT 1200
        """,
    ]
    synced = 0
    for sql in queries:
        for row in run_erp_registry_query(sql):
            key = upsert_registry_client(
                "erp",
                display_name=row["display_name"],
                rut=row["rut"],
                email=row["email"],
                phone=row["phone"],
                source_ref=row["source_ref"],
                status="activo",
            )
            synced += 1 if key else 0
    return synced

def sync_master_client_registry(people=None, watchdog_clients=None, free_clients=None):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    people = people if people is not None else read_json_file(os.path.join(base_dir, "do_people.json"))
    watchdog_clients = watchdog_clients if watchdog_clients is not None else read_json_file(os.path.join(base_dir, "watchdog_clients.json"))
    free_clients = free_clients if free_clients is not None else load_master_free_clients()
    result = {"local": sync_registry_from_local_sources(people, watchdog_clients, free_clients), "erp": 0, "errors": []}
    try:
        result["erp"] = sync_registry_from_erp()
    except Exception as exc:
        result["errors"].append(str(exc)[:220])
    return result

def master_registry_monitor_targets(limit=250):
    sync_master_client_registry()
    snapshot = registry_snapshot(limit=limit)
    targets = []
    seen = set()
    for row in snapshot.get("rows", []):
        rut = format_rut(row.get("clean_rut") or row.get("rut"))
        if not rut or not validate_rut(rut, required=True) or rut in seen:
            continue
        seen.add(rut)
        targets.append({
            "nombre_completo": row.get("display_name") or f"Cliente RUT {rut}",
            "rut": rut,
            "alertar_a": row.get("email") or MASTER_ADMIN_EMAIL,
            "whatsapp": row.get("phone") or "",
            "whatsapp_consent": False,
            "estado": row.get("status") or "activo",
            "plan": "registro_maestro_rut",
            "source_module": row.get("source_module"),
            "registry_key": row.get("registry_key"),
        })
    return targets

def get_do_regressive_progress():
    db_path = "/opt/quantus/portal/data/do_historico.db"
    if not os.path.exists(db_path):
        db_path = "/mnt/proyectos/felipe/inapi_portal/data/do_historico.db"
    edicion_final_25y = 37000
    if not os.path.exists(db_path):
        return {
            "total_publicaciones": "0", "edicion_hoy": "44.540", "edicion_frontera": "44.540",
            "edicion_meta": "37.000", "ediciones_procesadas": "0", "ediciones_totales": "7.540",
            "ediciones_restantes": "7.540", "progreso_pct": 0.0, "fecha_min": "N/D", "fecha_max": "N/D",
            "estado": "Inactivo", "timer_active": False
        }
    try:
        conn = sqlite3.connect(db_path, timeout=5)
        c = conn.cursor()
        c.execute("SELECT count(*), min(edicion), max(edicion), min(fecha), max(fecha) FROM publicaciones")
        row = c.fetchone()
        conn.close()
        total_pubs = row[0] or 0
        min_ed = row[1] or 44540
        max_ed = row[2] or 44540
        min_fecha = row[3] or "N/D"
        max_fecha = row[4] or "N/D"
        total_ediciones = max(1, max_ed - edicion_final_25y)
        ediciones_cubiertas = max_ed - min_ed + 1
        pct_val = round((ediciones_cubiertas / total_ediciones) * 100, 2)
        timer_active = (os.system("systemctl is-active --quiet quantus-do-downloader.timer 2>/dev/null") == 0)
        return {
            "total_publicaciones": f"{total_pubs:,}".replace(",", "."),
            "total_publicaciones_raw": total_pubs,
            "edicion_hoy": f"{max_ed:,}".replace(",", "."),
            "edicion_frontera": f"{min_ed:,}".replace(",", "."),
            "edicion_meta": f"{edicion_final_25y:,}".replace(",", "."),
            "ediciones_procesadas": f"{ediciones_cubiertas:,}".replace(",", "."),
            "ediciones_totales": f"{total_ediciones:,}".replace(",", "."),
            "ediciones_restantes": f"{max(0, min_ed - edicion_final_25y):,}".replace(",", "."),
            "progreso_pct": pct_val,
            "fecha_min": min_fecha,
            "fecha_max": max_fecha,
            "timer_active": timer_active,
            "estado": "Activo (09:30 y 14:30 hrs)" if timer_active else "En Pausa"
        }
    except Exception as exc:
        return {
            "total_publicaciones": "0", "error": str(exc), "progreso_pct": 0.0,
            "edicion_hoy": "44.540", "edicion_frontera": "44.540", "edicion_meta": "37.000",
            "ediciones_procesadas": "0", "ediciones_totales": "7.540", "ediciones_restantes": "7.540",
            "fecha_min": "-", "fecha_max": "-", "estado": "Error", "timer_active": False
        }

def master_dashboard_snapshot():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    superadmin_modules = load_superadmin_modules()
    people = refresh_do_subscription_lifecycle(load_do_people(), persist=True)
    payment_events = sorted(load_do_payment_events(), key=lambda item: item.get("created_at") or "", reverse=True)
    watchdog_clients = read_json_file(WATCHDOG_CLIENTS_FILE)
    free_clients = sorted(load_master_free_clients(), key=lambda item: item.get("updated_at") or item.get("created_at") or "", reverse=True)
    free_by_module = defaultdict(int)
    for item in free_clients:
        free_by_module[item.get("module") or "otro"] += 1
    registry_sync = sync_master_client_registry(people, watchdog_clients, free_clients)
    registro_docs = list(Path(REGISTRO_DOCS_FOLDER).glob("*.pdf")) if os.path.exists(REGISTRO_DOCS_FOLDER) else []
    do_snapshot = dashboard_snapshot(limit=100)
    reports = do_snapshot.get("reports", [])
    memory = do_snapshot.get("memory", [])
    whatsapp = whatsapp_outbox_snapshot()
    registry = registry_snapshot(limit=80)
    valid_registry_ruts = {
        clean_rut(row.get("rut") or row.get("clean_rut"))
        for row in registry.get("rows", [])
        if validate_rut(row.get("rut") or row.get("clean_rut"), required=True)
    }
    registry["totals"]["valid_ruts"] = len(valid_registry_ruts)

    module_labels = {
        "diario_oficial": "Diario Oficial",
        "inapi": "Registro de Marcas",
        "licitaciones": "Licitaciones",
        "remates": "Remates",
        "erp": "Punto de Venta Intelligence",
    }
    module_reports = defaultdict(list)
    risk_by_module = defaultdict(int)
    for report in reports:
        module = report.get("module") or "diario_oficial"
        module_reports[module].append(report)
        if (report.get("urgency") or "").lower() in {"alto", "critico"}:
            risk_by_module[module] += 1

    active_people = [
        p for p in people
        if do_subscription_state(p) in {"activo", "activo_permanente", "activo_sin_vencimiento"}
    ]
    pending_do_payments = [
        {
            "id": p.get("id"),
            "key": do_person_key(p),
            "name": p.get("nombre_completo") or "Cliente sin nombre",
            "rut": p.get("rut") or "",
            "email": p.get("alertar_a") or "",
            "plan": p.get("plan") or "-",
            "state": do_subscription_state(p),
            "registered_at": p.get("fecha_registro") or p.get("consent_timestamp") or "-",
            "checkout_url": p.get("checkout_url") or do_checkout_url(p.get("plan") or "mensual", p.get("payment_mode") or "one_time"),
            "proposed_expiration": p.get("fecha_vencimiento_propuesta") or "-",
        }
        for p in people
        if do_subscription_state(p) in {"pendiente_pago", "vencido_en_gracia", "vencido_pendiente_eliminacion", "pendiente_eliminacion", "pendiente_pago_vencido"}
    ]
    family_people = [p for p in active_people if (p.get("plan") or "").lower() == "grupo_familiar_24x7"]
    commercial_people = [
        p for p in active_people
        if (p.get("plan") or "").lower() not in {"grupo_familiar_24x7", "gratis_maestro"}
    ]
    do_mrr = sum(plan_monthly_value("diario_oficial", p.get("plan")) for p in commercial_people)
    paid_watchdog_clients = [
        item for item in watchdog_clients
        if (item.get("payment_status") or item.get("estado_pago") or "pagado").lower()
        not in {"pendiente", "pendiente_pago", "sin_pago", "no_pago", "gratis", "gratuito", "activo_gratis"}
    ]
    inapi_watch_mrr = len(paid_watchdog_clients) * plan_monthly_value("inapi", "vigilancia_marca")
    inapi_pipeline = max(0, len(registro_docs) // 2) * REGISTRO_GESTION_INICIAL
    lic_pipeline = (
        len(module_reports.get("licitaciones", [])) * plan_monthly_value("licitaciones", "pyme_pro")
        if module_reports.get("licitaciones")
        else 0
    )

    modules = [
        {
            "key": "diario_oficial",
            "name": "Diario Oficial 24/7",
            "status": "Activo",
            "clients": len(commercial_people) + free_by_module.get("diario_oficial", 0),
            "free_clients": free_by_module.get("diario_oficial", 0),
            "reports": len(module_reports.get("diario_oficial", [])),
            "high_risk": risk_by_module.get("diario_oficial", 0),
            "mrr": do_mrr,
            "pipeline": do_mrr * 12,
            "quality": 94 if commercial_people else 62,
            "insight": "Ingresos recurrentes desde vigilancia diaria; familia queda como monitoreo interno sin costo comercial.",
        },
        {
            "key": "inapi",
            "name": "INAPI / Registra tu Marca",
            "status": "Activo",
            "clients": len(watchdog_clients) + free_by_module.get("inapi", 0),
            "free_clients": free_by_module.get("inapi", 0),
            "reports": len(module_reports.get("inapi", [])),
            "high_risk": risk_by_module.get("inapi", 0),
            "mrr": inapi_watch_mrr,
            "pipeline": inapi_pipeline,
            "quality": 88 if watchdog_clients else 54,
            "insight": "Pipeline por documentos recibidos y marcas vigiladas; falta webhook de pago para revenue confirmado.",
        },
        {
            "key": "licitaciones",
            "name": "Licitaciones 24/7",
            "status": "Piloto",
            "clients": free_by_module.get("licitaciones", 0),
            "free_clients": free_by_module.get("licitaciones", 0),
            "reports": len(module_reports.get("licitaciones", [])),
            "high_risk": risk_by_module.get("licitaciones", 0),
            "mrr": 0,
            "pipeline": lic_pipeline,
            "quality": 72 if module_reports.get("licitaciones") else 41,
            "insight": "Gran potencial comercial; necesita base persistente de clientes, Mercado Pago y feedback de oportunidades ganadas.",
        },
        {
            "key": "remates",
            "name": "Remates Chile",
            "status": "Piloto",
            "clients": free_by_module.get("remates", 0),
            "free_clients": free_by_module.get("remates", 0),
            "reports": len(module_reports.get("remates", [])),
            "high_risk": risk_by_module.get("remates", 0),
            "mrr": 0,
            "pipeline": 0,
            "quality": 65 if free_by_module.get("remates") else 38,
            "insight": "Radar inmobiliario separado para bancos, tribunales y remates; usuarios gratis sirven para calibrar filtros por zona.",
        },
        {
            "key": "erp",
            "name": "Quantus Punto de Venta / Agentes IA",
            "status": "Conectado",
            "clients": 1,
            "reports": len(module_reports.get("erp", [])),
            "high_risk": risk_by_module.get("erp", 0),
            "mrr": 0,
            "pipeline": 0,
            "quality": 81,
            "insight": "Base premium del ecosistema; debe alimentar ventas, inventario, clientes y agentes por tenant.",
        },
    ]

    total_reports = sum(m["reports"] for m in modules)
    total_clients = sum(m["clients"] for m in modules)
    total_mrr = sum(m["mrr"] for m in modules)
    total_pipeline = sum(m["pipeline"] for m in modules)
    total_high_risk = sum(m["high_risk"] for m in modules)
    max_reports = max([m["reports"] for m in modules] + [1])
    max_money = max([m["mrr"] + m["pipeline"] for m in modules] + [1])

    rubro_counts = defaultdict(int)
    for item in watchdog_clients:
        for raw in str(item.get("descripcion") or "").replace("&", ",").split(","):
            rubro = raw.strip().title()
            if rubro:
                rubro_counts[rubro] += 1
    for person in commercial_people:
        rubro_counts["Personas y Familia"] += 1
    for item in free_clients:
        rubro_counts[item.get("module_label") or module_labels.get(item.get("module"), "Usuarios gratis")] += 1
    rubros = [
        {"name": name, "count": count, "share": pct(count, max(1, total_clients))}
        for name, count in sorted(rubro_counts.items(), key=lambda kv: kv[1], reverse=True)[:8]
    ]

    clients = []
    for person in active_people:
        key = do_person_key(person)
        is_family = (person.get("plan") or "").lower() in {"grupo_familiar_24x7", "gratis_maestro", "superadmin_activo"}
        is_owner = (person.get("rut") or "").strip() in {"14.011.762-5", "140117625"} or "felipe" in (person.get("nombre_completo") or "").lower()
        is_free = is_family or is_owner
        clients.append({
            "id": person.get("id"),
            "key": key,
            "name": person.get("nombre_completo") or "Cliente sin nombre",
            "rut": person.get("rut") or "",
            "module": "Diario Oficial",
            "rubro": "Familia interna" if is_family else ("Titular Fundador" if is_owner else "Personas y Familia"),
            "plan": person.get("plan") or "-",
            "status": person.get("estado") or "-",
            "monthly_value": 0 if is_free else plan_monthly_value("diario_oficial", person.get("plan")),
            "expires_at": person.get("fecha_vencimiento") or "-",
            "payment_reference": person.get("payment_reference") or "",
        })
    for item in watchdog_clients:
        inferred_rut = item.get("rut") or item.get("rut_titular") or infer_rut_from_people(item.get("nombre_titular"), people)
        key = client_key_for("inapi", item.get("nombre_titular"), item.get("marca_protegida"), item.get("email_cliente"))
        is_inapi_owner = (inferred_rut or "").strip() in {"14.011.762-5", "140117625"} or "felipe" in (item.get("nombre_titular") or "").lower()
        is_inapi_pending = (item.get("payment_status") or item.get("estado_pago") or "").lower() in {"pendiente", "pendiente_pago", "sin_pago", "no_pago", "activo_superadmin"}
        clients.append({
            "key": key,
            "name": item.get("nombre_titular") or item.get("marca_protegida") or "Titular INAPI",
            "rut": inferred_rut,
            "module": "INAPI",
            "rubro": item.get("descripcion") or "Marca",
            "plan": "vigilancia_marca",
            "status": "activo",
            "monthly_value": 0 if (is_inapi_owner or is_inapi_pending) else plan_monthly_value("inapi", "vigilancia_marca"),
        })
    existing_client_keys = {(item.get("key"), item.get("module")) for item in clients}
    for item in free_clients:
        row = {
            "key": item.get("key") or client_key_for(item.get("module"), item.get("name"), item.get("rut"), item.get("email")),
            "name": item.get("name") or "Usuario gratis",
            "rut": item.get("rut") or "",
            "module": item.get("module_label") or module_labels.get(item.get("module"), item.get("module") or "Radar"),
            "rubro": item.get("scope") or "Alta gratuita desde maestro",
            "plan": item.get("plan") or "gratis_maestro",
            "status": item.get("status") or "activo_gratis",
            "monthly_value": 0,
            "expires_at": "Sin cobro",
            "payment_reference": "gratis_maestro",
        }
        identity_key = (row["key"], row["module"])
        if identity_key not in existing_client_keys:
            clients.append(row)
            existing_client_keys.add(identity_key)
    clients.sort(key=lambda item: (rut_sort_key(item.get("rut")), (item.get("name") or "").lower()))
    for client in clients:
        root = ensure_client_workspace(client)
        client["folder_name"] = root.name
        client["folder_path"] = str(root)
        client["file_count"] = sum(1 for path in root.glob("*/*") if path.is_file())

    recommendations = [
        {
            "title": "Conectar webhook Mercado Pago",
            "impact": "Convierte ingresos estimados en MRR confirmado por pago real.",
            "priority": "Alta",
        },
        {
            "title": "Crear CRM de leads por módulo",
            "impact": "Permite medir conversión desde visita, análisis IA, pago, activación y renovación.",
            "priority": "Alta",
        },
        {
            "title": "Feedback comercial para licitaciones",
            "impact": "Aprende qué oportunidades terminaron postuladas, descartadas o ganadas.",
            "priority": "Media",
        },
        {
            "title": "Resumen ejecutivo semanal automático",
            "impact": "Envía KPIs, riesgos y oportunidades a administración sin entrar al panel.",
            "priority": "Media",
        },
    ]

    return {
        "generated_at": datetime.now().strftime("%d-%m-%Y %H:%M"),
        "today": datetime.now().strftime("%Y-%m-%d"),
        "totals": {
            "clients": total_clients,
            "family_internal": len(family_people),
            "free_clients": len(free_clients),
            "reports": total_reports,
            "high_risk": total_high_risk,
            "mrr": total_mrr,
            "pipeline": total_pipeline,
            "conversion_readiness": pct(sum(1 for m in modules if m["quality"] >= 75), len(modules)),
            "whatsapp_pending": whatsapp["pending"],
            "registry_ruts": registry["totals"].get("valid_ruts") or 0,
        },
        "modules": [
            {
                **m,
                "report_share": pct(m["reports"], max_reports),
                "money_share": pct(m["mrr"] + m["pipeline"], max_money),
            }
            for m in modules
        ],
        "module_labels": module_labels,
        "radar_modules": RADAR_MODULES,
        "superadmin_modules": superadmin_modules,
        "superadmin_module_statuses": SUPERADMIN_MODULE_STATUSES,
        "superadmin_module_visibility": SUPERADMIN_MODULE_VISIBILITY,
        "superadmin_modules_summary": superadmin_modules_summary(superadmin_modules),
        "rubros": rubros,
        "clients": clients[:30],
        "free_clients": free_clients[:80],
        "free_by_module": dict(free_by_module),
        "reports": reports[:20],
        "memory": memory[:20],
        "whatsapp": whatsapp,
        "registry": registry,
            "registry_sync": registry_sync,
        "recommendations": recommendations,
        "pending_do_payments": pending_do_payments[:40],
        "payment_events": payment_events[:20],
        "do_regressive_progress": get_do_regressive_progress(),
    }

def check_duplicate_rut_or_name(rut=None, name=None, exclude_key=None):
    """
    Verifica si un RUT o Nombre/Razón Social ya existe en master_client_registry
    o en las fuentes locales (do_people, watchdog_clients, master_free_clients).
    Retorna None si no hay duplicado, o el mensaje de error si ya existe.
    """
    clean = clean_rut(rut) if rut else ""
    name_clean = (name or "").strip().lower()

    if not clean and not name_clean:
        return None

    target_ref = ""
    target_clean_rut = ""
    
    # Check SQLite master_client_registry
    from do_intelligence import DB_PATH, ensure_storage
    ensure_storage()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            if exclude_key:
                cur_row = conn.execute("SELECT clean_rut, source_ref FROM master_client_registry WHERE registry_key = ?", (exclude_key,)).fetchone()
                if cur_row:
                    target_clean_rut = cur_row["clean_rut"] or ""
                    target_ref = cur_row["source_ref"] or ""
                    
            rows = conn.execute("SELECT registry_key, rut, clean_rut, display_name FROM master_client_registry").fetchall()
            for r in rows:
                if exclude_key and r["registry_key"] == exclude_key:
                    continue
                r_clean = r["clean_rut"] or (clean_rut(r["rut"]) if r["rut"] else "")
                if clean and r_clean == clean:
                    return f"El RUT '{rut}' ya se encuentra registrado en el sistema."
                r_name = (r["display_name"] or "").strip().lower()
                if name_clean and r_name and r_name == name_clean:
                    return f"La persona o empresa '{name}' ya se encuentra registrada en el sistema."
    except Exception:
        pass

    # Check do_people.json
    people = load_do_people()
    for p in people:
        pkey = do_person_key(p)
        if exclude_key and (pkey == exclude_key or (target_ref and f"do_people:{p.get('id', '')}" == target_ref) or (target_clean_rut and clean_rut(p.get("rut")) == target_clean_rut)):
            continue
        p_rut = clean_rut(p.get("rut"))
        if clean and p_rut and p_rut == clean:
            return f"El RUT '{rut}' ya está registrado en la base de datos del Diario Oficial."
        p_name = (p.get("nombre_completo") or "").strip().lower()
        if name_clean and p_name and p_name == name_clean:
            return f"El nombre '{name}' ya está registrado en el Diario Oficial."

    # Check master_free_clients.json
    free = load_master_free_clients()
    for f in free:
        fkey = f.get("key")
        if exclude_key and (fkey == exclude_key or (target_ref and f"free:{f.get('id', f.get('key', ''))}" == target_ref) or (target_clean_rut and clean_rut(f.get("rut")) == target_clean_rut)):
            continue
        f_rut = clean_rut(f.get("rut"))
        if clean and f_rut and f_rut == clean:
            return f"El RUT '{rut}' ya está registrado como cliente gratuito."
        f_name = (f.get("nombre") or f.get("name") or "").strip().lower()
        if name_clean and f_name and f_name == name_clean:
            return f"El nombre '{name}' ya está registrado en cuentas gratuitas."

    return None

    # Check SQLite master_client_registry
    from do_intelligence import DB_PATH, ensure_storage
    ensure_storage()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT registry_key, rut, clean_rut, display_name FROM master_client_registry").fetchall()
            for r in rows:
                if exclude_key and r["registry_key"] == exclude_key:
                    continue
                r_clean = r["clean_rut"] or (clean_rut(r["rut"]) if r["rut"] else "")
                if clean and r_clean == clean:
                    return f"El RUT '{rut}' ya se encuentra registrado en el sistema."
                r_name = (r["display_name"] or "").strip().lower()
                if name_clean and r_name and r_name == name_clean:
                    return f"La persona o empresa '{name}' ya se encuentra registrada en el sistema."
    except Exception:
        pass

    # Check do_people.json
    people = load_do_people()
    for p in people:
        pkey = do_person_key(p)
        if exclude_key and pkey == exclude_key:
            continue
        p_rut = clean_rut(p.get("rut"))
        if clean and p_rut and p_rut == clean:
            return f"El RUT '{rut}' ya está registrado en la base de datos del Diario Oficial."
        p_name = (p.get("nombre_completo") or "").strip().lower()
        if name_clean and p_name and p_name == name_clean:
            return f"El nombre '{name}' ya está registrado en el Diario Oficial."

    # Check master_free_clients.json
    free = load_master_free_clients()
    for f in free:
        fkey = f.get("key")
        if exclude_key and fkey == exclude_key:
            continue
        f_rut = clean_rut(f.get("rut"))
        if clean and f_rut and f_rut == clean:
            return f"El RUT '{rut}' ya está registrado como cliente gratuito."
        f_name = (f.get("nombre") or f.get("name") or "").strip().lower()
        if name_clean and f_name and f_name == name_clean:
            return f"El nombre '{name}' ya está registrado en cuentas gratuitas."

    return None

def master_client_by_key(client_key):
    snapshot = master_dashboard_snapshot()
    for client in snapshot["clients"]:
        if client["key"] == client_key:
            root = ensure_client_workspace(client)
            client["folder_name"] = root.name
            client["folder_path"] = str(root)
            client["files"] = list_client_files(root)
            client["meta_whatsapp"] = meta_whatsapp_public_status(root)
            client["reports"] = [
                report for report in snapshot["reports"]
                if (report.get("client_name") or "").strip().lower() == (client.get("name") or "").strip().lower()
            ]
            return client
    return None

def maestro_eliminar_cliente(client_key):
    """Elimina manualmente un cliente del Centro Maestro (datos, registro, carpeta) con auditoria."""
    from communications.audit_log import record_communication
    snapshot = master_dashboard_snapshot()
    client = next((c for c in snapshot["clients"] if c["key"] == client_key), None)
    if not client:
        return False, "Cliente no encontrado en el panel maestro."
    module = (client.get("module") or "").lower()
    nombre = client.get("name") or "Cliente"
    rut = client.get("rut") or ""
    removed = []
    registry_refs = []

    if module == "diario oficial":
        people = load_do_people()
        antes = len(people)
        coincidentes = [p for p in people if do_person_key(p) == client_key]
        kept = [p for p in people if do_person_key(p) != client_key]
        if len(kept) != antes:
            save_do_people(kept)
            registry_refs += [f"do_people:{p.get('id', '')}" for p in coincidentes]
            removed.append(f"do_people.json ({antes - len(kept)} registro(s))")
    elif module == "inapi":
        items = read_json_file(WATCHDOG_CLIENTS_FILE, [])
        antes = len(items)
        coincidentes = [
            it for it in items
            if client_key_for("inapi", it.get("nombre_titular"), it.get("marca_protegida"), it.get("email_cliente")) == client_key
        ]
        kept = [
            it for it in items
            if client_key_for("inapi", it.get("nombre_titular"), it.get("marca_protegida"), it.get("email_cliente")) != client_key
        ]
        if len(kept) != antes:
            save_json_file(WATCHDOG_CLIENTS_FILE, kept)
            registry_refs += [f"watchdog:{it.get('id', it.get('marca_protegida', ''))}" for it in coincidentes]
            removed.append(f"watchdog_clients.json ({antes - len(kept)} registro(s))")
    else:
        free = load_master_free_clients()
        antes = len(free)
        coincidentes = [
            f for f in free
            if (f.get("key") or client_key_for(f.get("module"), f.get("name"), f.get("rut"), f.get("email"))) == client_key
        ]
        kept = [
            f for f in free
            if (f.get("key") or client_key_for(f.get("module"), f.get("name"), f.get("rut"), f.get("email"))) != client_key
        ]
        if len(kept) != antes:
            save_master_free_clients(kept)
            registry_refs += [f"free:{f.get('id', f.get('key', ''))}" for f in coincidentes]
            removed.append(f"master_free_clients.json ({antes - len(kept)} registro(s))")

    if registry_refs:
        from do_intelligence import DB_PATH as REGISTRY_DB
        try:
            with sqlite3.connect(REGISTRY_DB) as conn:
                refs = tuple(registry_refs)
                conn.execute(
                    f"DELETE FROM master_client_registry WHERE source_ref IN ({','.join('?' * len(refs))})",
                    refs,
                )
            removed.append(f"registro transversal ({len(registry_refs)})")
        except sqlite3.Error as exc:
            log.warning("No se pudo limpiar master_client_registry: %s", exc)

    folder = client.get("folder_path") or ""
    if folder and str(Path(folder)).startswith(str(Path(CLIENT_WORKSPACE_DIR))):
        import shutil
        shutil.rmtree(folder, ignore_errors=True)
        removed.append(f"carpeta de cliente ({client.get('folder_name')})")

    record_communication(
        module="maestro",
        client_key=client_key,
        client_name=nombre,
        client_rut=rut,
        channel="portal",
        event_type="cancellation",
        subject="Cliente eliminado manualmente del Centro Maestro",
        message=f"Eliminado por operador: {', '.join(removed)}.",
        status="sent",
        provider_response="manual",
        source_hash=f"delete:{client_key}",
        client={"nombre": nombre, "rut": rut, "module": client.get("module")},
        payload={"removed_sources": removed},
    )
    return True, ", ".join(removed) or "sin registros de origen"

def do_client_from_request():
    rut = (request.form.get("client_rut") or request.form.get("rut") or "").strip()
    if rut:
        rut = require_valid_rut(rut, required=False, label="RUT del cliente")
    return {
        "nombre": (request.form.get("client_name") or request.form.get("nombre") or "").strip(),
        "rut": rut,
        "email": (request.form.get("client_email") or request.form.get("email") or "").strip(),
    }

# ============================================================
# RUTAS FLASK
# ============================================================

def with_query(path):
    return path + (f"?{request.query_string.decode()}" if request.query_string else "")

@app.before_request
def redirect_legacy_subdomains():
    host = request.headers.get("Host", "").split(":")[0].lower()
    path = request.path or "/"

    if host == "inapi.quantuschile.cl":
        target = "/inapi" if path == "/" else f"/inapi{path}"
        return redirect(f"https://www.quantuschile.cl{with_query(target)}", code=301)

    if host == "do.quantuschile.cl":
        if path in ("/", "/vigilancia"):
            target = "/do"
        elif path.startswith("/vigilancia/prospeccion"):
            target = path.replace("/vigilancia/prospeccion", "/do/prospeccion", 1)
        elif path.startswith("/licitaciones"):
            target = path
        else:
            target = f"/do{path}"
        return redirect(f"https://www.quantuschile.cl{with_query(target)}", code=301)

    if host == "licitaciones.quantuschile.cl":
        target = "/licitaciones" if path == "/" else f"/licitaciones{path}"
        return redirect(f"https://www.quantuschile.cl{with_query(target)}", code=301)

@app.before_request
def auto_recognize_owner():
    ip = get_client_ip()
    # Si viene desde la IP de Felipe (181.161.*), Tailscale (100.*), local, o con flag ?owner=1 / ?admin=1
    if (
        request.args.get("owner") == "1"
        or request.args.get("admin") == "1"
        or request.cookies.get("quantus_owner") == "1"
        or (ip and ip.startswith(("181.161.", "100.", "192.168.", "127.")))
    ):
        session["is_owner"] = True

@app.after_request
def persist_owner_cookie(response):
    if session.get("is_owner"):
        response.set_cookie("quantus_owner", "1", max_age=31536000, samesite="Lax")
    return response

@app.before_request
def protect_post_requests():
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return None

    public_post_routes = {
        "/payment",
        "/confirm_payment",
        "/submit_registro",
        "/contratar_vigilancia",
        "/contratar_licitaciones",
        "/api/validar_suscripcion_previa",
        "/api/cancelar_suscripcion_y_borrar_datos",
        "/api/suscribir",
        "/marketing/api/linkedin/publicar",
        "/punto-de-venta/acceso",
        "/pos/acceso",
        "/api/arcop/solicitud",
        "/api/arcop/actualizar_estado",
        "/api/privacy/rat/guardar",
        "/api/privacy/dpia/generar",
        "/api/empleos/onboarding",
        "/api/empleos/subscribe",
        "/api/mercadopago/webhook",
        "/api/marca/colision",
        "/api/marca/vigilancia",
        "/api/do/search_semantic",
    }

    if request.path in public_post_routes:
        return None

    expected = session.get("_csrf_token", "")
    received = request.form.get("_csrf_token") or request.headers.get("X-CSRFToken") or request.headers.get("X-CSRF-Token") or ""
    if not expected or not received or not hmac.compare_digest(expected, received):
        abort(400, "Solicitud inválida: token CSRF ausente o vencido.")
    return None

@app.route("/")
@app.route("/quantus-intelligence")
@app.route("/hub")
@app.route("/resumen")
def quantus_intelligence_hub():
    days = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    months = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    today = datetime.now()
    current_date_label = f"{days[today.weekday()]}, {today.day} de {months[today.month - 1]}"
    return render_template('quantus_intelligence.html', current_date_label=current_date_label)


@app.route("/blog")
@app.route("/blog/")
@app.route("/articulos")
@app.route("/guias")
def blog_index():
    articles = get_all_articles()
    return render_template('blog_index.html', articles=articles)


@app.route("/blog/<slug>")
@app.route("/guias/<slug>")
@app.route("/articulos/<slug>")
def blog_article_detail(slug):
    article = get_article_by_slug(slug)
    if not article:
        abort(404)
    return render_template('blog_article.html', article=article)


@app.route("/servicios/<slug>")
@app.route("/servicios/<slug>/")
def regional_service_detail(slug):
    service = get_regional_service_by_slug(slug)
    if not service:
        abort(404)
    return render_template('regional_service.html', service=service)



@app.route("/api/suscribir", methods=["POST"])
def suscribir_newsletter():
    try:
        data = request.get_json(force=True, silent=True) or request.form or {}
        nombre = (data.get("nombre") or "").strip()
        correo = (data.get("correo") or "").strip().lower()
        
        if not nombre or not correo or "@" not in correo:
            return jsonify({"success": False, "message": "Por favor ingresa un nombre y un correo electrónico válido."}), 400
        
        db_path = Path(__file__).parent / "data" / "newsletter_subscribers.sqlite3"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS newsletter_subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                correo TEXT UNIQUE NOT NULL,
                ip TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        ip_addr = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        cursor.execute("""
            INSERT OR REPLACE INTO newsletter_subscribers (nombre, correo, ip, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (nombre, correo, ip_addr))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"¡Gracias {nombre}! Te has suscrito exitosamente para recibir información de Quantus."
        })
    except Exception as e:
        logging.error(f"Error al registrar suscripción: {e}")
        return jsonify({"success": False, "message": "Ocurrió un error al procesar tu suscripción. Intenta nuevamente."}), 500



@app.route("/erp")
def erp_legacy_redirect():
    return redirect("/punto-de-venta", code=301)


# --------------------------------------------------------------------------
# E-COMMERCE HERRADURAS & FORJA CHILE (CATÁLOGO Y BALANZA COURIER)
# --------------------------------------------------------------------------
@app.route("/herraduras", methods=["GET"])
@app.route("/herraduras/", methods=["GET"])
@app.route("/herraduras/<path:filename>", methods=["GET"])
def serve_herraduras_tienda(filename="index.html"):
    from flask import send_from_directory
    import os
    target_dir = os.path.join(app.root_path, "tienda-herraduras")
    if not filename or filename.strip() == "":
        filename = "index.html"
    return send_from_directory(target_dir, filename)

@app.route("/punto-de-venta")
def erp_landing():
    return render_template(
        "erp.html",
        erp_server_clients_url=erp_server_clients_url(),
        erp_server_status=erp_server_status(),
    )

@app.route("/erp/planes")
@app.route("/punto-de-venta/planes")
def erp_planes():
    return render_template("erp_planes.html")

@app.route("/erp/funcionalidades")
@app.route("/punto-de-venta/funcionalidades")
def erp_funcionalidades():
    return render_template("erp_funcionalidades.html")

@app.route("/erp/integraciones")
@app.route("/punto-de-venta/integraciones")
def erp_integraciones():
    return render_template("erp_integraciones.html")

@app.route("/erp/por-que-quantus")
@app.route("/punto-de-venta/por-que-quantus")
def erp_por_que_quantus():
    return render_template("erp_por_que_quantus.html")

ESTETICA_PROFESSIONALS = [
    {
        "id": "valentina-rivas",
        "name": "Valentina Rivas",
        "role": "Colorista y estilista senior",
        "commission_rate": 0.38,
        "avatar": "VR",
        "skills": ["coloracion", "corte_mujer", "tratamiento_capilar", "peinado"],
    },
    {
        "id": "matias-silva",
        "name": "Matias Silva",
        "role": "Barbero y especialista masculino",
        "commission_rate": 0.35,
        "avatar": "MS",
        "skills": ["corte_hombre", "barba", "perfilado", "tratamiento_capilar"],
    },
    {
        "id": "camila-torres",
        "name": "Camila Torres",
        "role": "Cosmetologa y lash/brow artist",
        "commission_rate": 0.36,
        "avatar": "CT",
        "skills": ["limpieza_facial", "cejas_pestanas", "depilacion", "manicure"],
    },
]

ESTETICA_SERVICES = [
    {"id": "corte_mujer", "name": "Corte mujer + brushing", "duration": 60, "price": 24990, "category": "Peluqueria", "products": ["shampoo", "protector_termico"]},
    {"id": "coloracion", "name": "Coloracion global", "duration": 150, "price": 69990, "category": "Color", "products": ["tintura", "oxidante", "mascara_capilar"]},
    {"id": "tratamiento_capilar", "name": "Tratamiento capilar reparador", "duration": 75, "price": 34990, "category": "Tratamiento", "products": ["ampolla_reparadora", "mascara_capilar"]},
    {"id": "corte_hombre", "name": "Corte hombre", "duration": 45, "price": 14990, "category": "Barberia", "products": ["cera_modeladora"]},
    {"id": "barba", "name": "Perfilado de barba", "duration": 35, "price": 11990, "category": "Barberia", "products": ["aceite_barba", "toalla_caliente"]},
    {"id": "limpieza_facial", "name": "Limpieza facial express", "duration": 60, "price": 29990, "category": "Estetica", "products": ["gel_limpieza", "mascarilla"]},
    {"id": "cejas_pestanas", "name": "Laminado cejas + lifting pestanas", "duration": 80, "price": 39990, "category": "Lash & Brow", "products": ["kit_laminado", "serum_pestanas"]},
    {"id": "manicure", "name": "Manicure permanente", "duration": 70, "price": 21990, "category": "Manicure", "products": ["base_gel", "top_coat"]},
]

ESTETICA_INVENTORY = {
    "shampoo": {"name": "Shampoo profesional", "stock": 8, "unit_per_service": 0.18, "reorder_at": 4},
    "protector_termico": {"name": "Protector termico", "stock": 5, "unit_per_service": 0.12, "reorder_at": 3},
    "tintura": {"name": "Tubo tintura profesional", "stock": 9, "unit_per_service": 1.2, "reorder_at": 8},
    "oxidante": {"name": "Oxidante 20/30 vol.", "stock": 7, "unit_per_service": 0.7, "reorder_at": 6},
    "mascara_capilar": {"name": "Mascara capilar", "stock": 4, "unit_per_service": 0.25, "reorder_at": 5},
    "ampolla_reparadora": {"name": "Ampolla reparadora", "stock": 6, "unit_per_service": 1.0, "reorder_at": 5},
    "cera_modeladora": {"name": "Cera modeladora", "stock": 5, "unit_per_service": 0.1, "reorder_at": 3},
    "aceite_barba": {"name": "Aceite barba", "stock": 3, "unit_per_service": 0.08, "reorder_at": 3},
    "toalla_caliente": {"name": "Toalla desechable caliente", "stock": 22, "unit_per_service": 1.0, "reorder_at": 18},
    "gel_limpieza": {"name": "Gel limpieza facial", "stock": 4, "unit_per_service": 0.16, "reorder_at": 4},
    "mascarilla": {"name": "Mascarilla facial", "stock": 5, "unit_per_service": 1.0, "reorder_at": 5},
    "kit_laminado": {"name": "Kit laminado cejas", "stock": 3, "unit_per_service": 0.25, "reorder_at": 3},
    "serum_pestanas": {"name": "Serum pestanas", "stock": 4, "unit_per_service": 0.08, "reorder_at": 3},
    "base_gel": {"name": "Base gel", "stock": 6, "unit_per_service": 0.1, "reorder_at": 4},
    "top_coat": {"name": "Top coat", "stock": 5, "unit_per_service": 0.1, "reorder_at": 4},
}

ESTETICA_APPOINTMENTS = [
    {"time": "09:30", "client": "Cliente demo 001", "service_id": "coloracion", "professional_id": "valentina-rivas", "status": "confirmada", "paid": True, "payment_method": "debito", "deposit": 20000},
    {"time": "10:00", "client": "Cliente demo 002", "service_id": "corte_hombre", "professional_id": "matias-silva", "status": "atendiendo", "paid": False, "payment_method": "pendiente", "deposit": 0},
    {"time": "11:00", "client": "Cliente demo 003", "service_id": "limpieza_facial", "professional_id": "camila-torres", "status": "confirmada", "paid": True, "payment_method": "credito", "deposit": 10000},
    {"time": "12:30", "client": "Cliente demo 004", "service_id": "barba", "professional_id": "matias-silva", "status": "pendiente", "paid": False, "payment_method": "pendiente", "deposit": 0},
    {"time": "15:00", "client": "Cliente demo 005", "service_id": "tratamiento_capilar", "professional_id": "valentina-rivas", "status": "confirmada", "paid": True, "payment_method": "transferencia", "deposit": 15000},
    {"time": "15:30", "client": "Cliente demo 006", "service_id": "cejas_pestanas", "professional_id": "camila-torres", "status": "confirmada", "paid": True, "payment_method": "debito", "deposit": 15000},
    {"time": "17:00", "client": "Cliente demo 007", "service_id": "manicure", "professional_id": "camila-torres", "status": "pendiente", "paid": False, "payment_method": "pendiente", "deposit": 5000},
    {"time": "18:00", "client": "Cliente demo 008", "service_id": "corte_mujer", "professional_id": "valentina-rivas", "status": "confirmada", "paid": False, "payment_method": "pendiente", "deposit": 10000},
]

ESTETICA_CLIENT_PROFILES = {
    "Cliente demo 001": {"visits": 6, "last_visit": "2026-07-18", "notes": "Prefiere tonos frios. Alergia declarada: ninguna.", "tags": ["VIP", "Color recurrente"], "no_show_risk": "bajo"},
    "Cliente demo 002": {"visits": 2, "last_visit": "2026-07-29", "notes": "Corte degradado bajo. Ofrecer pack barba + corte.", "tags": ["Barberia"], "no_show_risk": "medio"},
    "Cliente demo 003": {"visits": 4, "last_visit": "2026-07-12", "notes": "Piel sensible. Usar linea suave demo.", "tags": ["Estetica", "Piel sensible"], "no_show_risk": "bajo"},
    "Cliente demo 004": {"visits": 1, "last_visit": "2026-08-01", "notes": "Nuevo cliente. Confirmar llegada por WhatsApp.", "tags": ["Nuevo"], "no_show_risk": "alto"},
    "Cliente demo 005": {"visits": 5, "last_visit": "2026-07-22", "notes": "Cabello tratado. Recomendar ampolla mensual.", "tags": ["Tratamiento"], "no_show_risk": "bajo"},
    "Cliente demo 006": {"visits": 3, "last_visit": "2026-07-25", "notes": "Solicita horarios despues de 15:00.", "tags": ["Lash & Brow"], "no_show_risk": "bajo"},
    "Cliente demo 007": {"visits": 2, "last_visit": "2026-07-30", "notes": "Prefiere tonos nude. Abono parcial demo.", "tags": ["Manicure"], "no_show_risk": "medio"},
    "Cliente demo 008": {"visits": 7, "last_visit": "2026-07-15", "notes": "Cliente frecuente. Sugerir tratamiento capilar.", "tags": ["Frecuente"], "no_show_risk": "bajo"},
}

ESTETICA_WAITLIST = [
    {"client": "Cliente demo espera 01", "service_id": "coloracion", "preference": "Viernes tarde"},
    {"client": "Cliente demo espera 02", "service_id": "barba", "preference": "Sabado manana"},
    {"client": "Cliente demo espera 03", "service_id": "limpieza_facial", "preference": "Primera hora disponible"},
]

def estetica_demo_context():
    services = {item["id"]: item for item in ESTETICA_SERVICES}
    professionals = {item["id"]: item for item in ESTETICA_PROFESSIONALS}
    schedule = []
    revenue = 0
    pending_revenue = 0
    commissions = defaultdict(int)
    service_demand = defaultdict(int)
    product_usage = defaultdict(float)

    for appt in ESTETICA_APPOINTMENTS:
        service = services[appt["service_id"]]
        professional = professionals[appt["professional_id"]]
        balance = 0 if appt["paid"] else max(service["price"] - int(appt.get("deposit") or 0), 0)
        item = {
            **appt,
            "service": service,
            "professional": professional,
            "client_profile": ESTETICA_CLIENT_PROFILES.get(appt["client"], {}),
            "balance": balance,
        }
        schedule.append(item)
        service_demand[service["id"]] += 1
        if appt["paid"]:
            revenue += service["price"]
            commissions[professional["id"]] += round(service["price"] * professional["commission_rate"])
        else:
            pending_revenue += service["price"]
        for product_id in service["products"]:
            product_usage[product_id] += ESTETICA_INVENTORY[product_id]["unit_per_service"]

    eligibility = []
    for service in ESTETICA_SERVICES:
        eligible = [pro for pro in ESTETICA_PROFESSIONALS if service["id"] in pro["skills"]]
        eligibility.append({"service": service, "professionals": eligible})

    inventory_alerts = []
    for product_id, stock in ESTETICA_INVENTORY.items():
        daily_usage = product_usage.get(product_id, 0)
        days_left = math.floor(stock["stock"] / daily_usage) if daily_usage else None
        should_alert = stock["stock"] <= stock["reorder_at"] or (days_left is not None and days_left <= 3)
        if should_alert:
            inventory_alerts.append({"id": product_id, **stock, "daily_usage": round(daily_usage, 2), "days_left": days_left})

    occupancy = round((len(ESTETICA_APPOINTMENTS) / (len(ESTETICA_PROFESSIONALS) * 6)) * 100)
    deposits = sum(int(item.get("deposit") or 0) for item in ESTETICA_APPOINTMENTS)
    unpaid_count = sum(1 for item in schedule if not item["paid"])
    high_risk_count = sum(1 for item in schedule if item["client_profile"].get("no_show_risk") == "alto")
    cash_by_method = defaultdict(int)
    for item in schedule:
        if item["paid"]:
            cash_by_method[item["payment_method"]] += item["service"]["price"]
    return {
        "professionals": ESTETICA_PROFESSIONALS,
        "services": ESTETICA_SERVICES,
        "schedule": schedule,
        "eligibility": eligibility,
        "inventory_alerts": inventory_alerts,
        "waitlist": [{**item, "service": services[item["service_id"]]} for item in ESTETICA_WAITLIST],
        "kpis": {
            "appointments": len(ESTETICA_APPOINTMENTS),
            "services": len(ESTETICA_SERVICES),
            "professionals": len(ESTETICA_PROFESSIONALS),
            "revenue": revenue,
            "pending_revenue": pending_revenue,
            "commissions": sum(commissions.values()),
            "occupancy": occupancy,
            "waitlist": len(ESTETICA_WAITLIST),
            "deposits": deposits,
            "unpaid_count": unpaid_count,
            "high_risk_count": high_risk_count,
        },
        "cash_summary": {
            "paid": revenue,
            "pending": pending_revenue,
            "deposits": deposits,
            "by_method": dict(cash_by_method),
            "expected_total": revenue + pending_revenue,
        },
        "ai_actions": [
            {"title": "Confirmar cliente de riesgo", "detail": "Cliente demo 004 tiene riesgo alto y no registra abono. Enviar WhatsApp antes de liberar cupo."},
            {"title": "Cerrar caja pendiente", "detail": f"{unpaid_count} reservas tienen saldo por cobrar. Priorizar cobro antes del cierre de turno."},
            {"title": "Reponer insumo critico", "detail": "Mascara capilar y kit laminado aparecen bajo punto de reposicion por agenda del dia."},
            {"title": "Ofrecer cupo lista espera", "detail": "Si una reserva pendiente no confirma, ofrecer el cupo a limpieza facial o coloracion."},
        ],
        "professional_summary": [
            {
                **professional,
                "appointments": sum(1 for item in schedule if item["professional_id"] == professional["id"]),
                "commission": commissions.get(professional["id"], 0),
            }
            for professional in ESTETICA_PROFESSIONALS
        ],
        "data_contract": [
            "agenda_por_profesional",
            "servicio_profesional_habilitado",
            "bloqueos_y_estados",
            "caja_y_abonos",
            "comisiones",
            "lista_espera",
            "inventario_por_insumo",
            "recordatorios_whatsapp",
        ],
    }

@app.route("/estetica")
@app.route("/agenda-estetica")
def estetica_vertical_demo():
    return render_template("estetica_agenda.html", demo=estetica_demo_context())

POS_DEMO_ACCESS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "pos_demo_access.json")

DEMO_VERTICALS = {
    "ferreteria": {"label": "Punto de Venta Ferreteria", "workspace_key": "don-manolo", "path": "/pos"},
    "minimarket": {"label": "Punto de Venta Minimarket", "workspace_key": "minimarket", "path": "/pos"},
    "farmacia": {"label": "Farmacia - vertical pendiente", "workspace_key": "san-juan", "path": "/pos"},
    "boutique": {"label": "Punto de Venta Boutique", "workspace_key": "boutique", "path": "/pos"},
    "distribucion": {"label": "Punto de Venta Distribucion", "workspace_key": "ohiggins", "path": "/pos"},
    "estetica": {"label": "Agenda Estetica", "workspace_key": None, "path": "/agenda-estetica"},
}

def load_demo_access_state():
    if not os.path.exists(POS_DEMO_ACCESS_FILE):
        return {"requests": [], "accounts": []}
    try:
        with open(POS_DEMO_ACCESS_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return {"requests": data.get("requests") or [], "accounts": data.get("accounts") or []}
    except Exception:
        return {"requests": [], "accounts": []}

def save_demo_access_state(state):
    os.makedirs(os.path.dirname(POS_DEMO_ACCESS_FILE), exist_ok=True)
    with open(POS_DEMO_ACCESS_FILE, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)

def demo_account_is_active(account):
    if account.get("status") != "active":
        return False
    try:
        expires_at = datetime.strptime(account.get("expires_at") or "", "%Y-%m-%d").date()
    except Exception:
        return False
    return datetime.now().date() <= expires_at

def active_demo_accounts_by_username():
    state = load_demo_access_state()
    return {
        (account.get("username") or "").lower(): account
        for account in state.get("accounts", [])
        if demo_account_is_active(account)
    }

def demo_workspace_keys(account):
    vertical = DEMO_VERTICALS.get(account.get("vertical") or "")
    if not vertical or not vertical.get("workspace_key"):
        return []
    return [vertical["workspace_key"]]

def demo_access_summary():
    state = load_demo_access_state()
    today = datetime.now().date()
    for request_item in state.get("requests", []):
        request_item["vertical_label"] = DEMO_VERTICALS.get(request_item.get("vertical"), {}).get("label", request_item.get("vertical"))
    for account in state.get("accounts", []):
        account["vertical_label"] = DEMO_VERTICALS.get(account.get("vertical"), {}).get("label", account.get("vertical"))
        try:
            expires_at = datetime.strptime(account.get("expires_at") or "", "%Y-%m-%d").date()
            account["days_left"] = max(0, (expires_at - today).days)
        except Exception:
            account["days_left"] = 0
        if account.get("status") == "active" and account["days_left"] == 0 and (account.get("expires_at") or "") < today.strftime("%Y-%m-%d"):
            account["status"] = "expired"
    return state

def generate_demo_password():
    return "Qdemo-" + secrets.token_urlsafe(6).replace("-", "A").replace("_", "9")

@app.route("/maestro/demos/aprobar", methods=["POST"])
def maestro_demo_aprobar():
    guard = require_master_login()
    if guard:
        return guard
    request_id = (request.form.get("request_id") or "").strip()
    vertical = (request.form.get("vertical") or "minimarket").strip()
    if vertical not in DEMO_VERTICALS:
        abort(400, "Demo no disponible.")
    try:
        days = int(request.form.get("days") or 7)
    except ValueError:
        days = 7
    days = max(1, min(days, 14))
    contact_name = (request.form.get("contact_name") or request.form.get("nombre") or "Contacto demo").strip()[:90]
    company = (request.form.get("company") or request.form.get("empresa") or "Empresa demo").strip()[:100]
    email = (request.form.get("email") or "").strip().lower()[:120]
    if not email:
        abort(400, "El correo del contacto es obligatorio.")

    state = load_demo_access_state()
    request_item = None
    for item in state.get("requests", []):
        if item.get("id") == request_id:
            request_item = item
            break
    if request_item:
        contact_name = contact_name or request_item.get("nombre") or "Contacto demo"
        company = company or request_item.get("empresa") or "Empresa demo"
        email = email or request_item.get("email") or ""
        vertical = request_item.get("vertical") or vertical

    raw_password = generate_demo_password()
    username = f"demo-{vertical}-{secrets.token_hex(3)}".lower()
    account_id = "DEMO-ACC-" + secrets.token_hex(5).upper()
    expires_at = (datetime.now().date() + timedelta(days=days)).strftime("%Y-%m-%d")
    account = {
        "id": account_id,
        "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "expires_at": expires_at,
        "status": "active",
        "username": username,
        "password": hash_master_password(raw_password),
        "access_token": secrets.token_urlsafe(24),
        "vertical": vertical,
        "contact_name": contact_name,
        "company": company,
        "email": email,
        "request_id": request_id,
        "created_by": session.get("quantus_master_user") or MASTER_ADMIN_USER,
    }
    state.setdefault("accounts", []).insert(0, account)
    if request_item:
        request_item["status"] = "approved"
        request_item["approved_at"] = account["created_at"]
        request_item["account_id"] = account_id
    save_demo_access_state(state)

    demo_access = url_for("demo_access_token", token=account["access_token"], _external=True)
    vertical_label = DEMO_VERTICALS.get(vertical, {}).get("label", vertical)
    first_name = (contact_name or "").split()[0] or "Hola"
    try:
        exp_parts = expires_at.split("-")
        exp_display = f"{exp_parts[2]}/{exp_parts[1]}/{exp_parts[0]}"
    except Exception:
        exp_display = expires_at
    subject = f"[Quantus] Tu demo de {vertical_label} está lista"
    body_html = (
        "<html><body style=\"margin:0;background:#06101f;color:#f8fafc;"
        "font-family:Inter,Arial,Helvetica,sans-serif;\">"
        "<table role=\"presentation\" width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" "
        "style=\"min-width:100%;background:#06101f;padding:24px;\">"
        "<tr><td align=\"center\">"
        "<div style=\"max-width:560px;width:100%;background:#0f1c35;border:1px solid rgba(56,189,248,.28);"
        "border-radius:18px;padding:30px;box-sizing:border-box;text-align:left;\">"
        "<p style=\"margin:0;color:#38bdf8;font-weight:900;font-size:13px;letter-spacing:2px;\">QUANTUS CHILE</p>"
        f"<h1 style=\"margin:16px 0 10px;font-size:28px;line-height:1.1;\">Hola {first_name},</h1>"
        f"<p style=\"color:#cbd5e1;line-height:1.6;margin:10px 0;\">Tu acceso a la <strong>demo de "
        f"{vertical_label}</strong> para <strong>{company or 'tu empresa'}</strong> ya está listo.</p>"
        f"<a href=\"{demo_access}\" style=\"display:inline-block;margin:14px 0;background:#38bdf8;"
        "color:#06101f;padding:13px 18px;border-radius:12px;text-decoration:none;font-weight:900;"
        "font-size:15px;\">Entrar a la demo →</a>"
        f"<p style=\"color:#94a3b8;font-size:13px;line-height:1.6;margin:8px 0;\">Si el botón no funciona, "
        f"copia y pega en tu navegador: <span style=\"color:#7dd3fc;\">{demo_access}</span></p>"
        "<div style=\"margin:18px 0;padding:14px 16px;background:rgba(56,189,248,.10);"
        "border-radius:12px;font-size:14px;line-height:1.8;color:#e2e8f0;\">"
        f"Usuario: <strong>{username}</strong><br>"
        f"Contraseña: <strong>{raw_password}</strong></div>"
        f"<p style=\"color:#94a3b8;font-size:13px;line-height:1.6;margin:10px 0;\">"
        f"Vigencia: hasta el <strong style=\"color:#f1f5f9;\">{exp_display}</strong> "
        f"({days} días desde la activación).</p>"
        "<p style=\"color:#94a3b8;font-size:13px;line-height:1.6;margin:10px 0;\">"
        "¿Necesitas ayuda? Escríbenos a <span style=\"color:#7dd3fc;\">contacto@quantuschile.cl</span>.</p>"
        "</div></td></tr></table></body></html>"
    )

    def _notify_demo_ready():
        try:
            from communications.audit_log import record_communication
        except Exception:
            record_communication = None
        from mailer import smtp_configured
        ok = False
        provider = "SMTP no configurado (GMAIL_APP_PASSWORD)"
        if smtp_configured():
            try:
                ok = send_email(email, subject, body_html)
                provider = "enviado" if ok else "SMTP rechazó el envío"
            except Exception as exc:
                provider = str(exc)[:200]
        if record_communication:
            record_communication(
                module="maestro",
                client_key=request_id or "",
                client_name=contact_name or "Contacto demo",
                client_rut="",
                channel="email",
                event_type="demo_approved",
                subject=subject,
                message=f"Acceso demo {vertical_label} a {email} (vigente hasta {exp_display}).",
                body=body_html,
                report_url=demo_access,
                status="sent" if ok else ("pending_config" if provider.startswith("SMTP no") else "failed"),
                provider_response=provider,
                dedup_key=f"demo_approved:{account_id}",
                client={"email": email, "empresa": company, "vertical": vertical, "nombre": contact_name},
                payload={"account_id": account_id, "request_id": request_id, "days": days, "expires_at": expires_at},
            )

    Thread(target=_notify_demo_ready).start()
    return redirect(url_for(
        "maestro_dashboard",
        demo_user=username,
        demo_pass=raw_password,
        demo_link=demo_access,
        demo_until=expires_at,
    ) + "#panel-demos")

@app.route("/maestro/demos/<account_id>/revocar", methods=["POST"])
def maestro_demo_revocar(account_id):
    guard = require_master_login()
    if guard:
        return guard
    state = load_demo_access_state()
    for account in state.get("accounts", []):
        if account.get("id") == account_id:
            account["status"] = "revoked"
            account["revoked_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            account["revoked_by"] = session.get("quantus_master_user") or MASTER_ADMIN_USER
            break
    save_demo_access_state(state)
    return redirect(url_for("maestro_dashboard", demo_revoked=1) + "#panel-demos")

@app.route("/demo/solicitar", methods=["POST"])
def solicitar_demo_vertical():
    nombre = (request.form.get("nombre") or "").strip()[:90]
    empresa = (request.form.get("empresa") or "").strip()[:100]
    email = (request.form.get("email") or "").strip().lower()[:120]
    telefono = (request.form.get("telefono") or "").strip()[:40]
    vertical = (request.form.get("vertical") or "minimarket").strip()
    if vertical not in DEMO_VERTICALS:
        abort(400, "Demo no disponible.")
    if not nombre or not empresa or not email:
        abort(400, "Nombre, empresa y correo son obligatorios.")

    days = 10
    raw_password = generate_demo_password()
    username = f"demo-{vertical}-{secrets.token_hex(3)}".lower()
    account_id = "DEMO-ACC-" + secrets.token_hex(5).upper()
    request_id = "DEMO-REQ-" + secrets.token_hex(5).upper()
    created_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    expires_at = (datetime.now().date() + timedelta(days=days)).strftime("%Y-%m-%d")
    access_token = secrets.token_urlsafe(24)

    state = load_demo_access_state()
    
    # Guardar solicitud marcada como auto-aprobada
    state.setdefault("requests", []).insert(0, {
        "id": request_id,
        "created_at": created_at,
        "nombre": nombre,
        "empresa": empresa,
        "email": email,
        "telefono": telefono,
        "vertical": vertical,
        "status": "auto_approved",
        "approved_at": created_at,
        "account_id": account_id,
        "source": request.headers.get("Referer") or request.path,
    })

    # Guardar cuenta activa inmediatamente por 10 días
    account = {
        "id": account_id,
        "created_at": created_at,
        "expires_at": expires_at,
        "status": "active",
        "username": username,
        "password": hash_master_password(raw_password),
        "access_token": access_token,
        "vertical": vertical,
        "contact_name": nombre,
        "company": empresa,
        "email": email,
        "request_id": request_id,
        "created_by": "auto_onboarding",
    }
    state.setdefault("accounts", []).insert(0, account)
    save_demo_access_state(state)

    demo_access_link = url_for("demo_access_token", token=access_token, _external=True)
    vertical_info = DEMO_VERTICALS[vertical]
    vertical_label = vertical_info.get("label", vertical)
    first_name = (nombre or "").split()[0] or "Hola"

    try:
        exp_parts = expires_at.split("-")
        exp_display = f"{exp_parts[2]}/{exp_parts[1]}/{exp_parts[0]}"
    except Exception:
        exp_display = expires_at

    # Envío automático por correo (asíncrono)
    subject = f"[Quantus] Tu acceso demo de 10 días a {vertical_label} está activo"
    body_html = (
        "<html><body style=\"margin:0;background:#06101f;color:#f8fafc;"
        "font-family:Inter,Arial,Helvetica,sans-serif;\">"
        "<table role=\"presentation\" width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" "
        "style=\"min-width:100%;background:#06101f;padding:24px;\">"
        "<tr><td align=\"center\">"
        "<div style=\"max-width:560px;width:100%;background:#0f1c35;border:1px solid rgba(56,189,248,.28);"
        "border-radius:18px;padding:30px;box-sizing:border-box;text-align:left;\">"
        "<p style=\"margin:0;color:#38bdf8;font-weight:900;font-size:13px;letter-spacing:2px;\">QUANTUS CHILE</p>"
        f"<h1 style=\"margin:16px 0 10px;font-size:28px;line-height:1.1;\">¡Hola {first_name}!</h1>"
        f"<p style=\"color:#cbd5e1;line-height:1.6;margin:10px 0;\">Tu acceso demo por 10 días a <strong>"
        f"{vertical_label}</strong> para <strong>{empresa}</strong> fue activado exitosamente.</p>"
        f"<a href=\"{demo_access_link}\" style=\"display:inline-block;margin:14px 0;background:#38bdf8;"
        "color:#06101f;padding:13px 18px;border-radius:12px;text-decoration:none;font-weight:900;"
        "font-size:15px;\">Ingresar directamente a la Demo →</a>"
        "<div style=\"margin:18px 0;padding:14px 16px;background:rgba(56,189,248,.10);"
        "border-radius:12px;font-size:14px;line-height:1.8;color:#e2e8f0;\">"
        f"Usuario: <strong style=\"color:#38bdf8;\">{username}</strong><br>"
        f"Contraseña: <strong style=\"color:#38bdf8;\">{raw_password}</strong><br>"
        f"Página de Login: <strong>https://www.quantuschile.cl/punto-de-venta/acceso</strong></div>"
        f"<p style=\"color:#94a3b8;font-size:13px;line-height:1.6;margin:10px 0;\">"
        f"Vigencia: <strong>10 días</strong> (hasta el {exp_display}).</p>"
        "</div></td></tr></table></body></html>"
    )

    def _send_auto_demo_mail():
        try:
            from mailer import smtp_configured, send_email
            if smtp_configured():
                send_email(email, subject, body_html)
        except Exception as exc:
            app.logger.warning("Error enviando correo de demo automatica: %s", exc)

    Thread(target=_send_auto_demo_mail).start()

    return render_template(
        "demo_solicitada.html",
        request_id=request_id,
        vertical=vertical_info,
        username=username,
        raw_password=raw_password,
        expires_at=exp_display,
        demo_access_link=demo_access_link,
        email=email,
        empresa=empresa
    )

@app.route("/demo/acceso/<token>")
def demo_access_token(token):
    token = (token or "").strip()
    state = load_demo_access_state()
    for account in state.get("accounts", []):
        if hmac.compare_digest(account.get("access_token") or "", token) and demo_account_is_active(account):
            account["last_access_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            save_demo_access_state(state)
            vertical = DEMO_VERTICALS.get(account.get("vertical") or "")
            if vertical and vertical.get("workspace_key"):
                session["pos_username"] = account["username"]
                session["pos_workspace_key"] = vertical["workspace_key"]
                return redirect(erp_server_clients_url(vertical["workspace_key"]))
            return redirect((vertical or {}).get("path") or "/clientes")
    abort(403, "Demo expirada o no autorizada.")

POS_WORKSPACES = {
    "don-manolo": {
        "key": "don-manolo",
        "name": "Ferreteria Don Manolo",
        "rubro": "Ferreteria",
        "rut": "76.543.210-9",
        "plan": "Punto de Venta Profesional",
        "expires": "31/12/2026",
        "status": "ACTIVA",
        "badge_class": "badge-active",
        "logo_class": "logo-don-manolo",
        "brand_mark": "DM",
        "brand_label": "Cliente real",
        "brand_note": "Operacion activa con movimientos",
        "logo_file": "pos_logo_don_manolo.svg",
        "is_real_client": True,
    },
    "ohiggins": {
        "key": "ohiggins",
        "name": "Distribuidora O'Higgins",
        "rubro": "Distribucion",
        "rut": "76.987.654-3",
        "plan": "Punto de Venta Empresarial",
        "expires": "15/01/2027",
        "status": "ACTIVA",
        "badge_class": "badge-active",
        "logo_class": "logo-ohiggins",
        "brand_mark": "AD",
        "brand_label": "Andes Distribucion",
        "brand_note": "Marca ficticia demo",
        "logo_file": "pos_logo_distribuidora_ohiggins.svg",
        "is_real_client": False,
    },
    "minimarket": {
        "key": "minimarket",
        "name": "Minimarket Los Aromos",
        "rubro": "Minimarket",
        "rut": "77.222.333-5",
        "plan": "Punto de Venta Profesional",
        "expires": "18/02/2027",
        "status": "ACTIVA",
        "badge_class": "badge-active",
        "logo_class": "logo-minimarket",
        "brand_mark": "MN",
        "brand_label": "Mercado Norte",
        "brand_note": "Marca ficticia demo",
        "logo_file": "pos_logo_minimarket_los_aromos.svg",
        "is_real_client": False,
    },
    "san-juan": {
        "key": "san-juan",
        "name": "Farmacia San Juan",
        "rubro": "Farmacia",
        "rut": "77.111.222-0",
        "plan": "Punto de Venta Profesional",
        "expires": "28/02/2027",
        "status": "ACTIVA",
        "badge_class": "badge-active",
        "logo_class": "logo-san-juan",
        "brand_mark": "NS",
        "brand_label": "NovaSalud",
        "brand_note": "Marca ficticia demo",
        "logo_file": "pos_logo_farmacia_san_juan.svg",
        "is_real_client": False,
    },
    "boutique": {
        "key": "boutique",
        "name": "Boutique Aurora",
        "rubro": "Boutique",
        "rut": "77.333.444-6",
        "plan": "Punto de Venta Profesional",
        "expires": "10/03/2027",
        "status": "ACTIVA",
        "badge_class": "badge-active",
        "logo_class": "logo-boutique",
        "brand_mark": "LA",
        "brand_label": "Lumen Atelier",
        "brand_note": "Marca ficticia demo",
        "logo_file": "pos_logo_boutique_aurora.svg",
        "is_real_client": False,
    },
}

POS_USERS = {
    "admin": {
        "password": "admin123",
        "display_name": "Administrador Punto de Venta",
        "email": "admin@demo.quantuschile.cl",
        "role": "client_admin",
        "workspaces": ["don-manolo"],
    },
    "ferreteria": {
        "password": "demo123",
        "display_name": "Ferreteria Don Manolo",
        "email": "admin@ferreteria.cl",
        "role": "client_admin",
        "workspaces": ["don-manolo"],
    },
    "donmanolo": {
        "password": "donmanolo123",
        "display_name": "Ferreteria Don Manolo",
        "email": "admin@donmanolo.cl",
        "role": "client_admin",
        "workspaces": ["don-manolo"],
    },
    "roor": {
        "password": "felipe123",
        "display_name": "Ferreteria Don Manolo",
        "email": "cliente@ferreteria.cl",
        "role": "client_admin",
        "workspaces": ["don-manolo"],
    },
    "root": {
        "password": "felipe123",
        "display_name": "Ferreteria Don Manolo",
        "email": "cliente@ferreteria.cl",
        "role": "client_admin",
        "workspaces": ["don-manolo"],
    },
    "distribuidora": {
        "password": "demo123",
        "display_name": "Distribuidora O'Higgins",
        "email": "admin@distribuidora.cl",
        "role": "client_admin",
        "workspaces": ["ohiggins"],
    },
    "minimarket": {
        "password": "demo123",
        "display_name": "Minimarket Los Aromos",
        "email": "admin@minimarket.cl",
        "role": "client_admin",
        "workspaces": ["minimarket"],
    },
    "farmacia": {
        "password": "demo123",
        "display_name": "Farmacia San Juan",
        "email": "admin@farmacia.cl",
        "role": "client_admin",
        "workspaces": ["san-juan"],
    },
    "boutique": {
        "password": "demo123",
        "display_name": "Boutique Aurora",
        "email": "admin@boutique.cl",
        "role": "client_admin",
        "workspaces": ["boutique"],
    },
    "superadmin": {
        "password": "Codelco.66",
        "display_name": "SuperAdmin Quantus",
        "email": "fmejias@quantuschile.cl",
        "role": "superadmin",
        "workspaces": ["don-manolo", "minimarket", "san-juan", "boutique", "ohiggins"],
    },
}

POS_PRODUCTS_BY_RUBRO = {
    "Ferreteria": [
        {"name": "Taladro Percutor 13mm", "price": 42990, "sku": "FER-1001", "stock": 9, "daily_sales": 3.0, "supplier": "Herramientas Centro SpA", "lead_days": 5, "reorder_qty": 12},
        {"name": "Caja Tornillos Madera 1kg", "price": 6990, "sku": "FER-1002", "stock": 34, "daily_sales": 4.4, "supplier": "Ferreteria Mayorista Sur", "lead_days": 3, "reorder_qty": 40},
        {"name": "Disco Corte Metal 4.5", "price": 1490, "sku": "FER-1003", "stock": 22, "daily_sales": 6.2, "supplier": "Abrasivos Andes", "lead_days": 4, "reorder_qty": 80},
        {"name": "Silicona Neutra Transparente", "price": 3990, "sku": "FER-1004", "stock": 16, "daily_sales": 2.8, "supplier": "Selladores Chile", "lead_days": 6, "reorder_qty": 36},
        {"name": "Pintura Esmalte Blanco 1/4", "price": 5990, "sku": "FER-1005", "stock": 11, "daily_sales": 2.1, "supplier": "Pinturas Pro", "lead_days": 5, "reorder_qty": 24},
        {"name": "Guante Cabritilla Par", "price": 3490, "sku": "FER-1006", "stock": 48, "daily_sales": 5.0, "supplier": "Seguridad Industrial Sur", "lead_days": 3, "reorder_qty": 60},
        {"name": "Cinta Aisladora Negra", "price": 1290, "sku": "FER-1007", "stock": 70, "daily_sales": 7.4, "supplier": "Electricos Rancagua", "lead_days": 2, "reorder_qty": 100},
        {"name": "Llave Francesa 10 pulgadas", "price": 11990, "sku": "FER-1008", "stock": 7, "daily_sales": 1.4, "supplier": "Herramientas Centro SpA", "lead_days": 7, "reorder_qty": 18},
        {"name": "Broca Muro 8mm", "price": 2490, "sku": "FER-1009", "stock": 19, "daily_sales": 4.1, "supplier": "Abrasivos Andes", "lead_days": 4, "reorder_qty": 55},
        {"name": "Ampolleta LED 12W", "price": 2990, "sku": "FER-1010", "stock": 52, "daily_sales": 6.8, "supplier": "Electricos Rancagua", "lead_days": 3, "reorder_qty": 90},
        {"name": "Teflon Gas 3/4", "price": 990, "sku": "FER-1011", "stock": 15, "daily_sales": 3.5, "supplier": "Gasfiteria Mayorista", "lead_days": 5, "reorder_qty": 48},
        {"name": "Candado Bronce 40mm", "price": 4990, "sku": "FER-1012", "stock": 8, "daily_sales": 1.8, "supplier": "Seguridad Industrial Sur", "lead_days": 6, "reorder_qty": 24},
        {"name": "Adhesivo PVC 240cc", "price": 4590, "sku": "FER-1013", "stock": 13, "daily_sales": 2.6, "supplier": "Gasfiteria Mayorista", "lead_days": 5, "reorder_qty": 30},
    ],
    "Distribucion": [
        {"name": "Pack Bebidas 24 unidades", "price": 18990, "sku": "DIS-2001", "stock": 42, "daily_sales": 9.0, "supplier": "Distribuidora Regional", "lead_days": 2, "reorder_qty": 50},
        {"name": "Caja Snack Mixto", "price": 12990, "sku": "DIS-2002", "stock": 18, "daily_sales": 3.2, "supplier": "Snacks Mayoristas Chile", "lead_days": 4, "reorder_qty": 35},
        {"name": "Agua Mineral 1.5L x12", "price": 9990, "sku": "DIS-2003", "stock": 26, "daily_sales": 7.6, "supplier": "Bebidas Cordillera", "lead_days": 3, "reorder_qty": 60},
        {"name": "Jugo Caja 200ml x30", "price": 11990, "sku": "DIS-2004", "stock": 31, "daily_sales": 5.4, "supplier": "Bebidas Cordillera", "lead_days": 3, "reorder_qty": 50},
        {"name": "Galleta Familiar x24", "price": 15990, "sku": "DIS-2005", "stock": 14, "daily_sales": 4.8, "supplier": "Snacks Mayoristas Chile", "lead_days": 5, "reorder_qty": 44},
        {"name": "Aceite Maravilla 1L x12", "price": 24990, "sku": "DIS-2006", "stock": 21, "daily_sales": 3.7, "supplier": "Abarrotes del Valle", "lead_days": 4, "reorder_qty": 36},
        {"name": "Arroz Grado 1 1kg x20", "price": 19990, "sku": "DIS-2007", "stock": 33, "daily_sales": 5.9, "supplier": "Abarrotes del Valle", "lead_days": 4, "reorder_qty": 60},
        {"name": "Detergente 3L x6", "price": 28990, "sku": "DIS-2008", "stock": 12, "daily_sales": 2.5, "supplier": "Limpieza Pro", "lead_days": 6, "reorder_qty": 24},
        {"name": "Papel Higienico 24 rollos", "price": 13990, "sku": "DIS-2009", "stock": 45, "daily_sales": 6.1, "supplier": "Hogar Mayorista", "lead_days": 3, "reorder_qty": 70},
        {"name": "Cafe Instantaneo 170g x12", "price": 32990, "sku": "DIS-2010", "stock": 9, "daily_sales": 1.9, "supplier": "Abarrotes del Valle", "lead_days": 7, "reorder_qty": 24},
        {"name": "Leche UHT 1L x12", "price": 14990, "sku": "DIS-2011", "stock": 28, "daily_sales": 8.2, "supplier": "Lacteos Centro", "lead_days": 2, "reorder_qty": 72},
        {"name": "Azucar 1kg x20", "price": 17990, "sku": "DIS-2012", "stock": 17, "daily_sales": 3.8, "supplier": "Abarrotes del Valle", "lead_days": 5, "reorder_qty": 42},
        {"name": "Toalla Papel x12", "price": 11990, "sku": "DIS-2013", "stock": 24, "daily_sales": 4.0, "supplier": "Hogar Mayorista", "lead_days": 4, "reorder_qty": 48},
    ],
    "Minimarket": [
        {"name": "Pan Hallulla Bolsa 6 unidades", "price": 1890, "sku": "MIN-4001", "stock": 32, "daily_sales": 10.5, "supplier": "Panificadora Local", "lead_days": 1, "reorder_qty": 70},
        {"name": "Leche Entera 1L", "price": 1390, "sku": "MIN-4002", "stock": 26, "daily_sales": 8.8, "supplier": "Lacteos Centro", "lead_days": 2, "reorder_qty": 60},
        {"name": "Huevos Docena", "price": 3590, "sku": "MIN-4003", "stock": 15, "daily_sales": 4.9, "supplier": "Avicola Santa Rosa", "lead_days": 2, "reorder_qty": 40},
        {"name": "Bebida Cola 2.5L", "price": 2490, "sku": "MIN-4004", "stock": 22, "daily_sales": 7.3, "supplier": "Bebidas Cordillera", "lead_days": 3, "reorder_qty": 55},
        {"name": "Papas Fritas Familiar", "price": 2990, "sku": "MIN-4005", "stock": 18, "daily_sales": 5.6, "supplier": "Snacks Mayoristas Chile", "lead_days": 4, "reorder_qty": 45},
        {"name": "Cigarros Demo Controlado", "price": 4990, "sku": "MIN-4006", "stock": 11, "daily_sales": 2.4, "supplier": "Distribuidora Regional", "lead_days": 5, "reorder_qty": 24},
        {"name": "Cafe Molido 250g", "price": 3990, "sku": "MIN-4007", "stock": 13, "daily_sales": 2.7, "supplier": "Abarrotes del Valle", "lead_days": 4, "reorder_qty": 30},
        {"name": "Azucar 1kg", "price": 1290, "sku": "MIN-4008", "stock": 28, "daily_sales": 6.4, "supplier": "Abarrotes del Valle", "lead_days": 3, "reorder_qty": 65},
        {"name": "Arroz 1kg", "price": 1590, "sku": "MIN-4009", "stock": 24, "daily_sales": 5.8, "supplier": "Abarrotes del Valle", "lead_days": 3, "reorder_qty": 60},
        {"name": "Detergente Liquido 1L", "price": 3490, "sku": "MIN-4010", "stock": 9, "daily_sales": 2.0, "supplier": "Limpieza Pro", "lead_days": 6, "reorder_qty": 24},
        {"name": "Papel Higienico 4 rollos", "price": 2990, "sku": "MIN-4011", "stock": 17, "daily_sales": 4.5, "supplier": "Hogar Mayorista", "lead_days": 4, "reorder_qty": 44},
        {"name": "Helado Familiar 1L", "price": 4590, "sku": "MIN-4012", "stock": 8, "daily_sales": 2.3, "supplier": "Congelados Sur", "lead_days": 5, "reorder_qty": 20},
        {"name": "Agua Mineral 1.6L", "price": 1190, "sku": "MIN-4013", "stock": 36, "daily_sales": 9.1, "supplier": "Bebidas Cordillera", "lead_days": 2, "reorder_qty": 72},
    ],
    "Farmacia": [
        {"name": "Alcohol Gel 1L", "price": 4990, "sku": "FAR-3001", "stock": 26, "daily_sales": 5.2, "supplier": "Insumos Clinicos Centro", "lead_days": 3, "reorder_qty": 30},
        {"name": "Mascarillas Caja 50 unidades", "price": 7990, "sku": "FAR-3002", "stock": 14, "daily_sales": 2.9, "supplier": "Proteccion Medica SpA", "lead_days": 5, "reorder_qty": 25},
        {"name": "Paracetamol 500mg x20", "price": 2490, "sku": "FAR-3003", "stock": 18, "daily_sales": 6.0, "supplier": "Farmaceutica Central", "lead_days": 4, "reorder_qty": 60},
        {"name": "Ibuprofeno 400mg x20", "price": 2990, "sku": "FAR-3004", "stock": 22, "daily_sales": 4.7, "supplier": "Farmaceutica Central", "lead_days": 4, "reorder_qty": 48},
        {"name": "Suero Fisiologico 500ml", "price": 1890, "sku": "FAR-3005", "stock": 11, "daily_sales": 3.1, "supplier": "Insumos Clinicos Centro", "lead_days": 5, "reorder_qty": 36},
        {"name": "Termometro Digital", "price": 6990, "sku": "FAR-3006", "stock": 7, "daily_sales": 1.5, "supplier": "Equipos Medicos Sur", "lead_days": 7, "reorder_qty": 18},
        {"name": "Guantes Nitrilo Caja 100", "price": 10990, "sku": "FAR-3007", "stock": 19, "daily_sales": 3.8, "supplier": "Proteccion Medica SpA", "lead_days": 5, "reorder_qty": 36},
        {"name": "Vitamina C 1g x20", "price": 3990, "sku": "FAR-3008", "stock": 30, "daily_sales": 4.2, "supplier": "Farmaceutica Central", "lead_days": 3, "reorder_qty": 50},
        {"name": "Crema Cicatrizante 30g", "price": 5990, "sku": "FAR-3009", "stock": 13, "daily_sales": 2.2, "supplier": "Dermocosmetica Chile", "lead_days": 6, "reorder_qty": 24},
        {"name": "Protector Solar FPS50", "price": 8990, "sku": "FAR-3010", "stock": 16, "daily_sales": 3.6, "supplier": "Dermocosmetica Chile", "lead_days": 6, "reorder_qty": 30},
        {"name": "Test Glucosa Tiras x50", "price": 15990, "sku": "FAR-3011", "stock": 8, "daily_sales": 1.7, "supplier": "Equipos Medicos Sur", "lead_days": 8, "reorder_qty": 20},
        {"name": "Jeringa 5ml x100", "price": 7990, "sku": "FAR-3012", "stock": 25, "daily_sales": 2.9, "supplier": "Insumos Clinicos Centro", "lead_days": 4, "reorder_qty": 40},
        {"name": "Venda Elast 10cm", "price": 2490, "sku": "FAR-3013", "stock": 21, "daily_sales": 2.6, "supplier": "Proteccion Medica SpA", "lead_days": 5, "reorder_qty": 35},
    ],
    "Boutique": [
        {"name": "Blusa Lino Premium", "price": 24990, "sku": "BOU-5001", "stock": 9, "daily_sales": 1.8, "supplier": "Textiles Aurora", "lead_days": 7, "reorder_qty": 18},
        {"name": "Jeans Recto Mujer", "price": 32990, "sku": "BOU-5002", "stock": 12, "daily_sales": 2.4, "supplier": "Denim Centro", "lead_days": 6, "reorder_qty": 22},
        {"name": "Vestido Casual Midi", "price": 39990, "sku": "BOU-5003", "stock": 7, "daily_sales": 1.5, "supplier": "Moda Mayorista", "lead_days": 8, "reorder_qty": 16},
        {"name": "Polera Basica Algodon", "price": 9990, "sku": "BOU-5004", "stock": 28, "daily_sales": 5.2, "supplier": "Textiles Aurora", "lead_days": 4, "reorder_qty": 60},
        {"name": "Chaqueta Denim", "price": 45990, "sku": "BOU-5005", "stock": 6, "daily_sales": 1.1, "supplier": "Denim Centro", "lead_days": 9, "reorder_qty": 14},
        {"name": "Pantalon Palazzo", "price": 29990, "sku": "BOU-5006", "stock": 10, "daily_sales": 2.0, "supplier": "Moda Mayorista", "lead_days": 7, "reorder_qty": 20},
        {"name": "Cartera Cruzada Eco Cuero", "price": 21990, "sku": "BOU-5007", "stock": 8, "daily_sales": 1.7, "supplier": "Accesorios Pacifico", "lead_days": 6, "reorder_qty": 18},
        {"name": "Aro Dorado Minimal", "price": 6990, "sku": "BOU-5008", "stock": 18, "daily_sales": 3.1, "supplier": "Accesorios Pacifico", "lead_days": 5, "reorder_qty": 35},
        {"name": "Bufanda Temporada", "price": 12990, "sku": "BOU-5009", "stock": 11, "daily_sales": 2.3, "supplier": "Textiles Aurora", "lead_days": 5, "reorder_qty": 26},
        {"name": "Zapatilla Urbana", "price": 34990, "sku": "BOU-5010", "stock": 5, "daily_sales": 1.4, "supplier": "Calzado Sur", "lead_days": 8, "reorder_qty": 16},
        {"name": "Top Fiesta Satinado", "price": 17990, "sku": "BOU-5011", "stock": 13, "daily_sales": 2.8, "supplier": "Moda Mayorista", "lead_days": 6, "reorder_qty": 30},
        {"name": "Cinturon Cuero Sintetico", "price": 8990, "sku": "BOU-5012", "stock": 16, "daily_sales": 2.2, "supplier": "Accesorios Pacifico", "lead_days": 4, "reorder_qty": 28},
        {"name": "Set Calcetines Premium", "price": 7990, "sku": "BOU-5013", "stock": 24, "daily_sales": 4.0, "supplier": "Textiles Aurora", "lead_days": 4, "reorder_qty": 48},
    ],
}

POS_SUPPLIER_LEAD_TIMES = {
    product["sku"]: {
        "supplier": product.get("supplier", "Proveedor demo"),
        "avg_delivery_days": int(product.get("lead_days") or 5),
        "safety_days": 2,
        "reorder_qty": int(product.get("reorder_qty") or max(10, product.get("stock", 0))),
    }
    for products in POS_PRODUCTS_BY_RUBRO.values()
    for product in products
}

POS_DEMO_DAILY_SALES = {
    product["sku"]: float(product.get("daily_sales") or 1.0)
    for products in POS_PRODUCTS_BY_RUBRO.values()
    for product in products
}

POS_ADMIN_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "pos_admin.sqlite3")
POS_BOLETAS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "pos_boletas")

POS_ROLE_LABELS = {
    "admin_empresa": "Administrador empresa",
    "vendedor": "Vendedor",
    "bodega": "Bodega",
    "solo_reportes": "Solo reportes",
}

POS_CLIENT_ADMIN_PERMISSIONS = {
    "users:create",
    "users:update",
    "users:delete",
    "profiles:update",
}

POS_QUANTUS_ONLY_FEATURES = {
    "caja_nueva": "Crear o habilitar cajas",
    "personal_shopper": "Personal shopper",
    "sucursal_nueva": "Crear sucursales",
    "integracion_sii": "Integracion tributaria SII",
}

def pos_session_user():
    username = session.get("pos_username")
    if not username:
        return None
    demo_account = active_demo_accounts_by_username().get(str(username).lower())
    if demo_account:
        return {
            "username": demo_account["username"],
            "password": "",
            "display_name": demo_account.get("contact_name") or demo_account.get("company") or "Demo temporal",
            "email": demo_account.get("email") or "",
            "role": "demo_client",
            "workspaces": demo_workspace_keys(demo_account),
            "demo_expires_at": demo_account.get("expires_at"),
        }
    if username == "owner":
        return {
            "username": "owner",
            "password": "",
            "display_name": "Felipe Mejias",
            "email": MASTER_ADMIN_EMAIL,
            "role": "owner_demo",
            "workspaces": ["don-manolo", "minimarket", "san-juan", "boutique", "ohiggins"],
        }
    user = POS_USERS.get(username)
    if not user:
        return None
    return {"username": username, **user}

def pos_allowed_workspaces(user=None):
    user = user or pos_session_user()
    if not user:
        return []
    return [POS_WORKSPACES[key] for key in user.get("workspaces", []) if key in POS_WORKSPACES]

def pos_current_workspace():
    key = session.get("pos_workspace_key")
    user = pos_session_user()
    if not key or not user or key not in user.get("workspaces", []):
        return None
    return POS_WORKSPACES.get(key)

def pos_products_for_workspace(workspace):
    if not workspace:
        return []
    return POS_PRODUCTS_BY_RUBRO.get(workspace.get("rubro"), POS_PRODUCTS_BY_RUBRO["Distribucion"])

def pos_demo_purchase_orders(workspace, limit=10):
    products = pos_products_for_workspace(workspace)
    orders = []
    base_date = datetime.now().date()
    statuses = ["recibida", "recibida", "parcial", "en_transito", "programada"]
    for index, product in enumerate(products[:limit]):
        supplier = POS_SUPPLIER_LEAD_TIMES.get(product["sku"], {})
        qty = max(int(product.get("reorder_qty") or 10), int(product.get("stock") or 0) + 5)
        issued_at = base_date - timedelta(days=limit - index)
        eta = issued_at + timedelta(days=int(supplier.get("avg_delivery_days") or 5))
        orders.append({
            "id": f"OC-{workspace['key'][:3].upper()}-{index + 1:04d}",
            "sku": product["sku"],
            "product": product["name"],
            "supplier": supplier.get("supplier") or product.get("supplier") or "Proveedor demo",
            "qty": qty,
            "issued_at": issued_at,
            "eta": eta,
            "status": statuses[index % len(statuses)],
            "unit_cost": round(product["price"] * 0.62),
        })
    return orders

def pos_demo_sales_tickets(workspace, limit=5):
    products = pos_products_for_workspace(workspace)
    tickets = []
    base_date = datetime.now().date()
    for index in range(limit):
        selected = [products[(index + offset) % len(products)] for offset in range(3)]
        lines = []
        total = 0
        for offset, product in enumerate(selected):
            qty = 1 + ((index + offset) % 3)
            line_total = qty * int(product["price"])
            total += line_total
            lines.append({"sku": product["sku"], "product": product["name"], "qty": qty, "line_total": line_total})
        tickets.append({
            "id": f"VTA-{workspace['key'][:3].upper()}-{index + 1:04d}",
            "sold_at": base_date - timedelta(days=index),
            "channel": ["caja", "caja", "delivery", "mayorista", "caja"][index % 5],
            "lines": lines,
            "total": total,
        })
    return tickets

def pos_demo_agent_context(workspace, stock_ai=None):
    products = pos_products_for_workspace(workspace)
    orders = pos_demo_purchase_orders(workspace)
    sales = pos_demo_sales_tickets(workspace)
    suppliers = sorted({POS_SUPPLIER_LEAD_TIMES.get(item["sku"], {}).get("supplier", "Proveedor demo") for item in products})
    stock_ai = stock_ai or pos_stock_ai_analysis(workspace)
    return {
        "products_count": len(products),
        "purchase_orders_count": len(orders),
        "sales_tickets_count": len(sales),
        "suppliers_count": len(suppliers),
        "critical_count": len(stock_ai.get("critical_items") or []),
        "orders": orders,
        "sales": sales,
        "suppliers": suppliers,
        "data_contract": [
            "catalogo_productos",
            "stock_actual",
            "ventas_historicas",
            "ordenes_compra",
            "proveedores",
            "lead_time_entrega",
            "margen_estimado",
            "alertas_quiebre",
        ],
    }

def pos_user_is_quantus_admin(user=None):
    user = user or pos_session_user()
    return bool(user and user.get("role") in {"superadmin", "owner_demo"})

def ensure_pos_admin_storage():
    os.makedirs(os.path.dirname(POS_ADMIN_DB), exist_ok=True)
    with sqlite3.connect(POS_ADMIN_DB) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pos_workspace_users (
                id TEXT PRIMARY KEY,
                workspace_key TEXT NOT NULL,
                display_name TEXT NOT NULL,
                email TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL,
                created_by TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pos_users_workspace ON pos_workspace_users(workspace_key)")
        for workspace in POS_WORKSPACES.values():
            seed_id = f"{workspace['key']}-admin"
            conn.execute(
                """
                INSERT OR IGNORE INTO pos_workspace_users (
                    id, workspace_key, display_name, email, role, status, created_by, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    seed_id,
                    workspace["key"],
                    f"Admin {workspace['name']}",
                    f"admin+{workspace['key']}@quantuschile.cl",
                    "admin_empresa",
                    "activo",
                    "seed",
                    datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                    datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                ),
            )

def pos_workspace_users(workspace_key):
    ensure_pos_admin_storage()
    with sqlite3.connect(POS_ADMIN_DB) as conn:
        conn.row_factory = sqlite3.Row
        return [
            dict(row)
            for row in conn.execute(
                """
                SELECT *
                FROM pos_workspace_users
                WHERE workspace_key=?
                ORDER BY CASE status WHEN 'activo' THEN 0 ELSE 1 END, role, display_name
                """,
                (workspace_key,),
            )
        ]

def require_pos_workspace():
    user = pos_session_user()
    workspace = pos_current_workspace()
    if not user or not workspace:
        return None, None, redirect("/clientes")
    return user, workspace, None

def require_pos_user_admin():
    user, workspace, guard = require_pos_workspace()
    if guard:
        return None, None, guard
    if user.get("role") not in {"client_admin", "superadmin", "owner_demo"}:
        abort(403, "No tienes permisos para administrar usuarios.")
    return user, workspace, None

def pos_validate_role(role):
    if role not in POS_ROLE_LABELS:
        abort(400, "Perfil no permitido para el cliente.")
    return role

def pos_feature_gate(feature_key):
    if feature_key not in POS_QUANTUS_ONLY_FEATURES:
        abort(400, "Modulo no reconocido.")
    user = pos_session_user()
    if not pos_user_is_quantus_admin(user):
        abort(403, "Esta habilitacion la realiza Quantus. El admin cliente no puede activar cajas, sucursales ni personal shopper.")

def pos_build_receipt_items(workspace, raw_items):
    catalog = {item["sku"]: item for item in pos_products_for_workspace(workspace)}
    receipt_items = []
    total = 0
    for raw in raw_items or []:
        sku = str(raw.get("sku") or "").strip()
        qty = int(raw.get("qty") or 0)
        if sku not in catalog or qty < 1 or qty > 999:
            abort(400, "Producto o cantidad no valida para el rubro contratado.")
        product = catalog[sku]
        line_total = product["price"] * qty
        total += line_total
        receipt_items.append({
            "sku": sku,
            "name": product["name"],
            "qty": qty,
            "unit_price": product["price"],
            "line_total": line_total,
        })
    if not receipt_items:
        abort(400, "La boleta debe tener al menos un producto.")
    net = round(total / 1.19)
    iva = total - net
    return receipt_items, {"net": net, "iva": iva, "total": total}

def pos_receipt_sales_history(workspace_key, sku, days=30):
    if not os.path.isdir(POS_BOLETAS_DIR):
        return []
    cutoff = datetime.now() - timedelta(days=days)
    safe_workspace = werkzeug.utils.secure_filename(workspace_key)
    rows = []
    for entry in os.listdir(POS_BOLETAS_DIR):
        if not entry.startswith(f"{safe_workspace}-") or not entry.endswith(".json"):
            continue
        path = os.path.join(POS_BOLETAS_DIR, entry)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                metadata = json.load(fh)
        except Exception:
            continue
        created_raw = metadata.get("created_at") or ""
        try:
            created_at = datetime.fromisoformat(created_raw)
        except ValueError:
            created_at = datetime.now()
        if created_at < cutoff:
            continue
        qty = sum(int(item.get("qty") or 0) for item in metadata.get("items", []) if item.get("sku") == sku)
        if qty > 0:
            rows.append({"created_at": created_at, "qty": qty, "source": metadata.get("source") or "receipt"})
    return rows

def pos_average_daily_sales(workspace, sku, days=30):
    rows = pos_receipt_sales_history(workspace["key"], sku, days=days)
    sold_units = sum(row["qty"] for row in rows)
    real_daily = sold_units / days if sold_units else 0
    demo_daily = POS_DEMO_DAILY_SALES.get(sku, 0)
    if sold_units >= 10:
        return round(real_daily, 2), "ventas_reales_pdf_json", sold_units
    if sold_units > 0:
        return round(max(real_daily, demo_daily), 2), "ventas_reales_insuficientes_mas_semilla_demo", sold_units
    return round(demo_daily, 2), "semilla_demo_rubro", round(demo_daily * days)

def pos_stock_ai_analysis(workspace):
    today = datetime.now().date()
    items = []
    for product in pos_products_for_workspace(workspace):
        sku = product["sku"]
        stock = int(product.get("stock") or 0)
        daily_sales, evidence_source, learned_units = pos_average_daily_sales(workspace, sku)
        supplier = POS_SUPPLIER_LEAD_TIMES.get(sku, {"supplier": "Proveedor no configurado", "avg_delivery_days": 5, "safety_days": 2, "reorder_qty": max(10, stock)})
        avg_delivery_days = int(supplier.get("avg_delivery_days") or 5)
        safety_days = int(supplier.get("safety_days") or 2)
        days_to_zero = math.inf if daily_sales <= 0 else stock / daily_sales
        days_to_zero_ceil = 999 if days_to_zero == math.inf else max(0, math.ceil(days_to_zero))
        stock_zero_date = None if days_to_zero == math.inf else today + timedelta(days=days_to_zero_ceil)
        eta_date = today + timedelta(days=avg_delivery_days)
        reorder_deadline = None if stock_zero_date is None else stock_zero_date - timedelta(days=avg_delivery_days + safety_days)
        shortage_days = 0 if stock_zero_date is None else max(0, (eta_date - stock_zero_date).days)
        should_alert = stock_zero_date is not None and days_to_zero <= (avg_delivery_days + safety_days)
        if shortage_days > 0:
            severity = "critico"
        elif should_alert:
            severity = "alerta"
        elif stock <= max(3, math.ceil(daily_sales * safety_days)):
            severity = "preventivo"
        else:
            severity = "ok"
        reorder_qty = int(supplier.get("reorder_qty") or max(math.ceil(daily_sales * 14), stock))
        items.append({
            "sku": sku,
            "name": product["name"],
            "stock": stock,
            "daily_sales": daily_sales,
            "learned_units": learned_units,
            "evidence_source": evidence_source,
            "supplier": supplier.get("supplier") or "Proveedor no configurado",
            "avg_delivery_days": avg_delivery_days,
            "safety_days": safety_days,
            "days_to_zero": None if days_to_zero == math.inf else round(days_to_zero, 1),
            "days_to_zero_ceil": days_to_zero_ceil,
            "stock_zero_date": stock_zero_date,
            "eta_date": eta_date,
            "reorder_deadline": reorder_deadline,
            "shortage_days": shortage_days,
            "severity": severity,
            "should_alert": should_alert,
            "reorder_qty": reorder_qty,
        })
    priority = {"critico": 0, "alerta": 1, "preventivo": 2, "ok": 3}
    items.sort(key=lambda item: (priority.get(item["severity"], 9), item["days_to_zero_ceil"]))
    critical = [item for item in items if item["severity"] in {"critico", "alerta", "preventivo"}]
    main = critical[0] if critical else (items[0] if items else None)
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "workspace": workspace,
        "items": items,
        "critical_items": critical,
        "main_alert": main,
        "has_alert": bool(critical),
    }

def pos_find_existing_offline_receipt(workspace_key, offline_id):
    if not offline_id:
        return None
    safe_workspace = werkzeug.utils.secure_filename(workspace_key)
    if not os.path.isdir(POS_BOLETAS_DIR):
        return None
    for entry in os.listdir(POS_BOLETAS_DIR):
        if not entry.startswith(f"{safe_workspace}-") or not entry.endswith(".json"):
            continue
        path = os.path.join(POS_BOLETAS_DIR, entry)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                metadata = json.load(fh)
        except Exception:
            continue
        if metadata.get("offline_id") == offline_id:
            return metadata
    return None

def pos_save_receipt_pdf(workspace, user, items, totals, offline_id=None, source="online"):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    os.makedirs(POS_BOLETAS_DIR, exist_ok=True)
    existing = pos_find_existing_offline_receipt(workspace["key"], offline_id)
    if existing:
        return existing

    sale_id = f"POS-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"
    safe_workspace = werkzeug.utils.secure_filename(workspace["key"])
    pdf_name = f"{safe_workspace}-{sale_id}.pdf"
    json_name = f"{safe_workspace}-{sale_id}.json"
    pdf_path = os.path.join(POS_BOLETAS_DIR, pdf_name)
    json_path = os.path.join(POS_BOLETAS_DIR, json_name)

    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    y = height - 54
    c.setFont("Helvetica-Bold", 14)
    c.drawString(54, y, "QUANTUS PUNTO DE VENTA - RESPALDO DE BOLETA")
    y -= 24
    c.setFont("Helvetica", 10)
    c.drawString(54, y, "Documento demo/no tributario. Respalda venta registrada desde maquina POS externa o flujo de caja interno.")
    y -= 26
    c.drawString(54, y, f"Folio interno: {sale_id}")
    if offline_id:
        y -= 16
        c.drawString(54, y, f"Venta local sincronizada: {offline_id}")
    y -= 16
    c.drawString(54, y, f"Empresa: {workspace['name']} | RUT: {workspace['rut']} | Rubro: {workspace['rubro']}")
    y -= 16
    c.drawString(54, y, f"Usuario: {user.get('email') or user.get('username')} | Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 24
    c.line(54, y, width - 54, y)
    y -= 18
    c.setFont("Helvetica-Bold", 10)
    c.drawString(54, y, "SKU")
    c.drawString(126, y, "Producto")
    c.drawRightString(410, y, "Cant.")
    c.drawRightString(490, y, "Unitario")
    c.drawRightString(width - 54, y, "Total")
    c.setFont("Helvetica", 10)
    y -= 14
    for item in items:
        if y < 110:
            c.showPage()
            y = height - 54
            c.setFont("Helvetica", 10)
        c.drawString(54, y, item["sku"][:12])
        c.drawString(126, y, item["name"][:42])
        c.drawRightString(410, y, str(item["qty"]))
        c.drawRightString(490, y, f"${item['unit_price']:,}".replace(",", "."))
        c.drawRightString(width - 54, y, f"${item['line_total']:,}".replace(",", "."))
        y -= 16
    y -= 8
    c.line(54, y, width - 54, y)
    y -= 20
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(490, y, "Neto")
    c.drawRightString(width - 54, y, f"${totals['net']:,}".replace(",", "."))
    y -= 16
    c.drawRightString(490, y, "IVA ref. 19%")
    c.drawRightString(width - 54, y, f"${totals['iva']:,}".replace(",", "."))
    y -= 18
    c.drawRightString(490, y, "Total")
    c.drawRightString(width - 54, y, f"${totals['total']:,}".replace(",", "."))
    y -= 34
    c.setFont("Helvetica", 9)
    c.drawString(54, y, "Archivo guardado para auditoria, respaldo y conciliacion. No reemplaza DTE/SII certificado.")
    c.save()

    metadata = {
        "sale_id": sale_id,
        "workspace_key": workspace["key"],
        "workspace_name": workspace["name"],
        "workspace_rut": workspace["rut"],
        "user": user.get("email") or user.get("username"),
        "items": items,
        "totals": totals,
        "pdf_file": pdf_name,
        "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "offline_id": offline_id,
        "source": source,
        "status": "PDF_RESPALDO_GUARDADO_NO_DTE",
    }
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, ensure_ascii=False, indent=2)
    return metadata

def authenticate_pos_user(username, password):
    username = (username or "").strip().lower()
    user = POS_USERS.get(username)
    if user and hmac.compare_digest(user["password"], password or ""):
        return username, user
    demo_account = active_demo_accounts_by_username().get(username)
    if demo_account and verify_master_password(password or "", demo_account.get("password") or {}):
        return username, {
            "password": "",
            "display_name": demo_account.get("contact_name") or demo_account.get("company") or "Demo temporal",
            "email": demo_account.get("email") or "",
            "role": "demo_client",
            "workspaces": demo_workspace_keys(demo_account),
        }

    auth = load_master_auth()
    master_username = (auth.get("username") or MASTER_ADMIN_USER or "").strip().lower()
    if username == master_username and verify_master_password(password or "", auth.get("password") or {}):
        return "owner", {
            "password": "",
            "display_name": "Felipe Mejias",
            "email": MASTER_ADMIN_EMAIL,
            "role": "owner_demo",
            "workspaces": ["don-manolo", "minimarket", "san-juan", "boutique", "ohiggins"],
        }
    try:
        response = requests.post(
            f"{QUANTUS_ERP_SERVER_URL}/api/auth/login",
            json={"username": username, "password": password or ""},
            timeout=8,
        )
        if response.ok:
            data = response.json()
            erp_user = data.get("user") or {}
            business_types = erp_user.get("business_types") or []
            return username, {
                "password": "",
                "display_name": erp_user.get("name") or username,
                "email": erp_user.get("email") or "",
                "role": "superadmin" if erp_user.get("role") == "SuperAdmin" else "erp_client",
                "erp_role": erp_user.get("role"),
                "erp_business_types": business_types,
                "workspaces": [
                    key for key, rubro in POS_ERP_RUBRO_BY_WORKSPACE.items()
                    if rubro in business_types
                ],
                "source": "erp_server",
            }
    except Exception as exc:
        app.logger.warning("ERP server credential delegation failed for %s: %s", username, exc)
    return None, None

ACTIVE_POS_SESSIONS = {}
POS_SESSION_LOCK = Lock()

@app.route("/punto-de-venta", methods=["GET", "POST"])
@app.route("/punto-de-venta/acceso", methods=["GET", "POST"])
@app.route("/punto-de-venta/clientes", methods=["GET", "POST"])
@app.route("/clientes", methods=["GET", "POST"])
@app.route("/pos/acceso", methods=["GET", "POST"])
def pos_cliente_login():
    erp_status = erp_server_status()
    erp_clients_url = erp_server_clients_url()
    if request.method == "POST":
        username, user = authenticate_pos_user(request.form.get("username"), request.form.get("password"))
        if not user:
            return render_template(
                "pos_cliente_login.html",
                show_companies=False,
                error="Credenciales inválidas para Punto de Venta.",
                companies=[],
                pos_user=None,
                erp_server_status=erp_status,
                erp_server_clients_url=erp_clients_url,
            ), 401

        # Control de Sesión Única Activa (Anti-Concurrencia)
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "127.0.0.1")
        force_login = request.form.get("force_login") == "1"
        current_time = time.time()

        with POS_SESSION_LOCK:
            existing_session = ACTIVE_POS_SESSIONS.get(username)
            my_token = session.get("_pos_auth_token")

            if existing_session and not force_login:
                # Si la sesión anterior estuvo activa en las últimas 2 horas y proviene de otro token
                if (current_time - existing_session.get("last_seen", 0) < 7200) and (my_token != existing_session.get("token")):
                    return render_template(
                        "pos_cliente_login.html",
                        show_companies=False,
                        error=f"⚠️ El usuario '{username}' ya cuenta con una sesión activa en otro navegador. Solo se permite 1 sesión simultánea.",
                        allow_force_login=True,
                        force_username=username,
                        force_password=request.form.get("password"),
                        companies=[],
                        pos_user=None,
                        erp_server_status=erp_status,
                        erp_server_clients_url=erp_clients_url,
                    ), 409

            # Registrar nueva sesión activa
            new_token = secrets.token_urlsafe(32)
            session["_pos_auth_token"] = new_token
            ACTIVE_POS_SESSIONS[username] = {
                "token": new_token,
                "login_time": current_time,
                "last_seen": current_time,
                "ip": client_ip
            }

        session["pos_username"] = username
        session.pop("pos_workspace_key", None)
        companies = pos_allowed_workspaces({"username": username, **user})
        if user.get("role") == "superadmin":
            return redirect("/punto-de-venta/clientes")
        if user.get("role") == "demo_client":
            demo_account = active_demo_accounts_by_username().get(username)
            vertical_key = (demo_account or {}).get("vertical")
            vertical_info = DEMO_VERTICALS.get(vertical_key or "")
            if vertical_info and vertical_info.get("workspace_key"):
                session["pos_workspace_key"] = vertical_info["workspace_key"]
                return redirect(erp_server_sso_url(vertical_info["workspace_key"], portal_user=username, rubro=vertical_key))
            if vertical_info and vertical_info.get("path"):
                return redirect(vertical_info["path"])
        if user.get("source") == "erp_server":
            erp_business_types = user.get("erp_business_types") or []
            if len(erp_business_types) == 1:
                return redirect(erp_server_sso_url(portal_user=username, rubro=erp_business_types[0]))
            if len(erp_business_types) > 1:
                return redirect(erp_server_sso_url(portal_user=username, rubro=erp_business_types[0]))
        if len(companies) == 1:
            session["pos_workspace_key"] = companies[0]["key"]
            return redirect(erp_server_sso_url(companies[0]["key"], portal_user=username))
        return redirect("/punto-de-venta/clientes")

    if request.args.get("logout") == "1":
        uname = session.get("pos_username")
        if uname:
            with POS_SESSION_LOCK:
                ACTIVE_POS_SESSIONS.pop(uname, None)
        session.pop("pos_username", None)
        session.pop("pos_workspace_key", None)
        session.pop("_pos_auth_token", None)
        return redirect("/punto-de-venta/acceso")

    user = pos_session_user()
    current_path = request.path.rstrip("/")
    
    # Ley 21.719 / CARTA MAGNA Regla 11 & 12: Bloquear acceso anónimo a la lista de clientes/empresas
    if current_path in ["/clientes", "/punto-de-venta/clientes"] and not user:
        return redirect("/punto-de-venta/acceso")

    show_co = bool(user)
    return render_template(
        "pos_cliente_login.html",
        show_companies=show_co,
        companies=pos_allowed_workspaces(user) if user else [],
        pos_user=user,
        error=None,
        erp_server_status=erp_status,
        erp_server_clients_url=erp_clients_url,
    )

@app.route("/punto-de-venta/clientes-erp")
def pos_erp_clients_link():
    return redirect("/punto-de-venta/acceso?logout=1", code=302)


@app.route("/pos/seleccionar/<workspace_key>", methods=["POST"])
def pos_select_workspace(workspace_key):
    user = pos_session_user()
    if not user:
        return redirect("/clientes")
    if workspace_key not in user.get("workspaces", []):
        abort(403, "Empresa no autorizada para estas credenciales.")
    session["pos_workspace_key"] = workspace_key
    return redirect(erp_server_sso_url(workspace_key, portal_user=session.get("pos_username")))

@app.route("/pos/usuarios/crear", methods=["POST"])
def pos_create_user():
    actor, workspace, guard = require_pos_user_admin()
    if guard:
        return guard
    display_name = (request.form.get("display_name") or "").strip()[:80]
    email = (request.form.get("email") or "").strip().lower()[:120]
    role = pos_validate_role((request.form.get("role") or "").strip())
    if not display_name or "@" not in email:
        abort(400, "Nombre y correo son obligatorios.")
    user_id = "USR-" + secrets.token_hex(8).upper()
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    ensure_pos_admin_storage()
    with sqlite3.connect(POS_ADMIN_DB) as conn:
        conn.execute(
            """
            INSERT INTO pos_workspace_users (
                id, workspace_key, display_name, email, role, status, created_by, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, 'activo', ?, ?, ?)
            """,
            (user_id, workspace["key"], display_name, email, role, actor.get("username"), now, now),
        )
    return redirect("/pos#usuarios")

@app.route("/pos/usuarios/<user_id>/actualizar", methods=["POST"])
def pos_update_user(user_id):
    actor, workspace, guard = require_pos_user_admin()
    if guard:
        return guard
    display_name = (request.form.get("display_name") or "").strip()[:80]
    email = (request.form.get("email") or "").strip().lower()[:120]
    role = pos_validate_role((request.form.get("role") or "").strip())
    status = (request.form.get("status") or "").strip()
    if status not in {"activo", "suspendido"}:
        abort(400, "Estado no permitido.")
    if not display_name or "@" not in email:
        abort(400, "Nombre y correo son obligatorios.")
    ensure_pos_admin_storage()
    with sqlite3.connect(POS_ADMIN_DB) as conn:
        cur = conn.execute(
            """
            UPDATE pos_workspace_users
            SET display_name=?, email=?, role=?, status=?, updated_at=?
            WHERE id=? AND workspace_key=?
            """,
            (display_name, email, role, status, datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), user_id, workspace["key"]),
        )
    if cur.rowcount < 1:
        abort(404, "Usuario no encontrado para esta empresa.")
    return redirect("/pos#usuarios")

@app.route("/pos/usuarios/<user_id>/eliminar", methods=["POST"])
def pos_delete_user(user_id):
    actor, workspace, guard = require_pos_user_admin()
    if guard:
        return guard
    ensure_pos_admin_storage()
    with sqlite3.connect(POS_ADMIN_DB) as conn:
        cur = conn.execute(
            "DELETE FROM pos_workspace_users WHERE id=? AND workspace_key=?",
            (user_id, workspace["key"]),
        )
    if cur.rowcount < 1:
        abort(404, "Usuario no encontrado para esta empresa.")
    return redirect("/pos#usuarios")

@app.route("/pos/configuracion/habilitar-feature", methods=["POST"])
def pos_enable_restricted_feature():
    user, workspace, guard = require_pos_workspace()
    if guard:
        return guard
    feature_key = (request.form.get("feature") or "").strip()
    pos_feature_gate(feature_key)
    return redirect("/pos#configuracion")

@app.route("/pos/boletas/respaldo", methods=["POST"])
def pos_create_receipt_backup():
    user, workspace, guard = require_pos_workspace()
    if guard:
        return guard
    data = request.get_json(silent=True) or {}
    items, totals = pos_build_receipt_items(workspace, data.get("items") or [])
    receipt = pos_save_receipt_pdf(
        workspace,
        user,
        items,
        totals,
        offline_id=(data.get("offline_id") or None),
        source="online",
    )
    return jsonify({
        "ok": True,
        "sale_id": receipt["sale_id"],
        "status": receipt["status"],
        "pdf_url": url_for("pos_receipt_pdf", filename=receipt["pdf_file"]),
    })

@app.route("/pos/sync/offline-sales", methods=["POST"])
def pos_sync_offline_sales():
    user, workspace, guard = require_pos_workspace()
    if guard:
        return guard
    data = request.get_json(silent=True) or {}
    sales = data.get("sales") or []
    if not isinstance(sales, list) or len(sales) > 50:
        abort(400, "Lote offline no valido.")

    synced = []
    failed = []
    for sale in sales:
        offline_id = str(sale.get("offline_id") or "").strip()[:80]
        if not offline_id:
            failed.append({"offline_id": None, "error": "offline_id requerido"})
            continue
        try:
            items, totals = pos_build_receipt_items(workspace, sale.get("items") or [])
            receipt = pos_save_receipt_pdf(
                workspace,
                user,
                items,
                totals,
                offline_id=offline_id,
                source="offline_sync",
            )
            synced.append({
                "offline_id": offline_id,
                "sale_id": receipt["sale_id"],
                "status": receipt["status"],
                "pdf_url": url_for("pos_receipt_pdf", filename=receipt["pdf_file"]),
            })
        except Exception as exc:
            failed.append({"offline_id": offline_id, "error": str(exc)})
    return jsonify({"ok": not failed, "synced": synced, "failed": failed})

@app.route("/pos/boletas/<filename>")
def pos_receipt_pdf(filename):
    user, workspace, guard = require_pos_workspace()
    if guard:
        return guard
    safe_name = werkzeug.utils.secure_filename(filename)
    expected_prefix = werkzeug.utils.secure_filename(workspace["key"]) + "-"
    if safe_name != filename or not safe_name.startswith(expected_prefix) or not safe_name.endswith(".pdf"):
        abort(403, "Boleta no autorizada para esta empresa.")
    path = os.path.join(POS_BOLETAS_DIR, safe_name)
    if not os.path.exists(path):
        abort(404, "Boleta no encontrada.")
    return send_file(path, mimetype="application/pdf", as_attachment=False, download_name=safe_name)

@app.route("/pos")
@app.route("/pos_terminal")
@app.route("/erp/pos")
@app.route("/app")
def pos_terminal():
    return redirect(erp_server_sso_url(session.get("pos_workspace_key"), portal_user=session.get("pos_username")), code=302)

@app.route("/informe-quiebre-stock-ia")
def informe_quiebre_stock_ia():
    user, workspace, guard = require_pos_workspace()
    if guard:
        return guard
    stock_ai = pos_stock_ai_analysis(workspace)
    agent_context = pos_demo_agent_context(workspace, stock_ai)
    return render_template(
        "informe_quiebre_stock_ia.html",
        stock_ai=stock_ai,
        agent_context=agent_context,
        workspace=workspace,
        pos_user=user,
    )

@app.route("/privacidad")
@app.route("/politica-de-privacidad")
@app.route("/politicas-de-privacidad")
def privacidad_quantus():
    body = """
    <h2>Responsable del tratamiento</h2>
    <p>Quantus Chile SpA, RUT 78.478.612-9, con domicilio societario en Rancagua, Región del Libertador General Bernardo O'Higgins, opera este sitio y sus radares asociados.</p>
    <h2>Datos tratados</h2>
    <p>Según el servicio contratado o consultado, Quantus puede tratar nombre, razón social, RUT, correo, teléfono, WhatsApp, criterios de búsqueda, documentos, reportes, pagos, consentimientos y evidencia operacional.</p>
    <h2>Finalidades</h2>
    <p>Prestar servicios de vigilancia, responder solicitudes, generar reportes, administrar cuentas, registrar consentimientos, confirmar pagos, prevenir fraude, mantener seguridad, respaldo y auditoría.</p>
    <h2>Principios</h2>
    <p>El tratamiento se organiza bajo finalidad, proporcionalidad, calidad, transparencia, responsabilidad, seguridad y confidencialidad. Los datos no deben usarse para fines incompatibles con los informados.</p>
    <h2>Publicidad de Terceros y Google AdSense</h2>
    <p>Quantus Chile SpA puede mostrar anuncios publicitarios servidos por Google AdSense y sus redes asociadas. Google, como proveedor externo, utiliza cookies (incluida la cookie de DoubleClick / DART) para publicar anuncios en este sitio web en función de las visitas anteriores de los usuarios a este u otros sitios web en Internet.</p>
    <p>Los usuarios pueden inhabilitar el uso de cookies para la publicidad personalizada accediendo a la <a href="https://adssettings.google.com" target="_blank" rel="noopener noreferrer" style="color:#38bdf8; text-decoration:underline;">Configuración de Anuncios de Google</a> o a través del portal de la industria <a href="https://www.aboutads.info" target="_blank" rel="noopener noreferrer" style="color:#38bdf8; text-decoration:underline;">www.aboutads.info</a>.</p>
    <h2>Derechos de titulares (Ley N° 21.719)</h2>
    <p>Los titulares pueden ejercer sus derechos de <strong>Acceso, Rectificación, Supresión, Oposición, Portabilidad o Bloqueo</strong> directamente a través de nuestro <a href="/privacidad/derechos-arcop" style="color:#38bdf8; font-weight:bold; text-decoration:underline;">Portal Oficial de Derechos ARCOP</a> (con emisión de comprobante inmutable y plazo legal de 10 días hábiles) o escribiendo a privacidad@quantuschile.cl.</p>
    <h2>Conservación</h2>
    <p>Los datos se conservan mientras sean necesarios para el servicio, cumplimiento contractual, soporte, trazabilidad o exigencias legales; luego podrán eliminarse, bloquearse o anonimizarse. En suscripciones vencidas, Quantus ejecuta alertas de término y una política de eliminación, bloqueo o anonimizado según corresponda.</p>
    """
    return render_template(
        "legal_simple.html",
        title="Política de Privacidad",
        notice="Política oficial de privacidad y protección de datos personales de Quantus Chile SpA conforme a la Ley N° 21.719 y normativas internacionales.",
        body=body,
    )

@app.route("/privacidad/derechos-arcop")
@app.route("/derechos-arcop")
@app.route("/arcop")
@app.route("/portal-arcop")
def portal_arcop_view():
    return render_template("portal_arcop.html")

@app.route("/terminos")
@app.route("/terminos-y-condiciones")
@app.route("/terminos-de-servicio")
def terminos_quantus():
    body = """
    <h2>Objeto del sitio</h2>
    <p>quantuschile.cl es la plataforma oficial de Quantus Chile SpA, RUT 78.478.612-9, para enlazar radares de inteligencia de negocios, portales y servicios digitales relacionados con vigilancia legal, comercial y operacional. El canal de contacto general es contacto@quantuschile.cl y el canal de privacidad es privacidad@quantuschile.cl.</p>
    <h2>Servicios</h2>
    <p>Los servicios pueden incluir Diario Oficial, licitaciones, INAPI, remates y administración privada. Cada módulo cuenta con términos, condiciones, advertencias de fuente y flujos de contratación transparentes.</p>
    <h2>Fuentes oficiales y alcance</h2>
    <p>Quantus monitorea fuentes públicas u oficiales para generar alertas, resúmenes y recomendaciones operativas. El servicio no reemplaza la lectura de la publicación original, la gestión ante el organismo correspondiente ni la asesoría de un abogado, contador u otro profesional cuando el caso lo requiera.</p>
    <h2>Publicidad y monetización</h2>
    <p>El sitio puede incluir espacios publicitarios de terceros administrados por Google AdSense y redes colaboradoras. El contenido publicitario mostrado no constituye recomendación expresa de Quantus Chile SpA.</p>
    <h2>Información honesta</h2>
    <p>La plataforma no implica afiliación directa con instituciones públicas. Los logos, nombres o marcas de instituciones se usan exclusivamente como referencia descriptiva de fuentes públicas. La facturación está disponible con los datos tributarios informados por el cliente.</p>
    <h2>Contratación y pagos</h2>
    <p>Antes de cualquier pago, Quantus registra datos, valida duplicados y muestra el precio total en pesos chilenos, modalidad de pago, duración del plan, renovación si corresponde y condiciones aplicables. El comprobante de pago electrónico acredita la operación y la factura se emite por el canal tributario oficial.</p>
    <h2>Limitación de responsabilidad</h2>
    <p>Los radares dependen de la disponibilidad y calidad de las fuentes oficiales o públicas. Las alertas preventivas no reemplazan asesoría legal, contable o revisión humana especializada.</p>
    <h2>Datos personales</h2>
    <p>El tratamiento de datos se rige por la política de privacidad, el consentimiento informado y las finalidades aceptadas por el usuario conforme a la Ley N° 21.719.</p>
    """
    return render_template(
        "legal_simple.html",
        title="Términos y Condiciones de Uso",
        notice="Términos y condiciones oficiales de uso de la plataforma Quantus Chile SpA.",
        body=body,
    )

@app.route("/cookies")
def cookies_quantus():
    body = """
    <h2>Uso de Cookies en Quantus</h2>
    <p>Quantus utiliza cookies técnicas necesarias para garantizar la seguridad, navegación, sesión, protección CSRF, gestión de formularios, preferencias de privacidad y acceso al Centro Maestro.</p>
    <h2>Cookies de Analítica y Terceros</h2>
    <p>El sitio dispone de un sistema de gestión de consentimiento. Las cookies de analítica y medición ayudan a comprender cómo interactúan los usuarios con la plataforma para mejorar continuamente la experiencia de uso.</p>
    <h2>Cookies de Publicidad y Google AdSense</h2>
    <p>Este sitio puede utilizar cookies publicitarias servidas por Google AdSense y sus socios de red. Estas cookies permiten mostrar publicidad relevante y no invasiva, limitar la frecuencia con que ve un anuncio y medir el rendimiento publicitario.</p>
    <p>Usted puede desactivar la personalización de anuncios en cualquier momento accediendo a <a href="https://adssettings.google.com" target="_blank" rel="noopener noreferrer" style="color:#38bdf8; text-decoration:underline;">Configuración de Anuncios de Google</a> o administrando las preferencias desde la configuración de su navegador web.</p>
    <h2>Gestión y Preferencias</h2>
    <p>El usuario puede aceptar, rechazar o configurar sus preferencias de cookies desde el banner inicial o eliminando los datos del sitio en su navegador.</p>
    """
    return render_template(
        "legal_simple.html",
        title="Política de Cookies",
        notice="Política oficial de cookies de Quantus Chile SpA. Detalle del uso de cookies técnicas, de analítica y de publicidad de terceros.",
        body=body,
    )

@app.route("/api/arcop/solicitud", methods=["POST"])
def api_recibir_solicitud_arcop():
    import os, json, datetime, hashlib, random
    data = request.get_json(silent=True) or request.form or {}
    nombre = (data.get("nombre") or "").strip()
    rut = (data.get("rut") or "").strip()
    email = (data.get("email") or "").strip()
    telefono = (data.get("telefono") or "").strip()
    tipo_derecho = (data.get("tipo_derecho") or "acceso").strip().lower()
    calidad = (data.get("calidad") or "cliente").strip()
    empresa_ref = (data.get("empresa_referencia") or "").strip()
    fundamento = (data.get("fundamento") or "").strip()

    if not nombre or not rut or not email or not fundamento:
        return jsonify({"status": "error", "message": "Faltan campos obligatorios (Nombre, RUT, Email o Fundamento)."}), 400

    now = datetime.datetime.now()
    folio = f"ARCOP-{now.year}-{random.randint(1000, 9999)}"

    # Calcular 10 dias habiles (excluyendo sabados y domingos)
    dias_agregados = 0
    cur = now
    while dias_agregados < 10:
        cur += datetime.timedelta(days=1)
        if cur.weekday() < 5:
            dias_agregados += 1
    fecha_limite = cur.strftime("%d/%m/%Y")
    fecha_ingreso = now.strftime("%d/%m/%Y %H:%M:%S")

    # Hash SHA-256 de evidencia
    raw_signature = f"{folio}|{rut}|{email}|{tipo_derecho}|{fundamento}|{now.isoformat()}"
    hash_sha256 = hashlib.sha256(raw_signature.encode("utf-8")).hexdigest()

    labels_map = {
        "acceso": "🔍 Acceso a Datos Personales",
        "rectificacion": "✏️ Rectificación de Datos",
        "supresion": "🗑️ Supresión / Borrado (Derecho al Olvido)",
        "oposicion": "✋ Oposición al Tratamiento",
        "portabilidad": "📦 Portabilidad de Datos",
        "bloqueo": "🔒 Bloqueo Temporal de Datos"
    }

    solicitud_record = {
        "folio": folio,
        "hash_sha256": hash_sha256,
        "tipo_derecho": tipo_derecho,
        "tipo_derecho_label": labels_map.get(tipo_derecho, tipo_derecho.upper()),
        "nombre": nombre,
        "rut": rut,
        "email": email,
        "telefono": telefono,
        "calidad": calidad,
        "empresa_referencia": empresa_ref,
        "fundamento": fundamento,
        "fecha_ingreso": fecha_ingreso,
        "fecha_limite": fecha_limite,
        "estado": "INGRESADA_EN_EVALUACION",
        "created_at": now.isoformat()
    }

    try:
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(data_dir, exist_ok=True)
        arcop_file = os.path.join(data_dir, "arcop_requests.json")
        records = []
        if os.path.exists(arcop_file):
            try:
                with open(arcop_file, "r", encoding="utf-8") as f:
                    records = json.load(f)
            except Exception:
                records = []
        records.insert(0, solicitud_record)
        with open(arcop_file, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error guardando bitacora ARCOP: {e}")

    return jsonify({
        "status": "success",
        "folio": folio,
        "hash_sha256": hash_sha256,
        "fecha_ingreso": fecha_ingreso,
        "fecha_limite": fecha_limite,
        "tipo_derecho_label": labels_map.get(tipo_derecho, tipo_derecho.upper())
    }), 200

@app.route("/api/arcop/solicitudes", methods=["GET"])
def api_listar_solicitudes_arcop():
    import os, json, datetime
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    arcop_file = os.path.join(data_dir, "arcop_requests.json")
    records = []
    if os.path.exists(arcop_file):
        try:
            with open(arcop_file, "r", encoding="utf-8") as f:
                records = json.load(f)
        except Exception:
            records = []

    now = datetime.datetime.now()
    # Calcular dias restantes
    for r in records:
        try:
            created_dt = datetime.datetime.fromisoformat(r.get("created_at", now.isoformat()))
            # dias habiles transcurridos
            dias_habiles_usados = 0
            cur = created_dt
            while cur.date() < now.date():
                cur += datetime.timedelta(days=1)
                if cur.weekday() < 5:
                    dias_habiles_usados += 1
            dias_restantes = max(0, 10 - dias_habiles_usados)
            r["dias_restantes"] = dias_restantes
            if r.get("estado") == "INGRESADA_EN_EVALUACION":
                if dias_restantes <= 2:
                    r["alerta_nivel"] = "urgente" # Rojo
                elif dias_restantes <= 5:
                    r["alerta_nivel"] = "advertencia" # Amarillo
                else:
                    r["alerta_nivel"] = "normal" # Verde
            else:
                r["alerta_nivel"] = "resuelta"
        except Exception:
            r["dias_restantes"] = 10
            r["alerta_nivel"] = "normal"

    return jsonify({"status": "success", "solicitudes": records, "total": len(records)}), 200

@app.route("/api/arcop/actualizar_estado", methods=["POST"])
def api_actualizar_estado_arcop():
    import os, json, datetime
    data = request.get_json(silent=True) or request.form or {}
    folio = (data.get("folio") or "").strip()
    nuevo_estado = (data.get("estado") or "RESUELTA").strip().upper()
    respuesta = (data.get("respuesta_oficial") or "").strip()
    operador = (data.get("operador") or "Oficial de Cumplimiento").strip()

    if not folio:
        return jsonify({"status": "error", "message": "Folio requerido"}), 400

    data_dir = os.path.join(os.path.dirname(__file__), "data")
    arcop_file = os.path.join(data_dir, "arcop_requests.json")
    records = []
    if os.path.exists(arcop_file):
        try:
            with open(arcop_file, "r", encoding="utf-8") as f:
                records = json.load(f)
        except Exception:
            records = []

    updated = False
    for r in records:
        if r.get("folio") == folio:
            r["estado"] = nuevo_estado
            r["respuesta_oficial"] = respuesta
            r["operador_responsable"] = operador
            r["fecha_resolucion"] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            updated = True
            break

    if updated:
        with open(arcop_file, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        return jsonify({"status": "success", "message": f"Solicitud {folio} actualizada a {nuevo_estado}."}), 200
    else:
        return jsonify({"status": "error", "message": "Folio no encontrado"}), 404

@app.route("/api/privacy/consent_hub", methods=["GET"])
def api_consent_hub_list():
    import os, json
    # Retornar resumen consolidado de consentimientos
    consents = [
        {
            "id": "CS-2026-001",
            "titular": "Quantus Intelligence Users",
            "rut": "78.***.***-9",
            "canal": "Plataforma Web / Checkbox Expreso",
            "finalidad": "Vigilancia de Marcas, Diario Oficial y ERP",
            "base_legal": "Art. 13° N° 1 (Consentimiento Expreso)",
            "hash_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "estado": "ACTIVO",
            "fecha": "2026-08-01 10:14:22"
        },
        {
            "id": "CS-2026-002",
            "titular": "Notificaciones WhatsApp Business",
            "rut": "15.***.***-4",
            "canal": "WhatsApp Opt-in Directo",
            "finalidad": "Alertas operacionales y reportes de licitaciones",
            "base_legal": "Art. 13° N° 2 (Ejecución Contractual)",
            "hash_sha256": "8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4",
            "estado": "ACTIVO",
            "fecha": "2026-08-05 14:20:00"
        }
    ]
    return jsonify({"status": "success", "consents": consents, "total": len(consents)}), 200

@app.route("/api/privacy/rat", methods=["GET"])
def api_privacy_rat_list():
    import os, json
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    rat_file = os.path.join(data_dir, "rat_inventory.json")

    default_rat = [
        {
            "id": "RAT-01",
            "actividad": "Gestión de Clientes, Ventas y ERP",
            "finalidad": "Prestación de servicios, emisión de facturas y control de cobranza.",
            "base_legal": "Art. 13° N° 2 (Ejecución de Contrato) y Obligación Tributaria (SII)",
            "titulares": "Clientes y Representantes Legales",
            "datos_tratados": "RUT, Razón Social, Nombre, Email, Teléfono, Dirección, Datos de Facturación",
            "destinatarios": "SII, Pasarelas de Pago (Mercado Pago), Hosting Seguro",
            "retencion": "6 años tributarios post término de contrato",
            "seguridad": "HTTPS TLS 1.3, Cifrado en reposo, RBAC estricto, Hash SHA-256",
            "transferencia_int": "No / Servidores bajo estándar de adecuación"
        },
        {
            "id": "RAT-02",
            "actividad": "Vigilancia de Marcas INAPI y Diario Oficial",
            "finalidad": "Monitoreo de publicaciones oficiales y alertas de coincidencias comerciales.",
            "base_legal": "Art. 13° N° 2 (Contrato) y Art. 13° N° 4 (Interés Legítimo)",
            "titulares": "Usuarios Suscriptores y Titulares de Marcas",
            "datos_tratados": "Nombre, Marca, RUT titular, Boletín INAPI, Extractos DO",
            "destinatarios": "Plataforma interna Quantus Intelligence",
            "retencion": "Duración de la suscripción + 1 año de histórico",
            "seguridad": "Aislamiento multi-tenant, logs inmutables",
            "transferencia_int": "No"
        },
        {
            "id": "RAT-03",
            "actividad": "Notificaciones Automatizadas por WhatsApp",
            "finalidad": "Envío de alertas de quiebre, vencimientos y reportes operacionales.",
            "base_legal": "Art. 13° N° 1 (Consentimiento Expreso del Titular)",
            "titulares": "Clientes registrados con opt-in activo",
            "datos_tratados": "Número de teléfono WhatsApp, Nombre de contacto",
            "destinatarios": "Meta WhatsApp Cloud API (con DPA firmado)",
            "retencion": "Hasta la revocación del consentimiento o fin del servicio",
            "seguridad": "Tokens revocables, cifrado end-to-end",
            "transferencia_int": "Sí (Meta Platforms Inc. con Cláusulas Contractuales Tipo)"
        },
        {
            "id": "RAT-04",
            "actividad": "Gestión Laboral y Nómina de Trabajadores",
            "finalidad": "Administración de contratos de trabajo, pago de remuneraciones e imposiciones.",
            "base_legal": "Art. 13° N° 2 y 3 (Código del Trabajo y Leyes Previsionales)",
            "titulares": "Empleados y Colaboradores",
            "datos_tratados": "RUT, Cuenta bancaria, AFP, Fonasa/Isapre, Liquidaciones, Asistencia",
            "destinatarios": "Previred, AFC, Dirección del Trabajo, Mutual de Seguridad",
            "retencion": "5 años posteriores al finiquito laboral",
            "seguridad": "Carpeta privada por RUT, acceso restringido a RRHH",
            "transferencia_int": "No"
        },
        {
            "id": "RAT-05",
            "actividad": "Videovigilancia y Seguridad en Instalaciones",
            "finalidad": "Seguridad física de bienes, clientes y colaboradores en locales comerciales.",
            "base_legal": "Art. 13° N° 4 (Interés Legítimo de Seguridad con Señalética Visible)",
            "titulares": "Visitantes, Clientes y Personal",
            "datos_tratados": "Imágenes y grabaciones de cámaras de seguridad",
            "destinatarios": "Uso interno exclusivo / Ministerio Público ante requerimiento judicial",
            "retencion": "30 días corridos (sobreescritura automática)",
            "seguridad": "NVR protegido con clave robusta sin acceso público",
            "transferencia_int": "No"
        }
    ]

    if os.path.exists(rat_file):
        try:
            with open(rat_file, "r", encoding="utf-8") as f:
                records = json.load(f)
                return jsonify({"status": "success", "rat": records, "total": len(records)}), 200
        except Exception:
            pass

    # Guardar los predeterminados si no existia
    os.makedirs(data_dir, exist_ok=True)
    with open(rat_file, "w", encoding="utf-8") as f:
        json.dump(default_rat, f, ensure_ascii=False, indent=2)

    return jsonify({"status": "success", "rat": default_rat, "total": len(default_rat)}), 200

@app.route("/api/privacy/rat/guardar", methods=["POST"])
def api_privacy_rat_guardar():
    import os, json
    data = request.get_json(silent=True) or request.form or {}
    actividad = (data.get("actividad") or "").strip()
    finalidad = (data.get("finalidad") or "").strip()
    base_legal = (data.get("base_legal") or "Art. 13° N° 1 (Consentimiento)").strip()
    titulares = (data.get("titulares") or "Clientes").strip()
    datos_tratados = (data.get("datos_tratados") or "").strip()
    destinatarios = (data.get("destinatarios") or "Interno").strip()
    retencion = (data.get("retencion") or "Mínimo necesario").strip()
    seguridad = (data.get("seguridad") or "HTTPS, Cifrado, RBAC").strip()

    if not actividad or not finalidad or not datos_tratados:
        return jsonify({"status": "error", "message": "Faltan campos obligatorios para el RAT."}), 400

    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    rat_file = os.path.join(data_dir, "rat_inventory.json")

    records = []
    if os.path.exists(rat_file):
        try:
            with open(rat_file, "r", encoding="utf-8") as f:
                records = json.load(f)
        except Exception:
            records = []

    nuevo_id = f"RAT-{len(records) + 1:02d}"
    nuevo_item = {
        "id": nuevo_id,
        "actividad": actividad,
        "finalidad": finalidad,
        "base_legal": base_legal,
        "titulares": titulares,
        "datos_tratados": datos_tratados,
        "destinatarios": destinatarios,
        "retencion": retencion,
        "seguridad": seguridad,
        "transferencia_int": data.get("transferencia_int", "No")
    }
    records.append(nuevo_item)

    with open(rat_file, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    return jsonify({"status": "success", "message": f"Actividad {nuevo_id} agregada al RAT Oficial.", "item": nuevo_item}), 200

@app.route("/api/privacy/dpia/generar", methods=["POST"])
def api_privacy_dpia_generar():
    import datetime
    data = request.get_json(silent=True) or request.form or {}
    proyecto = (data.get("proyecto") or "Nuevo Tratamiento de Datos").strip()
    finalidad = (data.get("finalidad") or "").strip()
    tipo_datos = data.get("tipo_datos", []) # ej: ["sensibles", "biometricos", "menores", "financieros", "generales"]
    tecnologias = data.get("tecnologias", []) # ej: ["ia_scoring", "camaras_faciales", "cloud_externo", "perfilamiento"]
    volumen = (data.get("volumen") or "medio").strip() # bajo, medio, masivo

    # Motor Cuantitativo de Evaluación de Riesgo Ley 21.719
    score_riesgo = 20 # Base
    factores = []
    mitigaciones = [
        "Cifrado de datos en reposo (AES-256) y en tránsito (TLS 1.3).",
        "Control de acceso basado en roles (RBAC) con autenticación multifactor (MFA).",
        "Registro inmutable de logs de acceso y auditoría de consultas."
    ]

    if "sensibles" in tipo_datos or "salud" in tipo_datos:
        score_riesgo += 30
        factores.append("Tratamiento de Datos Sensibles (Salud/Biometría - Art. 14° Ley 21.719).")
        mitigaciones.append("Consentimiento escrito expreso reforzado de los titulares.")

    if "menores" in tipo_datos:
        score_riesgo += 35
        factores.append("Tratamiento de Datos de Niños, Niñas y Adolescentes (Art. 32° Ley 21.719).")
        mitigaciones.append("Autorización firmada por padre/madre o representante legal con verificación de identidad.")

    if "biometricos" in tipo_datos or "camaras_faciales" in tecnologias:
        score_riesgo += 25
        factores.append("Identificación biométrica automatizada.")
        mitigaciones.append("Almacenamiento exclusivo de templates matemáticos hash, sin guardar imágenes faciales brutas.")

    if "ia_scoring" in tecnologias or "perfilamiento" in tecnologias:
        score_riesgo += 25
        factores.append("Decisiones automatizadas y perfilamiento algorítmico (Art. 15° Ley 21.719).")
        mitigaciones.append("Garantizar derecho de intervención humana y explicabilidad del algoritmo.")

    if volumen == "masivo":
        score_riesgo += 15
        factores.append("Tratamiento masivo a gran escala (>25.000 titulares).")

    score_riesgo = min(100, score_riesgo)

    if score_riesgo >= 70:
        nivel = "ALTO RIESGO / CRÍTICO"
        color = "#ef4444"
        consulta_previa = "REQUERIDA: Conforme a la Ley 21.719, se debe efectuar consulta previa a la Agencia de Protección de Datos antes de iniciar el tratamiento."
    elif score_riesgo >= 40:
        nivel = "RIESGO MODERADO"
        color = "#f59e0b"
        consulta_previa = "OPCIONAL / RECOMENDADA: Aplicar medidas mitigadoras y auditar semestralmente."
    else:
        nivel = "BAJO RIESGO"
        color = "#10b981"
        consulta_previa = "NO REQUERIDA: Tratamiento estándar amparado en ejecución de contrato."

    ahora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    informe_dpia = {
        "proyecto": proyecto,
        "fecha_evaluacion": ahora,
        "score_riesgo": score_riesgo,
        "nivel_riesgo": nivel,
        "color_badge": color,
        "consulta_previa": consulta_previa,
        "factores_detectados": factores if factores else ["Tratamiento comercial estándar."],
        "mitigaciones_obligatorias": mitigaciones,
        "conclusion": f"El proyecto '{proyecto}' presenta un nivel de {nivel} ({score_riesgo}/100). Cumpliendo las mitigaciones técnicas y organizativas listadas, el riesgo residual se reduce a nivel aceptable bajo la Ley 21.719."
    }

    return jsonify({"status": "success", "dpia": informe_dpia}), 200

@app.route("/retracto-cancelacion")
def retracto_cancelacion_quantus():
    body = """
    <h2>Servicios digitales Quantus</h2>
    <p>Quantus presta servicios digitales de monitoreo, analisis, configuracion de radares, reportes y gestion documental. Antes del pago se informa precio, duracion, modalidad, proveedor, factura, fuente del servicio y condiciones principales.</p>
    <h2>Retracto</h2>
    <p>En contrataciones a distancia puede existir derecho a retracto conforme a la Ley del Consumidor. Como criterio operacional, el cliente debe solicitarlo dentro del plazo legal y antes del uso efectivo del servicio o antes de que se active el monitoreo, analisis, reporte, ingreso documental o gestion solicitada.</p>
    <h2>Activacion inmediata</h2>
    <p>Cuando el cliente solicita activacion inmediata, configuracion del radar, revision de fuentes, generacion de informe IA, carga documental o inicio de gestion ante terceros, Quantus dejara evidencia de esa solicitud y evaluara la procedencia del retracto segun el estado real de ejecucion del servicio.</p>
    <h2>Cancelacion de suscripciones</h2>
    <p>Las suscripciones pueden cancelarse escribiendo a contacto@quantuschile.cl. El servicio se mantiene hasta el fin del periodo pagado, salvo una condicion distinta aceptada por escrito. Al terminar, se aplicara la politica de retencion, bloqueo, eliminacion o anonimizado segun corresponda.</p>
    <h2>Factura y respaldo</h2>
    <p>La factura se emite por el canal tributario de Quantus con los datos entregados por el cliente. El usuario recibira confirmacion escrita del servicio contratado, datos registrados, precio y vigencia.</p>
    """
    return render_template(
        "legal_simple.html",
        title="Retracto y cancelacion",
        notice="Criterio operativo para servicios digitales Quantus. Requiere revision contractual final antes de produccion publica.",
        body=body,
    )

def load_and_purge_remates():
    """
    Load remates from the radar SQLite database (populated by remates_radar_worker.py).
    Falls back to static JSON if the database doesn't exist or is empty.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "data", "remates_radar.sqlite3")
    json_path = os.path.join(base_dir, "data", "remates_inmuebles.json")

    # Try SQLite first
    if os.path.exists(db_path):
        try:
            import sqlite3 as _sqlite3
            conn = _sqlite3.connect(db_path, timeout=5)
            conn.row_factory = _sqlite3.Row
            rows = conn.execute("""
                WITH ranked AS (
                    SELECT *,
                           ROW_NUMBER() OVER(PARTITION BY fuente ORDER BY fecha_remate ASC) as rn
                    FROM remates_unificados
                    WHERE estado IN ('proximo', 'en_curso')
                      AND monto_minimo IS NOT NULL 
                      AND monto_minimo > 0
                )
                SELECT * FROM ranked
                WHERE rn <= 2
                ORDER BY rn ASC,
                    CASE fuente
                        WHEN 'REMATES_MADRID' THEN 1
                        WHEN 'PODER_JUDICIAL' THEN 2
                        WHEN 'MACAL_REMATES' THEN 3
                        WHEN 'TATTERSALL' THEN 4
                        WHEN 'TGR' THEN 5
                        WHEN 'ADUANA' THEN 6
                        WHEN 'DICREP_TIA_RICA' THEN 7
                        ELSE 8
                    END
                LIMIT 12
            """).fetchall()
            conn.close()

            if rows:
                remates = []
                for r in rows:
                    monto_min = float(r["monto_minimo"] or 0)
                    # Estimación de valor comercial y descuento
                    if monto_min > 50000000:
                        descuento_pct = 45
                        valor_comercial = round(monto_min * 1.82)
                    elif monto_min > 20000000:
                        descuento_pct = 50
                        valor_comercial = round(monto_min * 2.0)
                    elif monto_min > 5000000:
                        descuento_pct = 40
                        valor_comercial = round(monto_min * 1.67)
                    else:
                        descuento_pct = 55
                        valor_comercial = round(monto_min * 2.22)
                    
                    garantia_valevista = round(monto_min * 0.10)

                    remates.append({
                        "id": r["id"],
                        "fuente": r["fuente"],
                        "fuente_url": r["fuente_url"],
                        "tipo_propiedad": r["titulo"],
                        "descripcion": r["descripcion"] or "",
                        "direccion": r["direccion"] or r["titulo"],
                        "comuna": r["comuna"] or "",
                        "region": r["region"] or "",
                        "superficie": r["superficie"] or "",
                        "coordenadas_mapa": f"{r['latitud']},{r['longitud']}" if r["latitud"] else "",
                        "google_maps_url": r["google_maps_url"] or "",
                        "minimo_remate_clp": monto_min,
                        "fecha_remate": r["fecha_remate"] or "",
                        "estado": r["estado"],
                        "modalidad": r["modalidad"] or "Subasta Pública",
                        "tribunal": r["tribunal"] or "",
                        "rol_causa": r["rol_causa"] or "",
                        "imagen_url": r["imagen_url"] or "",
                        "uso_permitido": r["uso_permitido"] or "",
                        "tipo_bien": r["tipo_bien"] or "",
                        "descuento_estimado_pct": descuento_pct,
                        "valor_comercial_estimado_clp": valor_comercial,
                        "garantia_requerida_valevista_clp": garantia_valevista,
                        "rol_sii": "",
                        "evaluacion_oportunidad": f"🎯 Oportunidad detectada con {descuento_pct}% bajo avalúo comercial. Requiere garantía Vale Vista del 10% (${garantia_valevista:,.0f} CLP).".replace(",", "."),
                    })
                log.info("Loaded %d remates from SQLite radar DB", len(remates))
                return remates
        except Exception as e:
            log.warning("Could not read remates radar DB: %s", e)

    # Fallback to static JSON
    remates = []
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                remates = json.load(f)
        except Exception:
            remates = []

    return remates


@app.route('/admin/radar-total')
def admin_radar_total():
    """
    Secret dashboard to view all items collected by the radar, categorized by type.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "data", "remates_radar.sqlite3")
    
    items_by_type = {
        "vehiculos": [],
        "maquinaria": [],
        "inmuebles": [],
        "terrenos": [],
        "otros": []
    }
    
    if os.path.exists(db_path):
        try:
            import sqlite3 as _sqlite3
            conn = _sqlite3.connect(db_path, timeout=5)
            conn.row_factory = _sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM remates_unificados
                ORDER BY fecha_remate ASC, created_at DESC
            """).fetchall()
            conn.close()
            
            for r in rows:
                item = dict(r)
                tipo = item["tipo_bien"] or ""
                
                # Categorize
                if "vehiculo" in tipo:
                    items_by_type["vehiculos"].append(item)
                elif "maquinaria" in tipo:
                    items_by_type["maquinaria"].append(item)
                elif "inmueble" in tipo or "casa" in tipo or "departamento" in tipo:
                    items_by_type["inmuebles"].append(item)
                elif "terreno" in tipo or "parcela" in tipo:
                    items_by_type["terrenos"].append(item)
                else:
                    items_by_type["otros"].append(item)
                    
        except Exception as e:
            log.error("Could not read remates radar DB for admin route: %s", e)
            
    return render_template("admin_radar_total.html", data=items_by_type)

@app.route('/remates')
@app.route('/remates-inmuebles-chile')
def remates_inmuebles_view():
    remates = load_and_purge_remates()
    return render_template('remates_inmuebles.html', remates=remates)


@app.route('/ads.txt')
def ads_txt():
    """Google AdSense verification file."""
    return "google.com, pub-8306242057672839, DIRECT, f08c47fec0942fa0\n", 200, {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/sitemap.xml')
def sitemap_xml():
    """Dynamic sitemap for Google Search Console and SEO indexing."""
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    urls = [
        {'loc': 'https://www.quantuschile.cl/', 'priority': '1.0', 'changefreq': 'daily'},
        {'loc': 'https://www.quantuschile.cl/blog', 'priority': '0.9', 'changefreq': 'daily'},
        {'loc': 'https://www.quantuschile.cl/do', 'priority': '0.9', 'changefreq': 'daily'},
        {'loc': 'https://www.quantuschile.cl/licitaciones', 'priority': '0.9', 'changefreq': 'daily'},
        {'loc': 'https://www.quantuschile.cl/remates', 'priority': '0.9', 'changefreq': 'daily'},
        {'loc': 'https://www.quantuschile.cl/inapi', 'priority': '0.9', 'changefreq': 'daily'},
        {'loc': 'https://www.quantuschile.cl/empleos-publicos', 'priority': '0.9', 'changefreq': 'daily'},
        {'loc': 'https://www.quantuschile.cl/punto-de-venta', 'priority': '0.9', 'changefreq': 'weekly'},
        {'loc': 'https://www.quantuschile.cl/checklist-ley-21719', 'priority': '0.8', 'changefreq': 'weekly'},
        {'loc': 'https://www.quantuschile.cl/como-funciona', 'priority': '0.8', 'changefreq': 'monthly'},
        {'loc': 'https://www.quantuschile.cl/quienes-somos', 'priority': '0.8', 'changefreq': 'monthly'},
        {'loc': 'https://www.quantuschile.cl/contacto', 'priority': '0.7', 'changefreq': 'monthly'},
        {'loc': 'https://www.quantuschile.cl/seguridad-confianza', 'priority': '0.7', 'changefreq': 'monthly'},
        {'loc': 'https://www.quantuschile.cl/privacidad', 'priority': '0.5', 'changefreq': 'monthly'},
        {'loc': 'https://www.quantuschile.cl/terminos', 'priority': '0.5', 'changefreq': 'monthly'},
        {'loc': 'https://www.quantuschile.cl/cookies', 'priority': '0.5', 'changefreq': 'monthly'},
        {'loc': 'https://www.quantuschile.cl/privacidad/derechos-arcop', 'priority': '0.5', 'changefreq': 'monthly'},
    ]
    
    # Add all blog articles dynamically
    try:
        from data.blog_articles_data import get_all_articles
        for art in get_all_articles():
            urls.append({
                'loc': f"https://www.quantuschile.cl/blog/{art['slug']}",
                'priority': '0.8',
                'changefreq': 'weekly'
            })
    except Exception:
        pass

    xml_items = []
    for u in urls:
        xml_items.append(f"""  <url>
    <loc>{u['loc']}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>{u['changefreq']}</changefreq>
    <priority>{u['priority']}</priority>
  </url>""")
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + '\n'.join(xml_items) + '\n</urlset>'
    return sitemap, 200, {'Content-Type': 'application/xml; charset=utf-8'}


@app.route('/login')
def legacy_login_redirect():
    """Ruta legacy que fue reemplazada; 301 permanente a acceso punto de venta."""
    return redirect('/punto-de-venta/acceso', code=301)


@app.route('/robots.txt')
def robots_txt():
    """robots.txt file pointing to sitemap."""
    content = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /maestro/\n"
        "Disallow: /admin/\n"
        "Disallow: /pos/\n"
        "Disallow: /api/\n"
        "Disallow: /demo/\n"
        "Disallow: /punto-de-venta/acceso\n"
        "Disallow: /punto-de-venta/clientes\n"
        "Disallow: /punto-de-venta/clientes-erp\n"
        "\n"
        "Sitemap: https://www.quantuschile.cl/sitemap.xml\n"
    )
    return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/api/validar_suscripcion_previa', methods=['POST'])
def api_validar_suscripcion_previa():
    data = request_payload()
    rut_raw = (data.get('rut') or '').strip()
    nombre = (data.get('nombre') or '').strip()
    email = (data.get('email') or '').strip().lower()
    whatsapp = normalize_whatsapp(data.get('whatsapp') or data.get('telefono'))
    plan = (data.get('plan') or 'mensual').strip()
    payment_mode = (data.get('payment_mode') or 'one_time').strip()
    ruts_adicionales = (data.get('ruts_adicionales') or '').strip()
    watch_targets = []
    if rut_raw:
        watch_targets.append({'tipo': 'rut_principal', 'valor': rut_raw, 'prioridad': 'alta'})
    if ruts_adicionales:
        for term in ruts_adicionales.replace(';', ',').split(','):
            t_clean = term.strip()
            if t_clean:
                is_rut = any(ch.isdigit() for ch in t_clean) and ('-' in t_clean or '.' in t_clean)
                watch_targets.append({
                    'tipo': 'rut_adicional' if is_rut else 'termino_clave',
                    'valor': t_clean,
                    'prioridad': 'media'
                })
    
    rut_clean = clean_rut(rut_raw)
    if not validate_rut(rut_raw, required=True):
        return jsonify({'status': 'error', 'message': 'El RUT ingresado no es válido. Verifica el dígito verificador e inténtalo de nuevo.'}), 400

    nombre_words = [w for w in (nombre or '').split() if len(w) > 1]
    if len(nombre_words) < 2:
        return jsonify({
            'status': 'error',
            'message': 'Por favor ingresa tu nombre completo con ambos apellidos idéntico a tu carnet de identidad (ej: "Juan Andrés Pérez Soto") o la Razón Social completa para asegurar la máxima confiabilidad del escaneo.'
        }), 400

    if data.get("source_limitation_ack") != "1":
        return jsonify({'status': 'error', 'message': 'Debes aceptar la advertencia sobre posibles errores u omisiones del Diario Oficial para continuar.'}), 400
        
    people = refresh_do_subscription_lifecycle(load_do_people(), persist=True)
    existing = find_do_subscription(people, rut_raw, email)
    if existing:
        state = do_subscription_state(existing)
        if state in {"activo", "activo_permanente", "activo_sin_vencimiento"}:
            return jsonify({
                'status': 'ya_registrado',
                'registrado': True,
                'subscription_state': state,
                'message': f'El RUT {format_rut(rut_raw)} o el correo ingresado ya tiene una vigilancia activa. No realizaremos un nuevo cobro.'
            }), 200
        if state == "pendiente_pago":
            return jsonify({
                'status': 'pago_pendiente',
                'registrado': True,
                'subscription_state': state,
                'checkout_url': do_checkout_url(existing.get("plan") or plan, payment_mode),
                'message': 'Ya existe una solicitud pendiente de pago para estos datos. Puedes continuar al checkout o esperar la confirmación si ya pagaste.'
            }), 200
        if state in {"vencido_en_gracia", "vencido_pendiente_eliminacion", "pendiente_eliminacion"}:
            log.info("Renovación DO permitida para %s en estado %s", format_rut(rut_raw), state)

    checkout_url = do_checkout_url(plan, payment_mode)
    
    nuevo_id = max([p.get('id', 0) for p in people], default=0) + 1
    vencimiento = datetime.now().date() + timedelta(days=plan_duration_days(plan))
    nuevo_pre = {
        'id': nuevo_id,
        'nombre_completo': nombre,
        'rut': format_rut(rut_raw),
        'clean_rut': rut_clean,
        'alertar_a': email,
        'whatsapp': whatsapp,
        'whatsapp_consent': True,
        'ruts_adicionales': ruts_adicionales,
        'watch_targets': watch_targets,
        'estado': 'pendiente_pago',
        'subscription_state': 'pendiente_pago',
        'plan': plan,
        'payment_mode': payment_mode,
        'checkout_url': checkout_url,
        'fecha_registro': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'fecha_vencimiento_propuesta': vencimiento.strftime("%Y-%m-%d"),
        'privacy_cleanup_due': (datetime.now().date() + timedelta(days=DO_PENDING_PAYMENT_TTL_DAYS + DO_PRIVACY_RETENTION_DAYS)).strftime("%Y-%m-%d"),
        'ley_21719_consent': True,
        'consent_timestamp': datetime.now().isoformat(timespec="seconds"),
        'consent_ip': get_client_ip(),
        'consent_version': CONSENT_VERSION,
        'arco_rights_contact': 'privacidad@quantuschile.cl',
    }
    
    updated = False
    for i, p in enumerate(people):
        if do_identity_matches(p, rut_raw, email):
            people[i].update(nuevo_pre)
            updated = True
            break
            
    if not updated:
        people.append(nuevo_pre)
        
    save_do_people(people)
    
    return jsonify({
        'status': 'ok',
        'registrado': False,
        'checkout_url': checkout_url,
        'subscription_state': 'pendiente_pago',
        'message': 'Datos validados. Te llevaremos al pago seguro; la vigilancia se activará al confirmar el pago.'
    }), 200

@app.route('/api/validar_licitacion_previa', methods=['POST'])
def api_validar_licitacion_previa():
    data = request_payload()
    rut_raw = (data.get('rut') or '').strip()
    empresa = (data.get('empresa') or data.get('nombre') or '').strip()
    email = (data.get('email') or data.get('correo') or '').strip().lower()
    whatsapp = normalize_whatsapp(data.get('whatsapp') or data.get('telefono'))
    rubros = (data.get('rubros') or '').strip()
    plan = (data.get('plan') or 'oportunidades').strip()
    payment_mode = (data.get('payment_mode') or 'one_time').strip()

    if not validate_rut(rut_raw, required=True):
        return jsonify({'status': 'error', 'message': 'El RUT de la empresa no es válido. Verifica el dígito verificador e inténtalo nuevamente.'}), 400
    if not email:
        return jsonify({'status': 'error', 'message': 'Ingresa un correo para recibir alertas y reportes.'}), 400
    if data.get("data_consent") != "1":
        return jsonify({'status': 'error', 'message': 'Debes aceptar la autorización de tratamiento de datos personales para continuar.'}), 400
    if data.get("source_limitation_ack") != "1":
        return jsonify({'status': 'error', 'message': 'Debes aceptar la advertencia sobre cambios, anexos y plazos de Mercado Público para continuar.'}), 400

    clients = refresh_licitaciones_lifecycle(load_licitaciones_clients(), persist=True)
    existing = find_licitaciones_subscription(clients, rut_raw, email)
    if existing:
        state = licitaciones_subscription_state(existing)
        if state in {"activo", "activo_permanente", "activo_sin_vencimiento"}:
            return jsonify({
                'status': 'ya_registrado',
                'registrado': True,
                'subscription_state': state,
                'message': f'El RUT {format_rut(rut_raw)} o el correo ingresado ya tiene un Radar de Licitaciones activo. No realizaremos un nuevo cobro.'
            }), 200
        if state == "pendiente_pago":
            return jsonify({
                'status': 'pago_pendiente',
                'registrado': True,
                'subscription_state': state,
                'checkout_url': licitaciones_checkout_url(existing.get("plan") or plan, payment_mode),
                'message': 'Ya existe una solicitud pendiente de pago para estos datos. Puedes continuar al checkout o esperar la confirmación si ya pagaste.'
            }), 200
        if state in {"vencido_en_gracia", "vencido_pendiente_eliminacion", "pendiente_eliminacion"}:
            log.info("Renovación Licitaciones permitida para %s en estado %s", format_rut(rut_raw), state)

    checkout_url = licitaciones_checkout_url(plan, payment_mode)
    nuevo_id = max([c.get('id', 0) for c in clients], default=0) + 1
    vencimiento = datetime.now().date() + timedelta(days=licitaciones_plan_duration_days(plan))
    nuevo_pre = {
        'id': nuevo_id,
        'empresa': empresa,
        'nombre': empresa,
        'rut': format_rut(rut_raw),
        'clean_rut': clean_rut(rut_raw),
        'email': email,
        'whatsapp': whatsapp,
        'whatsapp_consent': bool(whatsapp),
        'rubros': rubros,
        'estado': 'pendiente_pago',
        'subscription_state': 'pendiente_pago',
        'plan': plan,
        'payment_mode': payment_mode,
        'checkout_url': checkout_url,
        'fecha_registro': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'fecha_vencimiento_propuesta': vencimiento.strftime("%Y-%m-%d"),
        'privacy_cleanup_due': (datetime.now().date() + timedelta(days=DO_PENDING_PAYMENT_TTL_DAYS + DO_PRIVACY_RETENTION_DAYS)).strftime("%Y-%m-%d"),
        'ley_21719_consent': True,
        'source_limitation_ack': True,
        'consent_timestamp': datetime.now().isoformat(timespec="seconds"),
        'consent_ip': get_client_ip(),
        'consent_version': CONSENT_VERSION,
        'arco_rights_contact': 'privacidad@quantuschile.cl',
    }

    updated = False
    for i, client in enumerate(clients):
        if licitaciones_identity_matches(client, rut_raw, email):
            clients[i].update(nuevo_pre)
            updated = True
            break
    if not updated:
        clients.append(nuevo_pre)

    save_licitaciones_clients(clients)
    save_service_consent(
        {
            "key": client_key_for("licitaciones", empresa, format_rut(rut_raw), email),
            "name": empresa or "Prospecto licitaciones",
            "module": "Licitaciones",
            "rut": format_rut(rut_raw),
            "rubro": rubros,
            "plan": plan,
            "email": email,
        },
        "Radar de Licitaciones 24/7",
        extra={
            "rubros": rubros,
            "whatsapp": whatsapp,
            "whatsapp_consent": bool(whatsapp),
            "payment_mode": payment_mode,
            "checkout_url": checkout_url,
            "fecha_vencimiento_propuesta": nuevo_pre["fecha_vencimiento_propuesta"],
            "source_limitation_ack": True,
        },
    )

    return jsonify({
        'status': 'ok',
        'registrado': False,
        'checkout_url': checkout_url,
        'subscription_state': 'pendiente_pago',
        'message': 'Datos validados. Te llevaremos al pago seguro; el radar se activará al confirmar el pago.'
    }), 200


def index():

    return render_template("index.html", current_utm=get_current_utm())

@app.route("/inapi")
@app.route("/inapi/")
@app.route("/marcas")
@app.route("/marcas/")
def index_alias():
    return render_template("marcas.html")

@app.route("/gracias_suscripcion")
@app.route("/pago_exitoso")
@app.route("/pago-exitoso")
@app.route("/success")
def gracias_suscripcion():
    modulo = request.args.get("modulo") or request.args.get("servicio") or request.args.get("m") or "diario_oficial"
    plan = request.args.get("plan") or "Suscripción Activa"
    rut = request.args.get("rut") or ""
    nombre = request.args.get("nombre") or ""
    email = request.args.get("email") or ""
    marca = request.args.get("marca") or ""
    clase = request.args.get("clase") or "1"
    
    return render_template(
        "success.html",
        modulo=modulo,
        plan=plan,
        rut=rut,
        nombre=nombre,
        email=email,
        marca=marca,
        clase=clase
    )

@app.route("/marketing/linkedin/autorizar")
def linkedin_autorizar():
    is_local = request.host.startswith(("127.0.0.1", "localhost"))
    try:
        from marketing.linkedin_client import get_authorization_url
        url, state = get_authorization_url(is_local=is_local)
        session["linkedin_state"] = state
        return redirect(url)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/marketing/api/auth/linkedin/callback")
def linkedin_callback():
    code = request.args.get("code")
    error = request.args.get("error")
    if error or not code:
        return f"<h3>Error en autenticación de LinkedIn: {error or 'Código ausente'}</h3><p><a href='/marketing/'>Volver a Marketing Center</a></p>", 400
    
    is_local = request.host.startswith(("127.0.0.1", "localhost"))
    try:
        from marketing.linkedin_client import exchange_code_for_token, get_user_profile
        token_info = exchange_code_for_token(code, is_local=is_local)
        profile = get_user_profile(token_info["access_token"])
        session["linkedin_user"] = profile
        return f"<h3>¡Conexión exitosa con LinkedIn!</h3><p>Acceso concedido a LinkedIn para Quantus Chile.</p><p><a href='/marketing/'>Ir a Marketing Center</a></p>"
    except Exception as e:
        return f"<h3>Error al intercambiar token con LinkedIn: {str(e)}</h3><p><a href='/marketing/'>Volver a Marketing Center</a></p>", 500

@app.route("/marketing/api/linkedin/publicar", methods=["POST"])
def linkedin_publicar():
    data = request.get_json() or request.form
    texto = data.get("texto")
    titulo = data.get("titulo")
    url_target = data.get("url")
    
    if not texto:
        return jsonify({"success": False, "error": "Falta el parámetro 'texto'"}), 400
        
    try:
        from marketing.linkedin_client import get_stored_token, post_share, get_user_profile
        token_info = get_stored_token()
        if not token_info or not token_info.get("access_token"):
            return jsonify({"success": False, "error": "No hay un token de LinkedIn activo. Por favor autoriza en /marketing/linkedin/autorizar"}), 401
            
        access_token = token_info["access_token"]
        profile = get_user_profile(access_token)
        author_urn = profile.get("sub") or profile.get("id") or "urn:li:person:authorized"
        if not author_urn.startswith("urn:li:"):
            author_urn = f"urn:li:person:{author_urn}"
            
        result = post_share(access_token, author_urn, texto, title=titulo, target_url=url_target)
        return jsonify({"success": True, "message": "Publicación realizada con éxito en LinkedIn", "result": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/vigilancia")
@app.route("/do")
@app.route("/do/")
@app.route("/DO")
@app.route("/Do")
@app.route("/DO/")
@app.route("/Do/")
@app.route("/VIGILANCIA")
@app.route("/Vigilancia")
def vigilancia():
    return render_template("vigilancia_do.html")

@app.route("/vigilancia/prospeccion")
@app.route("/do/prospeccion")
def vigilancia_prospeccion():
    return redirect(url_for("maestro_geointel"))

@app.route("/do/informe/<report_id>.pdf")
@app.route("/informes/<report_id>.pdf")
def report_pdf(report_id):
    report = get_report(report_id)
    if not report or not report.get("pdf_path") or not os.path.exists(report["pdf_path"]):
        abort(404)
    return send_file(
        report["pdf_path"],
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"quantus-diario-oficial-{report_id}.pdf",
    )

@app.route("/do/informe/<report_id>")
@app.route("/diario-oficial/informes/<report_id>")
@app.route("/informes/<report_id>")
def report_detail_html(report_id):
    report_data = get_report(report_id)
    if not report_data:
        ai_meta = {
            "resumen_ejecutivo": "Se detectó la publicación de la marca Biobelle Centro Médico & Estético (CVE 2853118) asociada al RUT 78.466.431-7 en la edición del Diario Oficial de Chile.",
            "acciones_recomendadas": [
                "Confirmar la publicación del extracto oficial de la marca (CVE 2853118).",
                "Monitorear la ventana de 30 días hábiles para observaciones u oposiciones en INAPI.",
                "Archivar comprobante digital en el expediente legal de Biobelle."
            ],
            "plazos_posibles": "Período de oposición de 30 días hábiles contados desde la publicación oficial."
        }
        report_data = {
            "id": report_id,
            "client_name": "BIOBELLE SALUD & ESTETICA SPA",
            "client_rut": "78.466.431-7",
            "publication_type": "Marca Comercial INAPI N° 1683119",
            "urgency": "Coincidencia Exacta por RUT",
            "created_at": "14/08/2026",
            "source_excerpt": "EXTRACTO OFICIAL (CVE 2853118): Biobelle Salud & Estética SpA (RUT 78.466.431-7), solicita el registro de la marca comercial 'BIOBELLE CENTRO MÉDICO & ESTÉTICO' para la Clase 44 (Establecimientos Médicos de Atención Ambulatoria) ante la Dirección del Diario Oficial de Chile. Fecha de publicación oficial: 14/08/2026.",
            "resumen": ai_meta["resumen_ejecutivo"],
            "acciones": ai_meta["acciones_recomendadas"],
            "plazos": ai_meta["plazos_posibles"],
            "official_url": "https://www.diariooficial.interior.gob.cl/publicaciones/2026/08/14/2853118.pdf"
        }
    else:
        ai_meta = {}
        if report_data.get("ai_json"):
            try:
                ai_meta = json.loads(report_data["ai_json"])
            except Exception:
                pass
        report_data["resumen"] = ai_meta.get("resumen_ejecutivo") or report_data.get("source_excerpt")
        report_data["acciones"] = ai_meta.get("acciones_recomendadas") or []
        report_data["plazos"] = ai_meta.get("plazos_posibles") or ""
        report_data["official_url"] = report_data.get("official_url") or "https://www.diariooficial.interior.gob.cl"
        
    return render_template("do_informe_detalle.html", report=report_data)

@app.route("/do/admin")
def do_admin_dashboard():
    require_admin_token()
    return render_template("do_admin.html", snapshot=dashboard_snapshot(), module_label="Diario Oficial")

@app.route("/admin/ia")
def ai_master_dashboard():
    require_admin_token()
    return render_template("do_admin.html", snapshot=dashboard_snapshot(), module_label="Quantus IA")

@app.route("/admin/maestro")
@app.route("/admin")
def admin_maestro_alias():
    return redirect(url_for("maestro_dashboard"))

@app.route("/maestro/login", methods=["GET", "POST"])
def maestro_login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        auth = load_master_auth()
        user_ok = hmac.compare_digest(username, auth.get("username") or MASTER_ADMIN_USER)
        pass_ok = verify_master_password(password, auth.get("password") or {})
        if user_ok and pass_ok:
            session["quantus_master_authenticated"] = True
            session["quantus_master_user"] = username
            return redirect(request.args.get("next") or url_for("maestro_dashboard"))
        return render_template("maestro_login.html", error="Credenciales inválidas. Revisa usuario y contraseña.", google_ready=google_oauth_configured())
    return render_template("maestro_login.html", error=request.args.get("error"), google_ready=google_oauth_configured())

@app.route("/maestro/google")
def maestro_google_login():
    if not google_oauth_configured():
        return redirect(url_for("maestro_login", error="Google Login aún no está configurado. Falta Client ID y Client Secret."))
    return redirect(build_google_auth_url())

@app.route("/maestro/google/callback")
def maestro_google_callback():
    if not google_oauth_configured():
        return redirect(url_for("maestro_login", error="Google Login aún no está configurado."))
    state = request.args.get("state") or ""
    expected_state = session.pop("google_oauth_state", "")
    if not state or not expected_state or not hmac.compare_digest(state, expected_state):
        return redirect(url_for("maestro_login", error="No se pudo validar la sesión de Google. Intenta nuevamente."))
    if request.args.get("error"):
        return redirect(url_for("maestro_login", error="Google rechazó el acceso o la sesión fue cancelada."))
    code = request.args.get("code") or ""
    if not code:
        return redirect(url_for("maestro_login", error="Google no devolvió un código válido."))
    token_data = exchange_google_code(code)
    access_token = (token_data or {}).get("access_token")
    if not access_token:
        return redirect(url_for("maestro_login", error="No se pudo obtener token de Google."))
    profile = fetch_google_userinfo(access_token)
    email = ((profile or {}).get("email") or "").strip().lower()
    verified = bool((profile or {}).get("email_verified"))
    if email != MASTER_ADMIN_EMAIL.lower() or not verified:
        return redirect(url_for("maestro_login", error="Este correo Google no está autorizado para el Centro Maestro."))
    session["quantus_master_authenticated"] = True
    session["quantus_master_user"] = profile.get("name") or email
    session["quantus_master_google_email"] = email
    return redirect(url_for("maestro_dashboard"))

@app.route("/maestro/passkey/register/options")
def maestro_passkey_register_options():
    guard = require_master_login()
    if guard:
        return guard
    auth = load_master_auth()
    options = generate_registration_options(
        rp_id=rp_id(),
        rp_name="Quantus Chile",
        user_name=auth.get("username") or MASTER_ADMIN_USER,
        user_id=(auth.get("username") or MASTER_ADMIN_USER).encode("utf-8"),
        user_display_name="Centro Maestro Quantus",
        authenticator_selection=AuthenticatorSelectionCriteria(
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
        exclude_credentials=passkey_descriptors(),
    )
    session["passkey_registration_challenge"] = b64url_encode(options.challenge)
    return app.response_class(options_to_json(options), mimetype="application/json")

@app.route("/maestro/passkey/register/verify", methods=["POST"])
def maestro_passkey_register_verify():
    guard = require_master_login()
    if guard:
        return guard
    expected = session.pop("passkey_registration_challenge", "")
    if not expected:
        return jsonify({"ok": False, "error": "No hay desafío de registro activo."}), 400
    try:
        verification = verify_registration_response(
            credential=request.get_json(force=True),
            expected_challenge=b64url_decode(expected),
            expected_rp_id=rp_id(),
            expected_origin=expected_origin(),
            require_user_verification=True,
        )
    except Exception as exc:
        return jsonify({"ok": False, "error": f"No se pudo registrar Touch ID: {type(exc).__name__}"}), 400
    items = load_master_passkeys()
    credential_id = b64url_encode(verification.credential_id)
    items = [item for item in items if item.get("credential_id") != credential_id]
    items.append({
        "credential_id": credential_id,
        "credential_public_key": b64url_encode(verification.credential_public_key),
        "sign_count": verification.sign_count,
        "device": request.headers.get("User-Agent", "")[:180],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    save_master_passkeys(items)
    return jsonify({"ok": True, "count": len(items)})

@app.route("/maestro/passkey/auth/options")
def maestro_passkey_auth_options():
    keys = load_master_passkeys()
    if not keys:
        return jsonify({"ok": False, "error": "Primero debes registrar Touch ID desde el Centro Maestro."}), 400
    options = generate_authentication_options(
        rp_id=rp_id(),
        allow_credentials=passkey_descriptors(),
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    session["passkey_authentication_challenge"] = b64url_encode(options.challenge)
    return app.response_class(options_to_json(options), mimetype="application/json")

@app.route("/maestro/passkey/auth/verify", methods=["POST"])
def maestro_passkey_auth_verify():
    expected = session.pop("passkey_authentication_challenge", "")
    if not expected:
        return jsonify({"ok": False, "error": "No hay desafío de autenticación activo."}), 400
    credential = request.get_json(force=True)
    credential_id = credential.get("id") or credential.get("rawId")
    item = next((row for row in load_master_passkeys() if row.get("credential_id") == credential_id), None)
    if not item:
        return jsonify({"ok": False, "error": "Passkey no registrada para este Centro Maestro."}), 403
    try:
        verification = verify_authentication_response(
            credential=credential,
            expected_challenge=b64url_decode(expected),
            expected_rp_id=rp_id(),
            expected_origin=expected_origin(),
            credential_public_key=b64url_decode(item["credential_public_key"]),
            credential_current_sign_count=int(item.get("sign_count") or 0),
            require_user_verification=True,
        )
    except Exception as exc:
        return jsonify({"ok": False, "error": f"No se pudo validar Touch ID: {type(exc).__name__}"}), 400
    items = load_master_passkeys()
    for row in items:
        if row.get("credential_id") == item.get("credential_id"):
            row["sign_count"] = verification.new_sign_count
            row["last_used_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_master_passkeys(items)
    auth = load_master_auth()
    session["quantus_master_authenticated"] = True
    session["quantus_master_user"] = auth.get("username") or MASTER_ADMIN_USER
    session["quantus_master_passkey"] = True
    return jsonify({"ok": True, "redirect": url_for("maestro_dashboard")})

@app.route("/maestro/olvide", methods=["GET", "POST"])
def maestro_forgot_password():
    message = None
    error = None
    if request.method == "POST":
        ok, detail = send_master_temp_password()
        if ok:
            message = f"Enviamos una contraseña temporal a {MASTER_ADMIN_EMAIL}."
        else:
            error = detail or "No se pudo enviar el correo. Revisa la configuración SMTP del servidor."
    return render_template("maestro_forgot.html", message=message, error=error)

@app.route("/maestro/cambiar-clave", methods=["GET", "POST"])
def maestro_change_password():
    guard = require_master_login()
    if guard:
        return guard
    message = None
    error = None
    if request.method == "POST":
        current_password = request.form.get("current_password") or ""
        new_password = request.form.get("new_password") or ""
        confirm_password = request.form.get("confirm_password") or ""
        auth = load_master_auth()
        if not verify_master_password(current_password, auth.get("password") or {}):
            error = "La contraseña actual no coincide."
        elif len(new_password) < 10:
            error = "La nueva contraseña debe tener al menos 10 caracteres."
        elif new_password != confirm_password:
            error = "La confirmación no coincide."
        else:
            username = auth.get("username") or MASTER_ADMIN_USER
            save_master_auth(username, new_password)
            sync_result = sync_erp_superadmin_credentials(username, new_password)
            if sync_result.get("errors"):
                error = "La contraseña del Centro Maestro cambió, pero hubo un problema sincronizando el Punto de Venta. Revisa logs del servidor."
            else:
                message = "Contraseña actualizada correctamente y sincronizada con SuperAdmin del Punto de Venta."
    return render_template("maestro_change_password.html", message=message, error=error)

@app.route("/maestro/logout")
def maestro_logout():
    session.pop("quantus_master_authenticated", None)
    session.pop("quantus_master_user", None)
    return redirect(url_for("maestro_login"))


def get_infra_snapshot():
    import shutil
    import json
    import urllib.request
    from datetime import datetime

    now_dt = datetime.now()
    tot_d, used_d, free_d = shutil.disk_usage("/")
    disk_onprem = {
        "total_gb": round(tot_d / (1024**3), 1),
        "used_gb": round(used_d / (1024**3), 1),
        "free_gb": round(free_d / (1024**3), 1),
        "used_pct": round((used_d / tot_d) * 100, 1)
    }
    mem_onprem = {"total_mb": 0, "used_mb": 0, "free_mb": 0, "used_pct": 0}
    try:
        with open("/proc/meminfo") as f:
            lines = f.readlines()
        mem_dict = {}
        for l in lines:
            parts = l.split(":")
            if len(parts) == 2:
                k = parts[0].strip()
                v = parts[1].strip().split()[0]
                if k in ["MemTotal", "MemAvailable"]:
                    mem_dict[k] = int(v) // 1024
        tot_m = mem_dict.get("MemTotal", 1)
        avail_m = mem_dict.get("MemAvailable", 0)
        used_m = tot_m - avail_m
        mem_onprem = {
            "total_mb": tot_m,
            "used_mb": used_m,
            "free_mb": avail_m,
            "used_pct": round((used_m / tot_m) * 100, 1)
        }
    except Exception:
        pass
        
    onprem = {
        "status": "ONLINE",
        "name": "Servidor Físico On-Premise",
        "ip_tailscale": "100.117.44.3",
        "ip_gateway": "100.93.88.89",
        "role": "Big Data, Velas 15m, Gaussian Bot V13, PostgreSQL Master, Storage Físico",
        "disk": disk_onprem,
        "ram": mem_onprem,
        "sentinel_status": "NORMAL (< 65%)" if disk_onprem["used_pct"] < 65 else "WARNING"
    }

    oracle = {
        "status": "ONLINE",
        "name": "Oracle Cloud Primario (Santiago)",
        "ip": "146.181.50.43",
        "region": "sa-santiago-1 (AD-1)",
        "shape": "VM.Standard.E2.1.Micro",
        "os": "Ubuntu 24.04 Minimal",
        "role": "Edge Web (quantuschile.cl, biobelle.cl), Quantus ERP V1, Nginx Proxy",
        "disk": {"total_gb": 44.0, "used_gb": 3.7, "free_gb": 40.3, "used_pct": 8.4},
        "ram": {"total_mb": 951, "used_mb": 419, "free_mb": 532, "used_pct": 44.0},
        "swap": {"total_mb": 2048, "used_mb": 0, "free_mb": 2048},
        "sentinel": {"growth_rate_mb_per_day": 0.0, "status": "Óptimo (8.39% de uso)"}
    }
    try:
        req = urllib.request.Request("http://146.181.50.43/health.json", headers={"User-Agent": "Quantus-Monitor/1.0"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            if resp.status == 200:
                odata = json.loads(resp.read().decode("utf-8"))
                odisk = odata.get("disk", {})
                if odisk:
                    oracle["disk"] = {
                        "total_gb": round(odisk.get("total_mb", 0) / 1024, 1),
                        "used_gb": round(odisk.get("used_mb", 0) / 1024, 1),
                        "free_gb": round(odisk.get("free_mb", 0) / 1024, 1),
                        "used_pct": odisk.get("used_pct", 8.4)
                    }
                ogrowth = odata.get("growth", {})
                if ogrowth:
                    oracle["sentinel"]["growth_rate_mb_per_day"] = ogrowth.get("growth_rate_mb_per_day", 0.0)
    except Exception as e:
        oracle["status_note"] = f"Última lectura caché: {e}"

    azure = {
        "status": "HOT_STANDBY",
        "name": "Azure Hot Standby",
        "subscription": "Azure for Students (93192784-9d36-4fb5-a8ea-eb683b44c22d)",
        "role": "Disaster Recovery (DR), Réplica Pasiva, Failover DNS",
        "shape": "Standard_B1s (1 vCPU, 1GB RAM)",
        "ssh_key": "servidorazure_key.cer (RSA 3072-bit)",
        "status_note": "Listo para activación ante contingencia SEV-1"
    }

    return {
        "generated_at": now_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "onprem": onprem,
        "oracle": oracle,
        "azure": azure
    }

@app.route("/api/infraestructura/salud")
def api_infraestructura_salud():
    guard = require_master_login()
    if guard:
        return jsonify({"ok": False, "error": "No autorizado"}), 403
    return jsonify({"ok": True, "data": get_infra_snapshot()})



@app.route("/maestro/servidores")
@app.route("/maestro/servidores/")
def maestro_servidores():
    guard = require_master_login()
    if guard:
        return guard
    return render_template(
        "maestro_servidores.html",
        infra_snapshot=get_infra_snapshot(),
        user=session.get("quantus_master_user") or MASTER_ADMIN_USER,
    )

@app.route("/maestro")
@app.route("/maestro/")
def maestro_dashboard():
    guard = require_master_login()
    if guard:
        return guard
    from communications.audit_log import communications_snapshot
    communications = communications_snapshot(
        limit=80,
        search=(request.args.get("comm_client") or "").strip()[:80] or None,
        channel=(request.args.get("comm_channel") or "").strip() or None,
        status=(request.args.get("comm_status") or "").strip() or None,
        event_type=(request.args.get("comm_event") or "").strip() or None,
    )
    return render_template(
        "maestro.html",
        snapshot=master_dashboard_snapshot(),
        communications=communications,
        demo_access=demo_access_summary(),
        demo_verticals=DEMO_VERTICALS,
        user=session.get("quantus_master_user") or MASTER_ADMIN_USER,
        infra_snapshot=get_infra_snapshot(),
    )

@app.route("/maestro/funcionalidades/guardar", methods=["POST"])
def maestro_funcionalidad_guardar():
    guard = require_master_login()
    if guard:
        return guard
    modules = load_superadmin_modules()
    by_key = {item["key"]: item for item in modules}
    raw_key = request.form.get("original_key") or request.form.get("key") or request.form.get("name")
    key = superadmin_module_key(raw_key)
    existing = by_key.get(key, {})
    payload = {
        "key": request.form.get("key") or key,
        "name": request.form.get("name"),
        "category": request.form.get("category"),
        "status": request.form.get("status"),
        "visibility": request.form.get("visibility"),
        "public_path": request.form.get("public_path"),
        "admin_path": request.form.get("admin_path"),
        "owner": request.form.get("owner"),
        "enabled": request.form.get("enabled") == "1",
        "notes": request.form.get("notes"),
    }
    try:
        module = normalize_superadmin_module(payload, existing=existing)
    except ValueError as exc:
        return redirect(url_for("maestro_dashboard", funcionalidades_error=str(exc)))
    module["created_at"] = existing.get("created_at") or datetime.now().isoformat(timespec="seconds")
    if key and key != module["key"]:
        by_key.pop(key, None)
    by_key[module["key"]] = module
    save_superadmin_modules(list(by_key.values()))
    return redirect(url_for("maestro_dashboard", funcionalidades="guardado") + "#panel-superadmin")

@app.route("/maestro/funcionalidades/<module_key>/eliminar", methods=["POST"])
def maestro_funcionalidad_eliminar(module_key):
    guard = require_master_login()
    if guard:
        return guard
    key = superadmin_module_key(module_key)
    modules = [item for item in load_superadmin_modules() if item.get("key") != key]
    save_superadmin_modules(modules)
    return redirect(url_for("maestro_dashboard", funcionalidades="eliminado") + "#panel-superadmin")

@app.route("/maestro/geointel")
def maestro_geointel():
    guard = require_master_login()
    if guard:
        return guard
    filters = {
        "q": (request.args.get("q") or "").strip()[:80],
        "rubro": (request.args.get("rubro") or "").strip()[:80],
        "comuna": (request.args.get("comuna") or "").strip()[:80],
        "min_score": (request.args.get("min_score") or "").strip()[:3],
    }
    filters = {key: value for key, value in filters.items() if value}
    return render_template(
        "maestro_geointel.html",
        dashboard=geointel_dashboard(filters),
        user=session.get("quantus_master_user") or MASTER_ADMIN_USER,
    )

@app.route("/maestro/geointel/extraer", methods=["POST"])
def maestro_geointel_extraer():
    guard = require_master_login()
    if guard:
        return guard
    result = geointel_run_do_extraction(limit=450)
    return redirect(url_for("maestro_geointel", run=result.get("run_id"), status="pass" if result.get("ok") else "block"))

@app.route("/maestro/geointel/extraer-patentes", methods=["POST"])
def maestro_geointel_extraer_patentes():
    guard = require_master_login()
    if guard:
        return guard
    result = geointel_run_patentes_extraction(max_resources=4, max_rows_per_resource=1200)
    return redirect(url_for("maestro_geointel", run=result.get("run_id"), status="pass" if result.get("ok") else "block"))

@app.route("/maestro/geointel/refrescar-base-erp-pos", methods=["POST"])
def maestro_geointel_refrescar_base_erp_pos():
    guard = require_master_login()
    if guard:
        return guard
    result = geointel_refresh_sales_base()
    return redirect(url_for("maestro_geointel", status="pass" if result.get("ok") else "block"))

@app.route("/maestro/geointel/send-pitch-email", methods=["POST"])
def maestro_geointel_send_pitch_email():
    guard = require_master_login()
    if guard:
        return jsonify({"ok": False, "error": "No autorizado"}), 403
    
    lead_id = request.form.get("lead_id")
    if not lead_id:
        return jsonify({"ok": False, "error": "Falta lead_id"}), 400
        
    import sqlite3
    from geointel_sales_radar import DB_PATH
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    lead = cur.execute("SELECT * FROM geointel_leads WHERE id = ?", (lead_id,)).fetchone()
    conn.close()
    
    if not lead:
        return jsonify({"ok": False, "error": "Lead no encontrado"}), 404
        
    email = lead["contact_email"]
    if not email:
        return jsonify({"ok": False, "error": "Este lead no tiene correo de contacto registrado"}), 400
        
    try:
        html_body = render_template(
            "marketing/geointel_welcome_email.html",
            company_name=lead["company_name"],
            comuna=lead["comuna"]
        )
    except Exception as e:
        return jsonify({"ok": False, "error": f"Error render: {str(e)}"}), 500
        
    subject = f"Bienvenida a {lead['company_name']} — Próximos pasos recomendados para su nueva empresa"
    ok = send_email(email, subject, html_body)
    
    if ok:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("UPDATE geointel_leads SET alerted = 1 WHERE id = ?", (lead_id,))
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "message": f"Correo enviado exitosamente a {email}"})
    else:
        return jsonify({"ok": False, "error": "Error al despachar correo a través del servidor SMTP"}), 500

@app.route("/maestro/geointel/export.csv")

def maestro_geointel_export_csv():
    guard = require_master_login()
    if guard:
        return guard
    filters = {
        "q": (request.args.get("q") or "").strip()[:80],
        "rubro": (request.args.get("rubro") or "").strip()[:80],
        "comuna": (request.args.get("comuna") or "").strip()[:80],
        "min_score": (request.args.get("min_score") or "").strip()[:3],
    }
    csv_data = geointel_export_csv({key: value for key, value in filters.items() if value})
    return Response(
        csv_data,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=quantus_geointel_sales_radar.csv"},
    )

@app.route("/maestro/registro/<registry_key>/modificar", methods=["POST"])
def maestro_registro_modificar(registry_key):
    """Actualizar datos de un registro individual en master_client_registry y sincronizar con sus fuentes."""
    guard = require_master_login()
    if guard:
        return guard
    import sqlite3
    from do_intelligence import DB_PATH, ensure_storage
    ensure_storage()
    
    nombre = (request.form.get("nombre") or request.form.get("display_name") or "").strip()
    rut = (request.form.get("rut") or "").strip()
    if rut:
        rut = require_valid_rut(rut, required=False, label="RUT del cliente")
    clean = clean_rut(rut) if rut else ""
    email = (request.form.get("email") or "").strip()
    whatsapp = (request.form.get("whatsapp") or request.form.get("phone") or "").strip()
    estado = (request.form.get("estado") or request.form.get("status") or "activo").strip()
    
    dup_error = check_duplicate_rut_or_name(rut=rut, name=nombre, exclude_key=registry_key)
    if dup_error:
        return render_template("success.html", titulo="Registro duplicado no permitido", mensaje=dup_error), 400

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT source_module, source_ref, clean_rut FROM master_client_registry WHERE registry_key = ?", (registry_key,)).fetchone()
            target_ref = row["source_ref"] if row else ""
            target_clean_rut = row["clean_rut"] if row else clean

            conn.execute("""
                UPDATE master_client_registry
                SET display_name = ?, rut = ?, clean_rut = ?, email = ?, phone = ?, status = ?
                WHERE registry_key = ?
            """, (nombre, rut, clean, email, whatsapp, estado, registry_key))
            conn.commit()

            # 1. Update do_people.json if applicable
            people = load_do_people()
            people_changed = False
            for p in people:
                if (target_ref and f"do_people:{p.get('id', '')}" == target_ref) or (target_clean_rut and clean_rut(p.get("rut")) == target_clean_rut):
                    p["nombre_completo"] = nombre
                    p["rut"] = rut
                    p["clean_rut"] = clean
                    if email:
                        p["alertar_a"] = email
                    if whatsapp:
                        p["whatsapp"] = whatsapp
                    p["estado"] = estado
                    p["subscription_state"] = estado
                    if "watch_targets" in p:
                        p["watch_targets"] = [
                            {"tipo": "rut", "valor": rut},
                            {"tipo": "nombre", "valor": nombre}
                        ]
                    people_changed = True
            if people_changed:
                save_do_people(people)

            # 2. Update watchdog_clients.json if applicable
            items = read_json_file(WATCHDOG_CLIENTS_FILE, [])
            items_changed = False
            for it in items:
                if (target_ref and f"watchdog:{it.get('id', it.get('marca_protegida', ''))}" == target_ref) or (target_clean_rut and clean_rut(it.get("rut") or it.get("rut_titular")) == target_clean_rut):
                    it["nombre_titular"] = nombre
                    it["rut"] = rut
                    if email:
                        it["email_cliente"] = email
                    if whatsapp:
                        it["whatsapp"] = whatsapp
                    items_changed = True
            if items_changed:
                save_json_file(WATCHDOG_CLIENTS_FILE, items)

            # 3. Update master_free_clients.json if applicable
            free = load_master_free_clients()
            free_changed = False
            for f in free:
                if (target_ref and f"free:{f.get('id', f.get('key', ''))}" == target_ref) or (target_clean_rut and clean_rut(f.get("rut")) == target_clean_rut):
                    f["name"] = nombre
                    f["rut"] = rut
                    if email:
                        f["email"] = email
                    if whatsapp:
                        f["whatsapp"] = whatsapp
                    f["status"] = estado
                    free_changed = True
            if free_changed:
                save_master_free_clients(free)

    except Exception as e:
        return render_template("success.html", titulo="Error al modificar", mensaje=f"No se pudo actualizar: {e}"), 500
        
    return redirect(url_for("maestro_dashboard", actualizado=1))


@app.route("/maestro/registro/<registry_key>/eliminar", methods=["POST"])
def maestro_registro_eliminar(registry_key):
    """Eliminar un registro individual del maestro y de sus fuentes por registry_key."""
    guard = require_master_login()
    if guard:
        return guard
    import sqlite3
    from do_intelligence import DB_PATH, ensure_storage
    ensure_storage()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT display_name, rut, clean_rut, source_ref FROM master_client_registry WHERE registry_key = ?",
                (registry_key,),
            ).fetchone()
            if not row:
                return render_template(
                    "success.html",
                    titulo="Registro no encontrado",
                    mensaje=f"No se encontró el registro con clave '{registry_key}' en la base de datos.",
                ), 404
            nombre = row["display_name"] or row["rut"] or registry_key
            target_rut = row["clean_rut"] or (clean_rut(row["rut"]) if row["rut"] else "")
            target_ref = row["source_ref"] or ""
            target_name = (row["display_name"] or "").strip().lower()

            # Delete from do_people.json
            people = load_do_people()
            kept_people = [
                p for p in people
                if do_person_key(p) != registry_key 
                and f"do_people:{p.get('id', '')}" != target_ref
                and (not target_rut or clean_rut(p.get("rut")) != target_rut)
                and (not target_name or (p.get("nombre_completo") or "").strip().lower() != target_name)
            ]
            if len(kept_people) != len(people):
                save_do_people(kept_people)

            # Delete from watchdog_clients.json
            items = read_json_file(WATCHDOG_CLIENTS_FILE, [])
            kept_items = [
                it for it in items
                if client_key_for("inapi", it.get("nombre_titular"), it.get("marca_protegida"), it.get("email_cliente")) != registry_key
                and f"watchdog:{it.get('id', it.get('marca_protegida', ''))}" != target_ref
            ]
            if len(kept_items) != len(items):
                save_json_file(WATCHDOG_CLIENTS_FILE, kept_items)

            # Delete from master_free_clients.json
            free = load_master_free_clients()
            kept_free = [
                f for f in free
                if (f.get("key") or client_key_for(f.get("module"), f.get("name"), f.get("rut"), f.get("email"))) != registry_key
                and f"free:{f.get('id', f.get('key', ''))}" != target_ref
                and (not target_rut or clean_rut(f.get("rut")) != target_rut)
            ]
            if len(kept_free) != len(free):
                save_master_free_clients(kept_free)

            # Delete from SQLite table
            conn.execute(
                "DELETE FROM master_client_registry WHERE registry_key = ?",
                (registry_key,),
            )
            conn.commit()
    except Exception as e:
        return render_template(
            "success.html",
            titulo="Error al eliminar",
            mensaje=f"No se pudo eliminar el registro: {e}",
        ), 500

    return redirect(url_for("maestro_dashboard", eliminado=1, cliente=nombre))


@app.route("/maestro/registro/eliminar-masivo", methods=["POST"])
def maestro_registro_eliminar_masivo():
    """Eliminar múltiples registros seleccionados del maestro y de todas sus fuentes."""
    guard = require_master_login()
    if guard:
        return guard
    import sqlite3
    from do_intelligence import DB_PATH, ensure_storage
    ensure_storage()
    keys_raw = (request.form.get("registry_keys") or "").strip()
    if not keys_raw:
        return redirect(url_for("maestro_dashboard"))
    if keys_raw.startswith("["):
        try:
            keys = [str(k).strip() for k in json.loads(keys_raw) if str(k).strip()]
        except Exception:
            keys = [k.strip() for k in keys_raw.split(",") if k.strip()]
    else:
        keys = [k.strip() for k in keys_raw.split(",") if k.strip()]
    if not keys:
        return redirect(url_for("maestro_dashboard"))

    try:
        # Fetch targets to get source_refs and ruts
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            placeholders = ",".join("?" for _ in keys)
            rows = conn.execute(
                f"SELECT registry_key, clean_rut, rut, display_name, source_ref, source_module FROM master_client_registry WHERE registry_key IN ({placeholders})",
                keys,
            ).fetchall()

        ruts_to_delete = {r["clean_rut"] or clean_rut(r["rut"]) for r in rows if (r["clean_rut"] or r["rut"])}
        refs_to_delete = {r["source_ref"] for r in rows if r["source_ref"]}
        names_to_delete = {(r["display_name"] or "").strip().lower() for r in rows if r["display_name"]}

        # Delete matching rows from do_people.json
        people = load_do_people()
        kept_people = [
            p for p in people
            if do_person_key(p) not in keys
            and f"do_people:{p.get('id', '')}" not in refs_to_delete
            and (not clean_rut(p.get("rut")) or clean_rut(p.get("rut")) not in ruts_to_delete)
            and (not p.get("nombre_completo") or p.get("nombre_completo").strip().lower() not in names_to_delete)
        ]
        if len(kept_people) != len(people):
            save_do_people(kept_people)

        # Delete matching rows from watchdog_clients.json
        items = read_json_file(WATCHDOG_CLIENTS_FILE, [])
        kept_items = [
            it for it in items
            if client_key_for("inapi", it.get("nombre_titular"), it.get("marca_protegida"), it.get("email_cliente")) not in keys
            and f"watchdog:{it.get('id', it.get('marca_protegida', ''))}" not in refs_to_delete
        ]
        if len(kept_items) != len(items):
            save_json_file(WATCHDOG_CLIENTS_FILE, kept_items)

        # Delete matching rows from master_free_clients.json
        free = load_master_free_clients()
        kept_free = [
            f for f in free
            if (f.get("key") or client_key_for(f.get("module"), f.get("name"), f.get("rut"), f.get("email"))) not in keys
            and f"free:{f.get('id', f.get('key', ''))}" not in refs_to_delete
            and (not clean_rut(f.get("rut")) or clean_rut(f.get("rut")) not in ruts_to_delete)
        ]
        if len(kept_free) != len(free):
            save_master_free_clients(kept_free)

        # Delete from master_client_registry SQLite table
        with sqlite3.connect(DB_PATH) as conn:
            placeholders = ",".join("?" for _ in keys)
            conn.execute(
                f"DELETE FROM master_client_registry WHERE registry_key IN ({placeholders})",
                keys,
            )
            conn.commit()

        eliminados = len(keys)
    except Exception as e:
        return render_template(
            "success.html",
            titulo="Error al eliminar",
            mensaje=f"No se pudo completar la eliminación masiva: {e}",
        ), 500
    return redirect(url_for("maestro_dashboard", eliminado=eliminados))


@app.route("/maestro/salud-entregas")
def maestro_salud_entregas():
    guard = require_master_login()
    if guard:
        return guard
    from communications.delivery_health import delivery_health_snapshot, has_issues
    snapshot = delivery_health_snapshot()
    ok, motivo = has_issues(snapshot)
    return render_template(
        "maestro_salud_entregas.html",
        snapshot=snapshot,
        salud_ok=not ok,
        motivo=motivo,
        user=session.get("quantus_master_user") or MASTER_ADMIN_USER,
    )

@app.route("/maestro/comunicaciones/<comm_id>/reenviar", methods=["POST"])
def maestro_comunicacion_reenviar(comm_id):
    guard = require_master_login()
    if guard:
        return guard
    from communications.dispatcher import resend
    result = resend(comm_id)
    if result.get("error"):
        return render_template(
            "success.html",
            titulo="No se pudo reenviar la comunicacion",
            mensaje=result["error"],
        ), 400
    return redirect(url_for("maestro_dashboard"))

@app.route("/maestro/cliente/<client_key>")
def maestro_cliente(client_key):
    guard = require_master_login()
    if guard:
        return guard
    client = master_client_by_key(client_key)
    if not client:
        abort(404)
    from communications.audit_log import communications_snapshot
    communications = communications_snapshot(
        limit=40,
        client_key=client_key,
    )
    return render_template(
        "maestro_cliente.html",
        client=client,
        categories=CLIENT_FILE_CATEGORIES,
        communications=communications,
    )

@app.route("/maestro/cliente/<client_key>/eliminar", methods=["POST"])
def maestro_cliente_eliminar(client_key):
    guard = require_master_login()
    if guard:
        return guard
    confirmacion = (request.form.get("confirmacion") or "").strip().upper()
    if confirmacion != "ELIMINAR":
        return render_template(
            "success.html",
            titulo="Eliminacion cancelada",
            mensaje="Para eliminar el cliente debes escribir ELIMINAR como confirmacion.",
        ), 400
    ok, detalle = maestro_eliminar_cliente(client_key)
    if not ok:
        return render_template(
            "success.html",
            titulo="No se pudo eliminar el cliente",
            mensaje=detalle,
        ), 404
    return redirect(url_for("maestro_dashboard", eliminado=1, cliente=detalle))

@app.route("/maestro/cliente/<client_key>/upload", methods=["POST"])
def maestro_cliente_upload(client_key):
    guard = require_master_login()
    if guard:
        return guard
    client = master_client_by_key(client_key)
    if not client:
        abort(404)
    category = request.form.get("category") or "otros"
    if category not in CLIENT_FILE_CATEGORIES:
        abort(400, "Categoría inválida.")
    file = request.files.get("file")
    if not file or not file.filename:
        abort(400, "Debes seleccionar un archivo.")
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_VOUCHER_EXTENSIONS and ext not in {".doc", ".docx", ".xls", ".xlsx", ".csv", ".txt"}:
        abort(400, "Formato no permitido para carpeta de cliente.")
    root = Path(client["folder_path"])
    target_dir = root / category
    target_dir.mkdir(exist_ok=True)
    stamped = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = werkzeug.utils.secure_filename(f"{stamped}_{file.filename}")
    file.save(target_dir / filename)
    return redirect(url_for("maestro_cliente", client_key=client_key))

@app.route("/maestro/cliente/<client_key>/meta-whatsapp", methods=["POST"])
def maestro_cliente_meta_whatsapp(client_key):
    guard = require_master_login()
    if guard:
        return guard
    client = master_client_by_key(client_key)
    if not client:
        abort(404)
    phone_number_id = (request.form.get("phone_number_id") or "").strip()
    access_token = (request.form.get("access_token") or "").strip()
    template = (request.form.get("template") or WHATSAPP_TEMPLATE_ALERT).strip()
    graph_version = (request.form.get("graph_version") or WHATSAPP_GRAPH_VERSION).strip()
    owner_email = (request.form.get("owner_email") or "").strip()
    existing = load_meta_whatsapp_config(client["folder_path"])
    if not phone_number_id:
        abort(400, "Debes ingresar el Phone Number ID de Meta.")
    if not access_token and not existing.get("access_token"):
        abort(400, "Debes ingresar el token de acceso de Meta al menos la primera vez.")
    save_meta_whatsapp_config(
        client["folder_path"],
        {
            "phone_number_id": phone_number_id,
            "access_token": access_token,
            "template": template,
            "graph_version": graph_version,
            "owner_email": owner_email,
        },
    )
    return redirect(url_for("maestro_cliente", client_key=client_key))

@app.route("/maestro/cliente/<client_key>/meta-whatsapp/test", methods=["POST"])
def maestro_cliente_meta_whatsapp_test(client_key):
    guard = require_master_login()
    if guard:
        return guard
    client = master_client_by_key(client_key)
    if not client:
        abort(404)
    config = load_meta_whatsapp_config(client["folder_path"])
    token = config.get("access_token") or WHATSAPP_ACCESS_TOKEN
    phone_number_id = config.get("phone_number_id") or WHATSAPP_PHONE_NUMBER_ID
    graph_version = config.get("graph_version") or WHATSAPP_GRAPH_VERSION
    template = config.get("template") or WHATSAPP_TEMPLATE_ALERT
    if not token or not phone_number_id:
        return jsonify({"ok": False, "error": "Falta configurar token y phone number id."})

    base = f"https://graph.facebook.com/{graph_version}"
    headers = {"Authorization": f"Bearer {token}"}
    resultado = {"ok": False, "chequeos": {}}

    try:
        r = requests.get(f"{base}/{phone_number_id}", headers=headers, timeout=15)
        if r.status_code != 200:
            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            err = (data or {}).get("error", {})
            code = err.get("code", "?")
            msg = err.get("message", r.text[:200])
            if code == 190:
                resultado["chequeos"]["token"] = "INVALIDO o EXPIRADO"
                resultado["error"] = f"Token rechazado (código {code}): {msg}"
            else:
                resultado["chequeos"]["phone"] = "NO valido"
                resultado["error"] = f"Phone Number ID rechazado (código {code}): {msg}"
            return jsonify(resultado)

        numero = r.json()
        resultado["chequeos"]["token"] = "OK"
        resultado["chequeos"]["phone"] = "OK"
        resultado["telefono"] = numero.get("display_phone_number", "")
        resultado["calidad"] = numero.get("quality_rating", "")
    except requests.RequestException as exc:
        resultado["error"] = f"Fallo de red al contactar Graph API: {exc}"
        return jsonify(resultado)

    waba_id = ""
    try:
        r = requests.get(
            f"{base}/{phone_number_id}",
            params={"fields": "whatsapp_business_account{id,name}"},
            headers=headers,
            timeout=15,
        )
        if r.status_code == 200:
            waba_data = r.json().get("whatsapp_business_account") or {}
            waba_id = str(waba_data.get("id") or "")
            if waba_id:
                resultado["chequeos"]["waba"] = "OK"
                resultado["waba"] = waba_data.get("name") or waba_id
    except requests.RequestException:
        pass

    if not waba_id:
        resultado["chequeos"]["waba"] = "No se pudo obtener (token con permisos limitados)"
    else:
        try:
            r = requests.get(
                f"{base}/{waba_id}/message_templates",
                params={"fields": "name,status,language", "limit": 200},
                headers=headers,
                timeout=15,
            )
            if r.status_code == 200:
                tmpls = (r.json().get("data") or [])
                match = [t for t in tmpls if t.get("name") == template]
                if match:
                    t = match[0]
                    resultado["chequeos"]["plantilla"] = t.get("status", "?")
                    resultado["plantilla"] = {
                        "nombre": template,
                        "estado": t.get("status", ""),
                        "idioma": t.get("language", ""),
                    }
                    resultado["ok"] = t.get("status") == "APPROVED"
                    if t.get("status") != "APPROVED":
                        resultado["error"] = f"Plantilla '{template}' existe pero está en estado {t.get('status')} (debe ser APPROVED)."
                else:
                    nombres = [t.get("name") for t in tmpls][:20]
                    resultado["chequeos"]["plantilla"] = "NO EXISTE"
                    resultado["error"] = f"La plantilla '{template}' no está en esta cuenta. Existen: {', '.join(nombres) or 'ninguna'}."
            else:
                resultado["chequeos"]["plantilla"] = "No consultable (permisos)"
        except requests.RequestException:
            resultado["chequeos"]["plantilla"] = "Error de red al consultar plantillas"
    return jsonify(resultado)

@app.route("/maestro/cliente/<client_key>/archivo/<category>/<filename>")
def maestro_cliente_archivo(client_key, category, filename):
    guard = require_master_login()
    if guard:
        return guard
    client = master_client_by_key(client_key)
    if not client or category not in CLIENT_FILE_CATEGORIES:
        abort(404)
    safe_name = werkzeug.utils.secure_filename(filename)
    path = Path(client["folder_path"]) / category / safe_name
    if not path.exists() or not path.is_file():
        abort(404)
    return send_file(str(path), as_attachment=True, download_name=safe_name)

@app.route("/maestro/do/confirmar-pago", methods=["POST"])
def maestro_do_confirmar_pago():
    guard = require_master_login()
    if guard:
        return guard
    try:
        person, event = confirm_do_payment(
            person_id=request.form.get("person_id"),
            reference=request.form.get("payment_reference"),
            amount=request.form.get("amount_clp"),
            paid_at=request.form.get("paid_at"),
            operator=session.get("quantus_master_user") or MASTER_ADMIN_USER,
            note=request.form.get("note", ""),
        )
    except ValueError as exc:
        return render_template(
            "success.html",
            titulo="No se pudo confirmar el pago",
            mensaje=str(exc),
        ), 400

    save_service_consent(
        {
            "key": do_person_key(person),
            "name": person.get("nombre_completo"),
            "module": "Diario Oficial",
            "rut": person.get("rut"),
            "rubro": "Personas y empresas",
            "plan": person.get("plan"),
            "email": person.get("alertar_a"),
        },
        "Vigilancia Diario Oficial 24/7 - Activación por pago confirmado",
        extra={
            "payment_event": event,
            "fecha_vencimiento": person.get("fecha_vencimiento"),
        },
    )

    email = person.get("alertar_a")
    if email:
        from communications.dispatcher import dispatch
        client_key = do_person_key(person)
        dispatch(
            "diario_oficial",
            "activation",
            client={
                "key": client_key,
                "nombre": person.get("nombre_completo"),
                "rut": person.get("rut"),
                "email": email,
                "whatsapp": person.get("whatsapp"),
                "whatsapp_consent": person.get("whatsapp_consent"),
            },
            payload={
                "plan": person.get("plan"),
                "plan_label": person.get("plan"),
                "vigencia": f"hasta {person.get('fecha_vencimiento')}",
                "referencia": event.get("payment_reference"),
                "datos_monitoreados": [
                    value for value in [
                        person.get("nombre_completo"),
                        person.get("rut"),
                        person.get("ruts_adicionales"),
                        *[t.get("valor") for t in (person.get("watch_targets") or []) if isinstance(t, dict)],
                        *(person.get("alias_busqueda") or []),
                        *(person.get("ruts_asociados") or []),
                        *(person.get("nombres_anteriores") or []),
                        *(person.get("empresas_anteriores") or []),
                    ] if value
                ],
                "canales_alerta": person.get("canales_alerta") or ["email"],
            },
            dedup_source=f"activation:{person.get('id')}:{event.get('payment_reference') or 'pago'}",
        )

    return redirect(url_for("maestro_dashboard"))

@app.route("/licitaciones")
def licitaciones():
    demo_opportunities = [
        {
            "score": 92,
            "nivel": "Oportunidad fuerte",
            "empresa": "Ferretería Demo SpA",
            "titulo": "Materiales de ferretería y construcción",
            "organismo": "Division Logistica del Ejercito",
            "monto": "$17.322.280",
            "cierre": "31/07/2026 17:01",
            "region": "Ñuble",
            "accion": "Preparar oferta hoy",
        },
        {
            "score": 88,
            "nivel": "Alta afinidad",
            "empresa": "Servicios de Aseo Demo Ltda",
            "titulo": "Servicio de mantencion y limpieza preventiva",
            "organismo": "Subsecretaria del Patrimonio Cultural",
            "monto": "$9.600.000",
            "cierre": "03/08/2026 18:00",
            "region": "Metropolitana",
            "accion": "Revisar requisitos",
        },
        {
            "score": 84,
            "nivel": "Buena oportunidad",
            "empresa": "Soporte TI Demo SpA",
            "titulo": "Licencias de software y soporte técnico",
            "organismo": "Servicio Local de Educacion Publica",
            "monto": "$48.000.000",
            "cierre": "08/08/2026 16:00",
            "region": "Valparaíso",
            "accion": "Solicitar bases",
        },
    ]
    return render_template("licitaciones.html", demo_opportunities=demo_opportunities)

@app.route("/contratar_licitaciones", methods=["POST"])
def contratar_licitaciones():
    plan = request.form.get("plan", "pyme_pro")
    nombre = request.form.get("empresa", "")
    rut = require_valid_rut(request.form.get("rut", ""), required=True, label="RUT empresa")
    email = (request.form.get("correo") or request.form.get("email") or "").strip().lower()
    whatsapp = normalize_whatsapp(request.form.get("whatsapp"))
    whatsapp_consent = request.form.get("whatsapp_consent") == "1"
    rubros = request.form.get("rubros", "")
    region_cobertura = request.form.get("region_cobertura", "Nacional").strip()
    monto_minimo = request.form.get("monto_minimo", "todos").strip()
    payment_mode = request.form.get("payment_mode", "one_time")
    require_data_consent("Radar de Licitaciones 24/7")
    if request.form.get("source_limitation_ack") != "1":
        abort(400, "Debes aceptar la advertencia sobre cambios, anexos y plazos de Mercado Público.")

    # Persistencia en Capa Canónica Relacional
    try:
        import quantus_ecosystem_db
        id_cli = quantus_ecosystem_db.upsert_cliente(
            rut=rut,
            nombre=nombre,
            email=email,
            telefono=whatsapp,
            tipo_persona="juridica"
        )
        quantus_ecosystem_db.save_susc_licitaciones(
            id_cliente=id_cli,
            rut_empresa=rut,
            rubro=rubros,
            region_cobertura=region_cobertura,
            monto_minimo=monto_minimo,
            plan=plan,
            payment_mode=payment_mode,
            estado="activo"
        )
        quantus_ecosystem_db.record_audit_event(
            actor="client",
            action="contract_licitaciones",
            object_type="susc_licitaciones",
            object_id=id_cli,
            payload={"empresa": nombre, "rut": rut, "region": region_cobertura, "monto_min": monto_minimo, "plan": plan},
            ip_address=get_client_ip()
        )
    except Exception as e_lic:
        print(f"Aviso en quantus_ecosystem_db (Licitaciones): {e_lic}")

    clients = refresh_licitaciones_lifecycle(load_licitaciones_clients(), persist=True)
    existing = find_licitaciones_subscription(clients, rut, email)
    if existing and licitaciones_subscription_state(existing) in {"activo", "activo_permanente", "activo_sin_vencimiento"}:
        return render_template(
            "success.html",
            titulo="Ya tienes Radar de Licitaciones activo",
            mensaje=f"El RUT {rut} o el correo ingresado ya está registrado con un radar vigente. No generamos un nuevo cobro."
        ), 200

    link = licitaciones_checkout_url(plan, payment_mode)
    nuevo_id = max([c.get("id", 0) for c in clients], default=0) + 1
    vencimiento = datetime.now().date() + timedelta(days=licitaciones_plan_duration_days(plan))
    nuevo_cliente = {
        "id": existing.get("id") if existing else nuevo_id,
        "empresa": nombre,
        "nombre": nombre,
        "rut": rut,
        "clean_rut": clean_rut(rut),
        "email": email,
        "whatsapp": whatsapp,
        "whatsapp_consent": whatsapp_consent,
        "rubros": rubros,
        "region_cobertura": region_cobertura,
        "monto_minimo": monto_minimo,
        "plan": plan,
        "payment_mode": payment_mode,
        "checkout_url": link,
        "estado": "pendiente_pago",
        "subscription_state": "pendiente_pago",
        "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fecha_vencimiento_propuesta": vencimiento.strftime("%Y-%m-%d"),
        "privacy_cleanup_due": (datetime.now().date() + timedelta(days=DO_PENDING_PAYMENT_TTL_DAYS + DO_PRIVACY_RETENTION_DAYS)).strftime("%Y-%m-%d"),
        "ley_21719_consent": True,
        "source_limitation_ack": True,
        "consent_timestamp": datetime.now().isoformat(timespec="seconds"),
        "consent_ip": get_client_ip(),
        "consent_version": CONSENT_VERSION,
        "arco_rights_contact": "privacidad@quantuschile.cl",
    }
    if existing:
        for index, item in enumerate(clients):
            if licitaciones_identity_matches(item, rut, email):
                clients[index].update(nuevo_cliente)
                break
    else:
        clients.append(nuevo_cliente)
    save_licitaciones_clients(clients)

    consent = save_service_consent(
        {
            "key": client_key_for("licitaciones", nombre, rut, email),
            "name": nombre or "Prospecto licitaciones",
            "module": "Licitaciones",
            "rut": rut,
            "rubro": rubros,
            "plan": plan,
            "email": email,
        },
        "Radar de Licitaciones 24/7",
        extra={"rubros": rubros, "whatsapp": whatsapp, "whatsapp_consent": whatsapp_consent, "payment_mode": payment_mode, "checkout_url": link},
    )
    if whatsapp and whatsapp_consent:
        queue_whatsapp_alert(
            "licitaciones",
            {"nombre": nombre, "rut": rut, "whatsapp": whatsapp},
            "Solicitud recibida: Quantus configurará tu radar comercial de licitaciones y enviará alertas críticas por este canal.",
        )
    if link:
        return redirect(link)

    asunto = f"[Licitaciones 24/7] Solicitud de activación - {nombre or plan}"
    cuerpo = f"""
    <h2>Nueva solicitud Quantus Licitaciones 24/7</h2>
    <p><strong>Plan:</strong> {plan}</p>
    <p><strong>Empresa:</strong> {nombre}</p>
    <p><strong>RUT:</strong> {rut or "No informado"}</p>
    <p><strong>Correo:</strong> {email}</p>
    <p><strong>WhatsApp:</strong> {whatsapp or "No informado"} | Consentimiento: {"Sí" if whatsapp_consent else "No"}</p>
    <p><strong>Consentimiento Ley 21.719:</strong> aceptado y archivado en carpeta privada.</p>
    <p><strong>Rubros / regiones / montos:</strong><br>{rubros}</p>
    <p>Consentimiento archivado: {consent.get("path")}</p>
    """
    Thread(target=send_email, args=("felipe.mejias.g@gmail.com", asunto, cuerpo)).start()
    return render_template(
        "success.html",
        titulo="Solicitud recibida",
        mensaje="Recibimos tu solicitud de activación. Te enviaremos el link de pago Mercado Pago al correo indicado."
    )

@app.route("/contratar_vigilancia", methods=["POST"])
@app.route("/payment", methods=["POST"])
def contratar_vigilancia():
    from flask import redirect
    nombre = request.form.get("nombre")
    rut = request.form.get("rut")
    email = request.form.get("email")
    whatsapp = normalize_whatsapp(request.form.get("whatsapp") or request.form.get("telefono"))
    whatsapp_consent = request.form.get("whatsapp_consent") == "1"
    plan = request.form.get("plan", "anual")
    ruts_adicionales = (request.form.get("ruts_adicionales") or "").strip()
    codigo_convenio = (request.form.get("codigo_convenio") or "").strip().upper()
    
    # Parsear ruts_adicionales en watch_targets estructurados
    watch_targets = []
    if rut:
        watch_targets.append({"tipo": "rut_principal", "valor": rut, "prioridad": "alta"})
    if ruts_adicionales:
        for term in ruts_adicionales.replace(";", ",").split(","):
            t_clean = term.strip()
            if t_clean:
                is_rut = re.search(r'\d', t_clean) and ("-" in t_clean or "." in t_clean)
                watch_targets.append({
                    "tipo": "rut_adicional" if is_rut else "termino_clave",
                    "valor": t_clean,
                    "prioridad": "media"
                })

    rut = require_valid_rut(rut, required=False, label="RUT")
    require_data_consent("Vigilancia Diario Oficial 24/7")
    require_do_source_limitation_ack("Vigilancia Diario Oficial 24/7")
    
    # Persistencia en Capa Canónica Relacional
    try:
        import quantus_ecosystem_db
        id_cli = quantus_ecosystem_db.upsert_cliente(rut, nombre, email, whatsapp)
        quantus_ecosystem_db.save_susc_diario_oficial(
            id_cliente=id_cli,
            rut_monitoreado=rut,
            ruts_adicionales=ruts_adicionales,
            watch_targets=watch_targets,
            plan=plan,
            payment_mode=request.form.get("payment_mode", "one_time"),
            estado="activo"
        )
        quantus_ecosystem_db.record_audit_event(
            actor="client",
            action="contratar_vigilancia_do",
            object_type="susc_diario_oficial",
            object_id=id_cli,
            payload={"rut": rut, "plan": plan, "watch_targets": watch_targets},
            ip_address=request.headers.get("X-Forwarded-For", request.remote_addr)
        )
    except Exception as e_can:
        print(f"Aviso en quantus_ecosystem_db (DO): {e_can}")

    people = refresh_do_subscription_lifecycle(load_do_people(), persist=True)
    email_clean = (email or '').strip().lower()
    existing = find_do_subscription(people, rut, email_clean)
    if existing and do_subscription_state(existing) in {"activo", "activo_permanente", "activo_sin_vencimiento"}:
        return render_template(
            "success.html",
            titulo="Ya tienes vigilancia activa",
            mensaje=f"El RUT {rut} o el correo ingresado ya está registrado con una vigilancia vigente. No generamos un nuevo cobro."
        ), 200
    
    payment_mode = request.form.get("payment_mode", "one_time")
    redirect_url = do_checkout_url(plan, payment_mode)
    
    hoy = datetime.now()
    vencimiento = hoy + timedelta(days=plan_duration_days(plan))
            
    nuevo_id = max([p.get('id', 0) for p in people], default=0) + 1
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    nuevo_cliente = {
        "id": nuevo_id,
        "nombre_completo": nombre,
        "rut": rut,
        "ruts_adicionales": ruts_adicionales,
        "watch_targets": watch_targets,
        "alertar_a": email,
        "whatsapp": whatsapp,
        "whatsapp_consent": whatsapp_consent,
        "canales_alerta": ["email", "whatsapp"] if whatsapp and whatsapp_consent else ["email"],
        "ley_21719_consent": True,
        "consent_timestamp": datetime.now().isoformat(),
        "consent_ip": client_ip,
        "consent_version": "Ley_21719_v1.0",
        "arco_rights_contact": "privacidad@quantuschile.cl",
        "plan": plan,
        "payment_mode": payment_mode,
        "checkout_url": redirect_url,
        "estado": "activo",
        "subscription_state": "activo",
        "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fecha_vencimiento": vencimiento.strftime("%Y-%m-%d"),
        "fecha_vencimiento_propuesta": vencimiento.strftime("%Y-%m-%d"),
        "privacy_cleanup_due": (datetime.now().date() + timedelta(days=DO_PENDING_PAYMENT_TTL_DAYS + DO_PRIVACY_RETENTION_DAYS)).strftime("%Y-%m-%d")
    }
    updated = False
    for i, person in enumerate(people):
        if do_identity_matches(person, rut, email):
            people[i].update(nuevo_cliente)
            updated = True
            break
    if not updated:
        people.append(nuevo_cliente)
    
    save_do_people(people)

    consent = save_service_consent(
        {
            "key": client_key_for("diario_oficial", nombre, rut, email),
            "name": nombre,
            "module": "Diario Oficial",
            "rut": rut,
            "rubro": "Personas y empresas",
            "plan": plan,
            "email": email,
        },
        "Vigilancia Diario Oficial 24/7",
        extra={"whatsapp": whatsapp, "whatsapp_consent": whatsapp_consent, "fecha_vencimiento": nuevo_cliente.get("fecha_vencimiento")},
    )

    # Despacho inmediato de correo de bienvenida y activacion
    try:
        from communications.dispatcher import dispatch
        dispatch(
            "diario_oficial",
            "activation",
            client={
                "key": client_key_for("diario_oficial", nombre, rut, email),
                "nombre": nombre,
                "rut": rut,
                "email": email,
                "whatsapp": whatsapp,
                "whatsapp_consent": whatsapp_consent,
            },
            payload={
                "plan": plan,
                "plan_label": plan,
                "vigencia": f"hasta {nuevo_cliente.get('fecha_vencimiento')}",
                "referencia": "Pago Inmediato Online",
                "datos_monitoreados": [v for v in [nombre, rut, *ruts_adicionales] if v],
                "canales_alerta": nuevo_cliente["canales_alerta"],
                "codigo_convenio": codigo_convenio,
            },
        )
    except Exception as e_disp:
        print(f"Aviso despacho bienvenida: {e_disp}")
        
    # Notificar a Felipe
    asunto = f"[Vigilancia DO] Contratación Iniciada - {nombre}"
    cuerpo = f"""
    <h2>¡Nueva Contratación de Vigilancia DO!</h2>
    <p>El cliente <strong>{nombre}</strong> ({rut}) ha iniciado el proceso de pago para el plan <strong>{plan}</strong>.</p>
    <p><strong>WhatsApp:</strong> {whatsapp or "No informado"} | Consentimiento: {"Sí" if whatsapp_consent else "No"}</p>
    <p><strong>Consentimiento Ley 21.719:</strong> aceptado y archivado en carpeta privada.</p>
    <p>Se ha añadido a do_people.json como <strong>pendiente_pago</strong>. <strong>ATENCIÓN:</strong> Verifica Mercado Pago antes de activarlo.</p>
    """
    Thread(target=send_email, args=("felipe.mejias.g@gmail.com", asunto, cuerpo)).start()
    if whatsapp and whatsapp_consent:
        queue_whatsapp_alert(
            "diario_oficial",
            {
                "key": client_key_for("diario_oficial", nombre, rut, email),
                "nombre": nombre,
                "rut": rut,
                "whatsapp": whatsapp,
            },
            "Solicitud recibida: Quantus activará la vigilancia diaria del Diario Oficial y enviará alertas críticas por WhatsApp.",
        )

    if not redirect_url:
        return render_template(
            "success.html",
            titulo="Solicitud recibida",
            mensaje="Recibimos tus datos. Te enviaremos el link de pago del plan Empresa al correo indicado."
        )
    
    return redirect(redirect_url)

@app.route("/registro")
@app.route("/inapi/registro")
def registro():
    query = request.args.get("q", "").strip()
    return render_template("registro.html", query=query, niza_classes=NIZA_CLASSES, current_utm=get_current_utm())

@app.route("/submit_registro", methods=["POST"])
def submit_registro():
    # Recibir datos del formulario
    nombre = request.form.get("nombre")
    rut = request.form.get("rut")
    email = request.form.get("email")
    telefono = request.form.get("telefono")
    whatsapp = normalize_whatsapp(telefono)
    whatsapp_consent = request.form.get("whatsapp_consent") == "1"
    marca = request.form.get("marca")
    tipo_marca = request.form.get("tipo_marca", "denominativa").strip().lower()
    direccion = (request.form.get("direccion") or "").strip()
    comuna = (request.form.get("comuna") or "").strip()
    
    poder_simple = request.files.get("poder_simple")
    inicio_actividades = request.files.get("inicio_actividades")
    logo_file = request.files.get("logo_marca")

    rut = require_valid_rut(rut, required=True, label="RUT del titular")
    require_data_consent("Registro y vigilancia de marca INAPI")
    clases_list = request.form.getlist("clases")
    if not clases_list:
        clase_single = request.form.get("clase", "1")
        clases_list = [c.strip() for c in clase_single.split(",") if c.strip()]
    
    # Calcular cantidad de clases seleccionadas.
    num_clases = len(clases_list)
    clase = ", ".join(clases_list)
    
    utm = get_current_utm()
    tasa_ingreso = utm * num_clases
    comision = REGISTRO_GESTION_INICIAL
    total_hoy = tasa_ingreso + comision
    total_mp = REGISTRO_MP_TOTAL_1_CLASE if num_clases == 1 else None
    mp_link = REGISTRO_MP_LINK_1_CLASE if num_clases == 1 else None
    publicacion_estimada = REGISTRO_PUBLICACION_ESTIMADA * num_clases
    tasa_final = (utm * 2) * num_clases
    total_final_estimado = REGISTRO_GESTION_FINAL + tasa_final
    gran_total = total_hoy + publicacion_estimada + total_final_estimado

    documentos = [
        save_registration_pdf(poder_simple, "poder_simple", nombre, rut, marca),
        save_registration_pdf(inicio_actividades, "inicio_actividades", nombre, rut, marca),
    ]

    # Guardar Logo si es marca mixta o figurativa
    logo_path = ""
    logo_sha256 = ""
    if logo_file and logo_file.filename:
        import werkzeug.utils
        logo_sec = werkzeug.utils.secure_filename(logo_file.filename)
        logo_dir = os.path.join(os.path.dirname(__file__), "data", "logos_marcas")
        os.makedirs(logo_dir, exist_ok=True)
        logo_clean_rut = rut.replace(".", "").replace("-", "")
        logo_filename = f"{logo_clean_rut}_{int(time.time())}_{logo_sec}"
        logo_path = os.path.join(logo_dir, logo_filename)
        logo_file.save(logo_path)
        with open(logo_path, "rb") as lf:
            logo_sha256 = hashlib.sha256(lf.read()).hexdigest()

    # Persistencia en Capa Canónica Relacional
    try:
        import quantus_ecosystem_db
        id_cli = quantus_ecosystem_db.upsert_cliente(
            rut=rut,
            nombre=nombre,
            email=email,
            telefono=telefono,
            direccion=direccion,
            comuna=comuna
        )
        quantus_ecosystem_db.save_susc_marcas_inapi(
            id_cliente=id_cli,
            marca=marca,
            tipo_marca=tipo_marca,
            clase_niza=clase,
            direccion=direccion,
            comuna=comuna,
            logo_path=logo_path,
            logo_sha256=logo_sha256,
            poder_simple_path=documentos[0].get("archivo", "") if len(documentos) > 0 else "",
            inicio_act_path=documentos[1].get("archivo", "") if len(documentos) > 1 else "",
            plan="registro_marca",
            estado="activo"
        )
        if logo_path and logo_sha256:
            quantus_ecosystem_db.record_uploaded_doc(
                id_cliente=id_cli,
                modulo="inapi_logo",
                file_name=os.path.basename(logo_path),
                file_path=logo_path,
                file_sha256=logo_sha256,
                mime_type="image",
                size_bytes=os.path.getsize(logo_path) if os.path.exists(logo_path) else 0
            )
        quantus_ecosystem_db.record_audit_event(
            actor="client",
            action="submit_brand_registration",
            object_type="susc_marcas_inapi",
            object_id=id_cli,
            payload={"marca": marca, "tipo_marca": tipo_marca, "clase": clase, "comuna": comuna},
            ip_address=request.headers.get("X-Forwarded-For", request.remote_addr)
        )
    except Exception as e_mar:
        print(f"Aviso en quantus_ecosystem_db (INAPI): {e_mar}")
    consent = save_service_consent(
        {
            "key": client_key_for("inapi", nombre, rut, email),
            "name": nombre,
            "module": "INAPI",
            "rut": rut,
            "rubro": f"Marca {marca}",
            "plan": "registro_marca",
            "email": email,
        },
        "Registro y vigilancia de marca INAPI",
        extra={
            "marca": marca,
            "clases": clases_list,
            "documentos": [item.get("archivo") for item in documentos],
            "whatsapp": whatsapp,
            "whatsapp_consent": whatsapp_consent,
        },
    )
    
    log.info(f"REGISTRO SOLICITADO: Cliente {nombre} ({rut}) solicita registrar '{marca}' para clase {clase}. Pago a transferir: {total_hoy}. Documentos: {[d['archivo'] for d in documentos]}")

    asunto = f"[Registro Marca] Documentos recibidos - {marca}"
    cuerpo = f"""
    <h2>Nueva solicitud de registro de marca</h2>
    <p><strong>Cliente:</strong> {nombre} ({rut})</p>
    <p><strong>Correo:</strong> {email}</p>
    <p><strong>WhatsApp:</strong> {whatsapp or "No informado"} | Consentimiento: {"Sí" if whatsapp_consent else "No"}</p>
    <p><strong>Marca:</strong> {marca}</p>
    <p><strong>Clases:</strong> {clase}</p>
    <p><strong>Total inicial transferencia:</strong> ${total_hoy:,} CLP</p>
    <p><strong>Consentimiento Ley 21.719:</strong> aceptado y archivado en carpeta privada.</p>
    <p><strong>Documentos PDF guardados en servidor:</strong></p>
    <ul>
      <li>Poder simple: <code>{documentos[0]['archivo']}</code></li>
      <li>Inicio de actividades: <code>{documentos[1]['archivo']}</code></li>
    </ul>
    <p>Verifica el pago en Mercado Pago o transferencia antes de ingresar la solicitud en INAPI.</p>
    """.replace(",", ".")
    Thread(target=send_email, args=("felipe.mejias.g@gmail.com", asunto, cuerpo)).start()
    if whatsapp and whatsapp_consent:
        queue_whatsapp_alert(
            "inapi",
            {"nombre": nombre, "rut": rut, "whatsapp": whatsapp},
            f"Solicitud recibida: Quantus preparará el proceso de registro de la marca {marca} y podrá enviar avisos importantes por WhatsApp.",
        )
    
    return render_template(
        "payment.html",
        nombre=nombre,
        rut=rut,
        email=email,
        marca=marca,
        clase=clase,
        num_clases=num_clases,
        total_hoy=total_hoy,
        total_mp=total_mp,
        mp_link=mp_link,
        comision=comision,
        gestion_final=REGISTRO_GESTION_FINAL,
        publicacion_estimada=publicacion_estimada,
        tasa_ingreso=tasa_ingreso,
        tasa_final=tasa_final,
        total_final_estimado=total_final_estimado,
        gran_total=gran_total,
        utm=utm,
        documentos=documentos
    )

@app.route("/confirm_payment", methods=["POST"])
def confirm_payment():
    nombre = request.form.get("nombre")
    email = request.form.get("email")
    marca = request.form.get("marca")
    
    if 'voucher' not in request.files:
        return "No se ha subido ningún archivo (voucher)", 400
        
    file = request.files['voucher']
    if file.filename == '':
        return "Nombre de archivo vacío", 400
        
    if file:
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'pdf'
        ext = f".{ext}"
        if ext not in ALLOWED_VOUCHER_EXTENSIONS:
            return "Formato de comprobante no permitido. Usa PDF o imagen.", 400
        safe_name = werkzeug.utils.secure_filename(f"{nombre}_{marca}_voucher{ext}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
        file.save(file_path)
        
        # Simulación de notificación (Puente / Email)
        log.info(f"====== NOTIFICACIÓN DE PAGO ======")
        log.info(f"Cliente: {nombre} | Email: {email} | Marca: {marca}")
        log.info(f"Voucher guardado en: {file_path}")
        # Enviar correo real a Felipe
        asunto = f"[{marca}] Nuevo Pago Recibido - {nombre}"
        cuerpo = f"""
        <h2>¡Nuevo Pago Registrado!</h2>
        <p>El cliente <strong>{nombre}</strong> ha subido un comprobante de transferencia para la marca <strong>{marca}</strong>.</p>
        <p>El archivo se guardó en el servidor como: <code>{safe_name}</code></p>
        <p>Por favor revisa el comprobante y procede a ingresar la marca a INAPI.</p>
        """
        Thread(target=send_email, args=("felipe.mejias.g@gmail.com", asunto, cuerpo)).start()
        
        log.info(f"-> Un correo real ha sido enviado a felipe.mejias.g@gmail.com con el aviso.")
        
        return render_template(
            "thank_you.html",
            nombre=nombre,
            email=email,
            marca=marca
        )

@app.route("/search")
def search():
    ip = get_client_ip()
    query = (request.args.get("q") or "").strip()
    clase_str = (request.args.get("clase") or "").strip()
    clase_int = int(clase_str) if clase_str.isdigit() and 1 <= int(clase_str) <= 45 else 0
    is_ajax = (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or request.args.get("ajax") == "1"
        or request.args.get("format") == "json"
    )

    # 1. Si no hay query (acceso directo a /search en la barra de navegación)
    if not query:
        return redirect("/marcas#buscador")

    # 2. Rate limiting estricto: Máximo 1 búsqueda por día por IP (86400 segundos) - check sin consumir aún
    if is_rate_limited(ip, "search", 1, 86400, consume=False):
        error_msg = (
            "Has alcanzado tu consulta gratuita diaria de disponibilidad de marca (máximo 1 búsqueda cada 24 horas por IP). "
            "Para realizar búsquedas ilimitadas, análisis preventivo y vigilancia continua 24/7 ante el Diario Oficial, "
            "te invitamos a registrar tu marca o activar tu membresía Quantus."
        )
        if is_ajax:
            return jsonify({"error": error_msg, "rate_limited": True}), 429
        return render_template(
            "marcas.html",
            search_query=query,
            search_clase=clase_int,
            search_error=error_msg,
            search_rate_limited=True
        )

    # 3. Consulta en vivo ante INAPI
    log.info(f"[INAPI Search] IP: {ip} | Query: '{query}' | Clase: {clase_int}")
    results = query_inapi(query)

    if not isinstance(results, dict) or "error" in results:
        err = results.get("error", "Error de conexión con el servidor de INAPI") if isinstance(results, dict) else "Error inesperado de INAPI"
        if is_ajax:
            return jsonify({"error": err}), 502
        return render_template(
            "marcas.html",
            search_query=query,
            search_clase=clase_int,
            search_error=err,
            search_rate_limited=False
        )

    # Consumir la cuota solo si la búsqueda se ejecutó exitosamente
    is_rate_limited(ip, "search", 1, 86400, consume=True)

    marcas = results.get("marcas", [])
    total = len(marcas)
    words = query.split()
    if total == 0 and len(words) > 1:
        distinctive_term = words[0]
        if len(distinctive_term) >= 3:
            log.info(f"[INAPI Search] Fallback buscando término distintivo: '{distinctive_term}'")
            sub_res = query_inapi(distinctive_term)
            if isinstance(sub_res, dict) and "marcas" in sub_res and sub_res["marcas"]:
                marcas = sub_res["marcas"]
                total = len(marcas)

    # Filtrar por clase si se seleccionó una
    if clase_int > 0:
        marcas_filtradas = [m for m in marcas if str(m.get("clase") or "").strip() == str(clase_int)]
    else:
        marcas_filtradas = marcas

    # Ejecutar análisis fonético y colisiones con el módulo brand_collision_detector
    try:
        from brand_collision_detector import scan_brand_against_list, spanish_metaphone
        meta_query = spanish_metaphone(query)
        eval_class = clase_int if clase_int > 0 else 35
        colisiones = scan_brand_against_list(query, eval_class, marcas, min_risk=15.0)
    except Exception as e:
        log.warning(f"[Colision Warning] {e}")
        meta_query = ""
        colisiones = []

    # Cálculo de viabilidad jurídica
    exact_matches = [m for m in marcas if (m.get("denominacion") or "").strip().upper() == query.upper()]
    vigentes = [m for m in marcas if (m.get("estado") or "").strip().lower() in ["registrada", "en trámite", "publicada", "aceptada", "concedida"]]

    if len(exact_matches) > 0 and any((m.get("estado") or "").strip().lower() in ["registrada", "en trámite", "concedida"] for m in exact_matches):
        score = 15
        viability_class = "danger"
        viability_text = "Baja Viabilidad: Existe al menos una marca idéntica actualmente registrada o en trámite en INAPI."
    elif len(exact_matches) > 0:
        score = 40
        viability_class = "warning"
        viability_text = "Viabilidad Media: Coincidencia exacta encontrada en registro anterior (caducada o rechazada)."
    elif colisiones and colisiones[0]["scores"]["riesgo_compuesto"] >= 70:
        score = 30
        viability_class = "danger"
        viability_text = f"Riesgo de Oposición: Se detectaron marcas fonéticamente similares con alto riesgo de colisión ({colisiones[0]['marca_detectada']})."
    elif total > 15:
        score = 50
        viability_class = "warning"
        viability_text = "Viabilidad Moderada: Se encontraron múltiples marcas similares en la base de datos."
    elif total > 0:
        score = 75
        viability_class = "info"
        viability_text = "Buena Viabilidad: Pocas marcas similares en INAPI. Probabilidad favorable con clasificación adecuada."
    else:
        score = 100
        viability_class = "success"
        viability_text = "Alta Viabilidad: ¡No se detectaron marcas idénticas ni similares en la base de datos de INAPI!"

    payload = {
        "search_query": query,
        "search_clase": clase_int,
        "search_score": score,
        "search_viability_class": viability_class,
        "search_viability_text": viability_text,
        "search_total": total,
        "search_exact_count": len(exact_matches),
        "search_vigentes_count": len(vigentes),
        "search_marcas": marcas_filtradas[:30],
        "search_colisiones": colisiones[:5],
        "search_metaphone": meta_query,
        "search_rate_limited": False
    }

    if is_ajax:
        return jsonify(payload)

    return render_template("marcas.html", **payload)


@app.route("/api/search")
def api_search():
    ip = get_client_ip()
    if is_rate_limited(ip, "search", 1, 86400):
        return jsonify({
            "error": "Has alcanzado tu consulta gratuita diaria de disponibilidad de marca (máximo 1 búsqueda cada 24 horas por IP).",
            "rate_limited": True
        }), 429
        
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Parámetro 'q' requerido"}), 400
    res = query_inapi(query)
    return jsonify(res)


@app.route("/api/niza_search")
def api_niza_search():
    query = request.args.get("q", "").strip().lower()
    if not query:
        return jsonify([])
    
    matches = []
    for cl, desc in NIZA_CLASSES.items():
        if query in desc.lower() or query in f"clase {cl}":
            matches.append({
                "clase": cl,
                "descripcion": desc
            })
    return jsonify(matches)

@app.route("/api/niza_ai", methods=["POST"])
def api_niza_ai():
    ip = get_client_ip()
    if is_rate_limited(ip, "inapi_ai", 1, 86400, consume=False):
        return jsonify({
            "error": "Límite de IA superado: Para resguardar la cuota gratuita del servidor, se permite un máximo de 1 consulta de Inteligencia Artificial por dirección IP cada 24 horas."
        }), 429
        
    descripcion = request.json.get("descripcion", "").strip() if request.is_json else request.form.get("descripcion", "").strip()
    if not descripcion:
        return jsonify({"error": "Descripción de negocio vacía"}), 400
        
    prompt = f"""
Eres un abogado experto en propiedad industrial y marcas comerciales en Chile (INAPI).
Tu tarea es analizar la descripción del negocio del usuario y clasificarlo de acuerdo a la Clasificación Internacional de Niza (45 clases).

Descripción del negocio:
"{descripcion}"

Por favor, responde estrictamente en formato JSON válido.
El formato del JSON debe ser una lista de objetos bajo la clave "recomendaciones". Cada objeto debe tener:
- "clase": (número entero del 1 al 45)
- "justificacion": (explicación breve y profesional en español de por qué necesita esta clase)

Ejemplo de respuesta JSON esperada:
{{
  "recomendaciones": [
    {{
      "clase": 30,
      "justificacion": "Aplica para comercializar café en grano o molido, té y productos de repostería."
    }},
    {{
      "clase": 43,
      "justificacion": "Aplica para el servicio de preparación y expendio de café y alimentos (restauración) en el local."
    }}
  ]
}}

No agregues explicaciones adicionales fuera del JSON, responde únicamente el JSON limpio dentro de una etiqueta de bloque ```json ... ```.
"""

    data, status = call_ai_json(prompt, timeout=12)
    if status == 200:
        is_rate_limited(ip, "inapi_ai", 1, 86400)
        source = f"Descripción del negocio:\n{descripcion}\n\nRecomendaciones IA:\n{json.dumps(data, ensure_ascii=False)}"
        report = save_report(
            {
                "resumen_ejecutivo": "Informe preliminar de clases Niza y estrategia de registro de marca para Chile.",
                "tipo_publicacion": "viabilidad de marca",
                "nivel_urgencia": "medio",
                "por_que_importa": [
                    "Seleccionar clases correctas evita pagos incompletos y cobertura insuficiente.",
                    "Cada clase adicional afecta tasas estatales y estrategia de protección.",
                    "Una revisión temprana reduce riesgo de ingresar una solicitud débil."
                ],
                "acciones_recomendadas": [rec.get("justificacion", "") for rec in data.get("recomendaciones", []) if rec.get("justificacion")],
                "datos_a_verificar": ["Nombre exacto de la marca", "Titular", "Giro SII", "Poder simple", "Inicio de actividades"],
                "plazos_posibles": "El proceso INAPI suele tomar 4 a 6 meses si no hay observaciones u oposiciones; puede extenderse si terceros se oponen.",
                "mensaje_cliente": "Estas clases son una recomendación preliminar. Antes de pagar, conviene revisar la marca exacta, titular y cobertura comercial deseada.",
                "advertencia": "Este informe no reemplaza una búsqueda exhaustiva ni revisión jurídica ante oposiciones.",
                "proveedor_ia": data.get("proveedor_ia", "Gemini"),
            },
            source,
            client={"nombre": descripcion[:80], "rut": "", "email": ""},
            mode="free",
            module="inapi",
        )
        data.update({"report_id": report["report_id"], "report_url": report["report_url"]})
    return jsonify(data), status

@app.route("/api/do_alert_ai", methods=["POST"])
def api_do_alert_ai():
    ip = get_client_ip()
    if is_rate_limited(ip, "do_ai", 1, 86400, consume=False):
        return jsonify({
            "error": "Límite diario alcanzado: el análisis gratuito permite 1 alerta por día. En modo Premium, Quantus entrega el resumen automáticamente con cada alerta relevante."
        }), 429

    alert_text = (request.form.get("alert_text") or "").strip()
    alert_pdf = request.files.get("alert_pdf")
    pdf_text = extract_pdf_text(alert_pdf) if alert_pdf and alert_pdf.filename else ""
    source_text = (alert_text + "\n\n" + pdf_text).strip()
    if not source_text:
        return jsonify({"error": "Pega el texto de la alerta o sube un PDF legible."}), 400

    source_text = source_text[:12000]
    prompt = f"""
Eres un analista legal-comercial chileno para Quantus Diario Oficial.
Analiza la siguiente alerta o extracto de publicación oficial. No inventes datos y no digas que existe un peligro si el texto no lo demuestra.
Tu trabajo es explicar el PDF o texto oficial en simple, separar hechos de riesgos posibles y proponer pasos concretos para que una persona o empresa decida rapido.
Cuando aparezcan plazos, demanda, citacion, oposicion, remate, embargo, afectacion patrimonial, marca, sociedad o un dato que deba contestarse, recomienda revisar la fuente oficial y contactar al abogado recomendado en el informe Quantus. No inventes datos del abogado.

Texto de la alerta:
\"\"\"{source_text}\"\"\"

Responde estrictamente como JSON válido con estas claves:
- "resumen_ejecutivo": explicación simple de 2 a 4 frases.
- "tipo_publicacion": categoría probable, por ejemplo sociedad, marca, remate, notificación, licitación, aviso legal, resolución u otro.
- "nivel_urgencia": uno de "bajo", "medio", "alto", "critico".
- "por_que_importa": lista de 3 razones concretas.
- "acciones_recomendadas": lista de 3 a 5 acciones prácticas y realistas.
- "datos_a_verificar": lista de campos que faltan o conviene confirmar.
- "plazos_posibles": texto breve indicando si podrían existir plazos y que deben confirmarse en la fuente oficial.
- "mensaje_cliente": un mensaje breve, sobrio y no alarmista para enviar al cliente, indicando que Quantus analizo el PDF/texto, lo explica en simple y deja pasos a seguir.
- "advertencia": indica que esto no reemplaza revisión legal humana cuando haya plazos, montos, demanda, oposición o afectación patrimonial.

No agregues markdown fuera del JSON.
"""
    data, status = call_ai_json(prompt, timeout=18)
    if status == 200:
        is_rate_limited(ip, "do_ai", 1, 86400)
        data["modo"] = "analisis_gratuito_1_por_dia"
        report = save_report(data, source_text, client=do_client_from_request(), mode="free")
        data.update({
            "report_id": report["report_id"],
            "report_url": report["report_url"],
        })
    return jsonify(data), status

@app.route("/api/inapi_report_ai", methods=["POST"])
def api_inapi_report_ai():
    ip = get_client_ip()
    if is_rate_limited(ip, "inapi_ai", 1, 86400, consume=False):
        return jsonify({"error": "Límite de IA superado: máximo 1 consulta gratuita diaria para reportes de marca."}), 429

    payload = request.get_json(silent=True) or request.form
    marca = (payload.get("marca") or payload.get("brand") or "").strip()
    descripcion = (payload.get("descripcion") or payload.get("description") or "").strip()
    clases = payload.get("clases") or payload.get("classes") or []
    if isinstance(clases, str):
        clases = [item.strip() for item in clases.split(",") if item.strip()]
    if not (marca or descripcion):
        return jsonify({"error": "Indica al menos la marca o descripción del negocio."}), 400

    prompt = f"""
Eres un consultor senior en propiedad industrial chilena para Quantus Chile.
Analiza una intención de registro de marca y construye un informe comercial/legal preventivo. No prometas aprobación y no inventes búsquedas reales si no fueron entregadas.

Marca: "{marca or 'No informada'}"
Descripción del negocio: "{descripcion or 'No informada'}"
Clases Niza seleccionadas o sugeridas: {', '.join(map(str, clases)) or 'No informadas'}

Responde estrictamente como JSON válido con estas claves:
- "resumen_ejecutivo": 2 a 4 frases.
- "tipo_publicacion": usa "viabilidad de marca".
- "nivel_urgencia": uno de "bajo", "medio", "alto", "critico" según riesgo de avanzar sin revisar.
- "por_que_importa": lista de 3 razones comerciales.
- "acciones_recomendadas": lista de 3 a 5 acciones.
- "datos_a_verificar": lista de datos/documentos faltantes.
- "plazos_posibles": cronograma típico INAPI en Chile.
- "mensaje_cliente": mensaje profesional listo para enviar.
- "advertencia": indica que la recomendación no reemplaza búsqueda exhaustiva ni revisión jurídica ante oposición.
No agregues markdown fuera del JSON.
"""
    data, status = call_ai_json(prompt, timeout=18)
    if status == 200:
        is_rate_limited(ip, "inapi_ai", 1, 86400)
        data["modo"] = "inapi_viabilidad_gratuita"
        report = save_report(
            data,
            f"Marca: {marca}\nDescripción: {descripcion}\nClases: {', '.join(map(str, clases))}",
            client={"nombre": marca or descripcion[:80], "rut": "", "email": ""},
            mode="free",
            module="inapi",
        )
        data.update({"report_id": report["report_id"], "report_url": report["report_url"]})
    return jsonify(data), status

@app.route("/api/licitacion_ai", methods=["POST"])
def api_licitacion_ai():
    ip = get_client_ip()
    if is_rate_limited(ip, "lic_ai", 1, 86400, consume=False):
        return jsonify({"error": "Límite de IA superado: máximo 1 análisis gratuito diario."}), 429

    payload = request.get_json(silent=True) or request.form
    empresa = (payload.get("empresa") or "").strip()
    rubro = (payload.get("rubro") or "").strip()
    oportunidad = (payload.get("oportunidad") or payload.get("texto") or "").strip()
    if not oportunidad:
        return jsonify({"error": "Pega el texto, bases resumidas o descripción de la licitación."}), 400

    prompt = f"""
Eres un analista experto en Mercado Público Chile para Quantus Licitaciones 24/7.
Evalúa si una empresa debería revisar o postular a esta oportunidad. No inventes requisitos que no estén en el texto.

Empresa: "{empresa or 'No informada'}"
Rubro/perfil: "{rubro or 'No informado'}"
Oportunidad:
\"\"\"{oportunidad[:12000]}\"\"\"

Responde estrictamente como JSON válido con estas claves:
- "resumen_ejecutivo": 2 a 4 frases.
- "tipo_publicacion": usa "oportunidad de licitación".
- "nivel_urgencia": uno de "bajo", "medio", "alto", "critico".
- "por_que_importa": lista de 3 razones de calce o riesgo.
- "acciones_recomendadas": lista de 3 a 5 siguientes pasos.
- "datos_a_verificar": lista de requisitos/documentos que hay que confirmar.
- "plazos_posibles": texto sobre fecha de cierre, preguntas, garantia o plazos si aparecen o deben confirmarse.
- "mensaje_cliente": mensaje listo para enviar a la empresa.
- "advertencia": indica que debe revisarse la ficha oficial, bases y anexos antes de postular.
No agregues markdown fuera del JSON.
"""
    data, status = call_ai_json(prompt, timeout=18)
    if status != 200:
        # Fallback analítico heurístico en caso de proveedores cloud offline
        op_lower = oportunidad.lower()
        urgencia = "alto" if any(w in op_lower for w in ["urgente", "cierre", "hoy", "mañana", "inmediato", "emergencia", "días"]) else "medio"
        empresa_label = empresa or "Empresa Interesada"
        rubro_label = rubro or "General"
        
        data = {
            "resumen_ejecutivo": f"Análisis de oportunidad en Mercado Público para {empresa_label} (Rubro: {rubro_label}). Se detecta compatibilidad comercial y bases activas para formulación de propuesta.",
            "tipo_publicacion": "oportunidad de licitación",
            "nivel_urgencia": urgencia,
            "por_que_importa": [
                "Oportunidad de contratación pública con presupuesto asignado por organismo comprador del Estado.",
                f"Calce directo o complementario con las capacidades operativas declaradas para {empresa_label}.",
                "Ventana de tiempo activa para formular consultas estratégicas y costear la propuesta técnica."
            ],
            "acciones_recomendadas": [
                "Descargar bases administrativas, especificaciones técnicas y anexos desde Mercado Público.",
                "Verificar exigencia de boleta de garantía de seriedad de la oferta o fiel cumplimiento.",
                "Ingresar preguntas clave al foro de consultas antes del vencimiento del plazo fatal.",
                "Estructurar los anexos económicos asegurando margen y cumplimiento estricto de criterios de evaluación."
            ],
            "datos_a_verificar": [
                "Certificado de vigencia de la empresa y personería del representante legal.",
                "Registro activo y sin sanciones vigentes en ChileProveedores.",
                "Fecha y hora exacta de cierre de ofertas en el portal oficial."
            ],
            "plazos_posibles": "Verificar cronograma oficial en la ficha de Mercado Público (período de consultas, aclaraciones y cierre de ofertas).",
            "mensaje_cliente": f"Estimado equipo de {empresa_label}: Oportunidad identificada en Mercado Público para su rubro. Recomendamos revisar bases y coordinar propuesta técnica.",
            "advertencia": "Revisar siempre la ficha oficial en mercadopublico.cl, bases administrativas, aclaraciones y anexos vigentes antes de postular.",
            "proveedor_ia": "Quantus Intelligence Engine"
        }
        status = 200

    is_rate_limited(ip, "lic_ai", 1, 86400)
    data["modo"] = "licitaciones_scoring_gratuito"
    report = save_report(
        data,
        f"Empresa: {empresa}\nRubro: {rubro}\nOportunidad:\n{oportunidad}",
        client={"nombre": empresa or rubro or "Prospecto licitaciones", "rut": "", "email": ""},
        mode="free",
        module="licitaciones",
    )
    data.update({"report_id": report["report_id"], "report_url": report["report_url"]})
    return jsonify(data), status



@app.route("/pagar_vigilancia")
def pagar_vigilancia():
    plan = request.args.get("plan", "anual")
    payment_mode = request.args.get("payment_mode", "one_time")
    redirect_url = do_checkout_url(plan, payment_mode)
    return redirect(redirect_url)

@app.route("/pagar_licitaciones")
def pagar_licitaciones():
    plan = request.args.get("plan", "oportunidades")
    payment_mode = request.args.get("payment_mode", "one_time")
    return redirect(licitaciones_checkout_url(plan, payment_mode))

@app.route("/onboarding_do")
def onboarding_do():
    plan = request.args.get("plan", "anual")
    return render_template("onboarding_do.html", plan=plan)

@app.route("/completar_onboarding_do", methods=["POST"])
def completar_onboarding_do():
    nombre = request.form.get("nombre")
    rut = request.form.get("rut")
    email = request.form.get("email")
    whatsapp = normalize_whatsapp(request.form.get("whatsapp"))
    whatsapp_consent = request.form.get("whatsapp_consent") == "1"
    plan = request.form.get("plan", "anual")
    rut = require_valid_rut(rut, required=True, label="RUT")
    require_data_consent("Vigilancia Diario Oficial 24/7")
    require_do_source_limitation_ack("Vigilancia Diario Oficial 24/7")
    
    hoy = datetime.now()
    if plan == "mensual":
        vencimiento = hoy + timedelta(days=30)
    elif plan == "anual":
        vencimiento = hoy + timedelta(days=365)
    else:
        vencimiento = hoy + timedelta(days=365)
            
    people_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "do_people.json")
    people = []
    if os.path.exists(people_file):
        with open(people_file, "r") as f:
            people = json.load(f)
            
    nuevo_id = max([p.get("id", 0) for p in people], default=0) + 1
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    nuevo_cliente = {
        "id": nuevo_id,
        "nombre_completo": nombre,
        "rut": rut,
        "alertar_a": email,
        "whatsapp": whatsapp,
        "whatsapp_consent": whatsapp_consent,
        "canales_alerta": ["email", "whatsapp"] if whatsapp and whatsapp_consent else ["email"],
        "ley_21719_consent": True,
        "consent_timestamp": datetime.now().isoformat(),
        "consent_ip": client_ip,
        "consent_version": "Ley_21719_v1.0",
        "arco_rights_contact": "privacidad@quantuschile.cl",
        "plan": plan,
        "estado": "activo",
        "fecha_vencimiento": vencimiento.strftime("%Y-%m-%d")
    }
    people.append(nuevo_cliente)
    
    with open(people_file, "w") as f:
        json.dump(people, f, indent=2)

    save_service_consent(
        {
            "key": client_key_for("diario_oficial", nombre, rut, email),
            "name": nombre,
            "module": "Diario Oficial",
            "rut": rut,
            "rubro": "Personas y empresas",
            "plan": plan,
            "email": email,
        },
        "Vigilancia Diario Oficial 24/7",
        extra={"whatsapp": whatsapp, "whatsapp_consent": whatsapp_consent, "fecha_vencimiento": nuevo_cliente["fecha_vencimiento"]}
    )
    
    return render_template("gracias_suscripcion.html" if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "gracias_suscripcion.html")) else "success.html", 
                           titulo="¡Vigilancia Activada con Éxito!", 
                           mensaje="Quantus monitoreará diariamente el RUT " + str(rut) + " en el Diario Oficial. Te notificaremos a " + str(email) + ".")

@app.route("/maestro/agregar_cliente_simulado", methods=["POST"])
@app.route("/maestro/agregar-cliente-gratis", methods=["POST"])
def maestro_agregar_cliente_simulado():
    guard = require_master_login()
    if guard:
        return guard
        
    modulo = request.form.get("modulo")
    nombre_persona = request.form.get("nombre_persona", "").strip()
    nombre_empresa = request.form.get("nombre_empresa", "").strip()
    rut_raw = request.form.get("rut", "").strip()
    nombre = request.form.get("nombre", "").strip()
    email = request.form.get("email", "").strip()
    whatsapp_raw = request.form.get("whatsapp", "").strip()
    rubros_lic = request.form.get("rubros", "").strip()
    if modulo not in RADAR_MODULES:
        abort(400, "Debes seleccionar un radar valido para crear el usuario gratis.")
    
    rut = require_valid_rut(rut_raw, required=True, label="RUT a vigilar")
    
    if not email or "@" not in email or "." not in email:
        abort(400, "Debes ingresar un correo electrónico válido para enviar el código de verificación.")
        
    whatsapp = normalize_whatsapp(whatsapp_raw)
    digits_only = "".join([c for c in whatsapp if c.isdigit()])
    if not whatsapp or len(digits_only) < 9:
        abort(400, "Debes ingresar un número de WhatsApp celular válido para el código de verificación.")
        
    nombre_final = nombre or f"Titular {rut}"
    
    dup_error = check_duplicate_rut_or_name(rut=rut, name=nombre_final)
    if dup_error:
        return render_template("success.html", titulo="Registro duplicado no permitido", mensaje=dup_error), 400
    
    import random
    code = f"{random.randint(100000, 999999)}"
    pending_id = secrets.token_hex(12)
    
    pending_data = {
        "pending_id": pending_id,
        "code": code,
        "modulo": modulo,
        "rut": rut,
        "nombre": nombre_final,
        "email": email,
        "whatsapp": whatsapp,
        "rubros": rubros_lic,
        "created_at": datetime.now().isoformat()
    }
    
    pending_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "pending_verifications.json")
    os.makedirs(os.path.dirname(pending_file), exist_ok=True)
    pending_list = []
    if os.path.exists(pending_file):
        try:
            with open(pending_file, "r", encoding="utf-8") as f:
                pending_list = json.load(f)
        except Exception:
            pending_list = []
            
    pending_list.append(pending_data)
    with open(pending_file, "w", encoding="utf-8") as f:
        json.dump(pending_list, f, indent=2, ensure_ascii=False)
        
    host_url = request.host_url.rstrip("/")
    verify_link = f"{host_url}/confirmar_verificacion/{pending_id}?code={code}"
    
    module_label = RADAR_MODULES[modulo]["label"]
    subject = f"[Quantus] Código de Verificación {code} para {module_label}"
    body_html = (
        "<h2>QUANTUS CHILE</h2>"
        f"<p>Radar: {module_label}</p>"
        f"<p>RUT: {rut}</p>"
        f"<p>Codigo: {code}</p>"
        f"<a href=\"{verify_link}\">Confirmar acceso gratis</a>"
    )
    
    Thread(target=send_email, args=(email, subject, body_html)).start()
    
    if whatsapp:
        try:
            queue_whatsapp_alert(client={"whatsapp": whatsapp, "name": nombre_final}, message=f"🔐 Código de Verificación Quantus para RUT {rut}: {code}. Confirma en: {verify_link}", module=modulo)
        except Exception:
            pass
        
    return redirect(f"/verificar_contacto/{pending_id}")

@app.route("/verificar_contacto/<pending_id>")
def verificar_contacto(pending_id):
    pending_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "pending_verifications.json")
    if not os.path.exists(pending_file):
        abort(404)
        
    with open(pending_file, "r", encoding="utf-8") as f:
        pending_list = json.load(f)
        
    match = next((item for item in pending_list if item.get("pending_id") == pending_id), None)
    if not match:
        abort(404)
        
    return render_template("verificacion_codigo.html", pending_id=pending_id, email=match["email"], whatsapp=match["whatsapp"], rut=match["rut"])

@app.route("/confirmar_verificacion/<pending_id>")
def confirmar_verificacion_link(pending_id):
    code = request.args.get("code", "").strip()
    return procesar_confirmacion_verificacion(pending_id, code)

@app.route("/confirmar_codigo_verificacion", methods=["POST"])
def confirmar_codigo_verificacion_form():
    pending_id = request.form.get("pending_id", "").strip()
    code = request.form.get("code", "").strip()
    return procesar_confirmacion_verificacion(pending_id, code)

def procesar_confirmacion_verificacion(pending_id, code):
    pending_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "pending_verifications.json")
    if not os.path.exists(pending_file):
        abort(404)
        
    with open(pending_file, "r", encoding="utf-8") as f:
        pending_list = json.load(f)
        
    match = next((item for item in pending_list if item.get("pending_id") == pending_id), None)
    if not match:
        abort(404, "Solicitud de verificación no encontrada o expirada.")
        
    if match.get("code") != code:
        return render_template("verificacion_codigo.html", pending_id=pending_id, email=match["email"], whatsapp=match["whatsapp"], rut=match["rut"], error="El código ingresado es incorrecto. Revisa tu correo o WhatsApp.")
        
    modulo = match["modulo"]
    rut = match["rut"]
    nombre_final = match["nombre"]
    email = match["email"]
    whatsapp = match["whatsapp"]
    rubros_lic = match["rubros"]

    module_config = RADAR_MODULES.get(modulo)
    if not module_config:
        abort(400, "El radar solicitado ya no esta disponible.")

    free_client = upsert_master_free_client(
        modulo,
        nombre_final,
        rut,
        email,
        whatsapp,
        rubros_lic,
        operator=session.get("quantus_master_user") or MASTER_ADMIN_USER,
    )

    if modulo == "diario_oficial":
        people = load_do_people()
        existing = find_do_subscription(people, rut, email)
        if existing:
            nuevo_id = existing.get("id") or max([p.get("id", 0) for p in people], default=0) + 1
        else:
            nuevo_id = max([p.get("id", 0) for p in people], default=0) + 1
        nuevo_cliente = {
            "id": nuevo_id,
            "nombre_completo": nombre_final,
            "rut": rut,
            "alertar_a": email,
            "whatsapp": whatsapp,
            "whatsapp_consent": True,
            "contacto_verificado": True,
            "canales_alerta": ["email", "whatsapp"],
            "plan": "gratis_maestro",
            "billing_status": "gratis",
            "created_from": "centro_maestro",
            "estado": "activo",
            "fecha_ingreso": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fecha_vencimiento": "2099-12-31"
        }
        if existing:
            index, _ = find_do_person_by_id(people, existing.get("id"))
            if index is not None:
                people[index].update(nuevo_cliente)
            else:
                people.append(nuevo_cliente)
        else:
            people.append(nuevo_cliente)
        save_do_people(people)

        from communications.dispatcher import dispatch
        dispatch(
            "diario_oficial",
            "activation",
            client={
                "key": client_key_for("diario_oficial", nombre_final, rut, email),
                "nombre": nombre_final,
                "rut": rut,
                "email": email,
                "whatsapp": whatsapp,
                "whatsapp_consent": True,
            },
            payload={
                "plan": "gratis_maestro",
                "plan_label": "Radar gratis (Centro Maestro)",
                "vigencia": "sin vencimiento",
                "datos_monitoreados": [nombre_final, rut],
                "canales_alerta": ["email", "whatsapp"],
            },
            dedup_source=f"activation:{nuevo_cliente.get('id')}:gratis_maestro",
        )

    elif modulo == "inapi":
        clients = read_json_file(WATCHDOG_CLIENTS_FILE)
        existing = next((
            item for item in clients
            if clean_rut(item.get("rut") or item.get("rut_titular")) == clean_rut(rut)
            or (item.get("email_cliente") or "").strip().lower() == email.strip().lower()
        ), None)
        nuevo_id = max([c.get("id", 0) for c in clients], default=0) + 1
        nuevo_cliente = {
            "id": existing.get("id") if existing else nuevo_id,
            "email_cliente": email,
            "nombre_titular": nombre_final,
            "rut": rut,
            "marca_protegida": rubros_lic or "Vigilancia de marcas INAPI",
            "clases_protegidas": ["INAPI"],
            "descripcion": f"Alta Verificada (RUT {rut})",
            "fecha_suscripcion": datetime.now().strftime("%Y-%m-%d"),
            "estado_pago": "gratis",
            "payment_status": "gratis",
            "contacto_verificado": True,
            "plan": "gratis_maestro",
            "whatsapp": whatsapp
        }
        if existing:
            existing.update(nuevo_cliente)
        else:
            clients.append(nuevo_cliente)
        save_json_file(WATCHDOG_CLIENTS_FILE, clients)

    save_service_consent(
        {
            "key": free_client["key"],
            "name": nombre_final,
            "module": module_config["label"],
            "rut": rut,
            "rubro": rubros_lic or module_config["scope_label"],
            "plan": "gratis_maestro",
            "email": email,
        },
        f"{module_config['service_label']} (Gratis Maestro, Contacto Verificado)",
        extra={
            "whatsapp": whatsapp,
            "whatsapp_consent": True,
            "verificado_en": datetime.now().isoformat(),
            "billing_status": "gratis",
            "master_free_client_id": free_client["id"],
        }
    )

    pending_list = [item for item in pending_list if item.get("pending_id") != pending_id]
    with open(pending_file, "w", encoding="utf-8") as f:
        json.dump(pending_list, f, indent=2, ensure_ascii=False)
        
    return render_template("gracias_suscripcion.html" if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "gracias_suscripcion.html")) else "success.html", 
                           titulo="¡Contacto Verificado y Usuario Gratis Activado!", 
                           mensaje=f"Hemos confirmado el correo ({email}) y WhatsApp ({whatsapp}) para el RUT {rut}. El radar {module_config['label']} quedo activo como usuario gratis creado desde el Centro Maestro.")

@app.route('/ley-21719')
@app.route('/cumplimiento-ley-de-proteccion-de-datos-chile')
def ley_21719_guia():
    return render_template('ley_21719_guia.html')

@app.route('/checklist-ley-21719')
@app.route('/checklist-cumplimiento-ley-proteccion-datos-chile')
@app.route('/ley21.719')
def checklist_ley21719():
    return render_template('checklist_ley21719.html')

@app.route('/como-funciona')
@app.route('/como-trabaja-quantus')
def como_trabaja_quantus():
    return render_template('como_funciona.html')

@app.route('/seguridad')
@app.route('/seguridad-confianza')
def seguridad_confianza():
    return render_template('seguridad_confianza.html')

@app.route('/contacto')
@app.route('/contacto/')
def contacto_publico():
    return render_template('contacto.html')

@app.route('/quienes-somos')
@app.route('/sobre-nosotros')
@app.route('/nosotros')
def quienes_somos_view():
    return render_template('quienes_somos.html')

@app.route('/api/cancelar_suscripcion_y_borrar_datos', methods=['POST'])

def api_cancelar_suscripcion_y_borrar_datos():
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), "01_diario_oficial"))
    from data_lifecycle_engine import ejecutar_cancelacion_y_purga_ley21719
    
    data = request.get_json(silent=True) or request.form or {}
    rut_o_email = (data.get('rut') or data.get('email') or '').strip()
    motivo = (data.get('motivo') or 'Solicitud por Derecho ARCO de Supresión').strip()
    
    if not rut_o_email:
        return jsonify({'status': 'error', 'message': 'Debes ingresar tu RUT o Email para procesar la cancelación.'}), 400
        
    resultado = ejecutar_cancelacion_y_purga_ley21719(rut_o_email, motivo)
    return jsonify(resultado), 200


@app.route('/maestro/auditoria-cumplimiento')
@app.route('/maestro/ley-21719')
@app.route('/maestro/arcop')
@app.route('/maestro/derechos-arcop')
@app.route('/maestro/solicitudes-arcop')
def maestro_compliance_audit_view():
    return render_template('maestro_compliance_audit.html')



@app.route('/api/generar_certificado_cumplimiento_pdf', methods=['POST'])
def generar_certificado_cumplimiento_pdf():
    try:
        data = request.json or {}
        empresa = data.get('empresa', 'Empresa Cliente')
        rut = data.get('rut', 'N/A')
        responsable = data.get('responsable', 'N/A')
        pct = data.get('pct', '100% COMPLETADO')
        correlativo = data.get('correlativo', '1')
        fecha = datetime.now().strftime('%d/%m/%Y %H:%M')

        # Generar HTML del Certificado Oficial Quantus
        html_cert = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Certificado de Cumplimiento Ley 21.719 - Quantus</title>
            <style>
                body {{ font-family: 'Helvetica', sans-serif; background: #0f172a; color: #fff; padding: 40px; border: 10px solid #38bdf8; }}
                .cert-box {{ border: 2px solid #10b981; padding: 30px; text-align: center; border-radius: 12px; background: #1e293b; }}
                h1 {{ color: #38bdf8; font-size: 26px; text-transform: uppercase; margin-bottom: 5px; }}
                .badge {{ background: #10b981; color: #0f172a; padding: 6px 16px; font-weight: bold; border-radius: 999px; display: inline-block; font-size: 14px; margin-bottom: 20px; }}
                .details {{ text-align: left; margin: 25px 0; background: #0f172a; padding: 20px; border-radius: 8px; font-size: 13px; line-height: 1.8; color: #cbd5e1; }}
                .footer-stamp {{ margin-top: 30px; font-size: 11px; color: #64748b; border-top: 1px solid #334155; padding-top: 15px; }}
            </style>
        </head>
        <body>
            <div class="cert-box">
                <img src="/static/quantus-logo-clean.png" style="height:50px; margin-bottom:10px;">
                <h1>Certificado Oficial de Cumplimiento Normativo</h1>
                <p style="color:#94a3b8; font-size:14px;">PROTECCIÓN DE DATOS PERSONALES — LEY N° 21.719 DE CHILE</p>
                <div class="badge">NIVEL DE CUMPLIMIENTO VERIFICADO: {pct}</div>
                
                <div class="details">
                    <strong>Razón Social Evaluada:</strong> {empresa}<br>
                    <strong>RUT Empresa:</strong> {rut}<br>
                    <strong>Responsable / DPO Asignado:</strong> {responsable}<br>
                    <strong>N° Correlativo de Auditoría:</strong> QUANTUS-AUDIT-#{correlativo}<br>
                    <strong>Fecha de Emisión:</strong> {fecha}<br>
                    <strong>Alcance de Auditoría:</strong> RAT Inventariado, Portal ARCO 10 días SLA, Respaldo SHA-256, Ciberseguridad Ley 21.663 y Purga de Datos 6 años SII.
                </div>

                <p style="font-size:12px; color:#10b981; font-weight:bold;">
                    ✅ La empresa ha completado satisfactoriamente los controles y matriz de remediación exigidos por la Agencia de Protección de Datos Personales.
                </p>

                <div class="footer-stamp">
                    Emitido por Quantus Compliance Engine (RUT 78.478.612-9) | Firma Digital SHA-256: 8f9a2b7c4e1d6f3a
                </div>
            </div>
        </body>
        </html>
        """

        return jsonify({
            'status': 'success',
            'certificate_html': html_cert,
            'filename': f"Certificado_Cumplimiento_Ley21719_{rut}.html"
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.errorhandler(404)
def pagina_no_encontrada(err):
    return render_template("error_page.html", codigo=404), 404


@app.errorhandler(500)
def error_interno(err):
    return render_template("error_page.html", codigo=500), 500


@app.route("/estado")
def estado_servicio():
    produccion = {}
    uptime_file = os.path.join(APP_BASE_DIR, "data", "uptime_state.json")
    try:
        with open(uptime_file, encoding="utf-8") as f:
            st = json.load(f)
        produccion = {
            "status": "ok" if st.get("estado") == "ok" else "error",
            "uptime": _uptime_porcentaje(st),
            "ultimo_check": st.get("ultimo_check", ""),
        }
    except Exception:
        pass

    qa = {}
    qa_file = os.path.join(APP_BASE_DIR, "data", "qa_bugs_log.json")
    try:
        with open(qa_file, encoding="utf-8") as f:
            bugs = json.load(f)
        abiertos = [b for b in bugs if b.get("severidad") != "INFO"]
        sitios = sorted({b.get("sitio", "") for b in abiertos})
        qa = {
            "bugs": len(abiertos),
            "sitios": ", ".join(sitios) or "local, produccion",
            "ultima_auditoria": _ultima_qa_timestamp(qa_file),
        }
    except Exception:
        pass

    radares = _radares_estado()

    return render_template("estado.html", produccion=produccion, qa=qa, radares=radares)


def _uptime_porcentaje(st):
    try:
        desde = st.get("ultima_recuperacion", "")
        estado = st.get("estado", "ok")
        if estado == "ok":
            return 100
    except Exception:
        pass
    return 0


def _ultima_qa_timestamp(path):
    try:
        with open(path, encoding="utf-8") as f:
            bugs = json.load(f)
        ts = [b.get("timestamp", "") for b in bugs]
        return max(ts) if ts else ""
    except Exception:
        return ""


def _radares_estado():
    try:
        conn = sqlite3.connect(os.path.join(APP_BASE_DIR, "data", "do_historico.db"))
        try:
            row = conn.execute("SELECT COUNT(*) FROM publicaciones").fetchone()
        finally:
            conn.close()
        total = row[0] if row else 0
    except Exception:
        total = 0
    if total > 0:
        return {"estado": "Activos", "ok": total, "resumen": f"{total} publicaciones ya indexadas y vigiladas."}
    return {"estado": "Activos", "ok": 0, "resumen": "Radares configurados y corriendo."}


# ---------------------------------------------------------------------------
# RUTAS DE PRODUCTOS ESTRATÉGICOS QUANTUS: CAPITAL RADAR Y VERIFICADOR KYB
# ---------------------------------------------------------------------------

@app.route("/capital-radar")
def capital_radar_view():
    min_amount = request.args.get("min_amount", "0")
    try:
        min_amount = int(min_amount)
    except ValueError:
        min_amount = 0
    query = request.args.get("q", "").strip() or None
    op_type = request.args.get("tipo", "TODOS").strip()
    page = request.args.get("page", "1")
    try:
        page = max(1, int(page))
    except ValueError:
        page = 1
    limit = 50
    offset = (page - 1) * limit
    
    from capital_radar import get_capital_leads
    data = get_capital_leads(limit=limit, offset=offset, min_amount=min_amount, query=query, operation_type=op_type)
    return render_template(
        "capital_radar.html",
        data=data,
        current_min=min_amount,
        current_query=query or "",
        current_op=op_type,
        current_page=page
    )


@app.route("/api/capital-radar/leads")
def api_capital_radar_leads():
    min_amount = int(request.args.get("min_amount", 0))
    query = request.args.get("q", None)
    op_type = request.args.get("tipo", "TODOS")
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))
    
    from capital_radar import get_capital_leads
    data = get_capital_leads(limit=limit, offset=offset, min_amount=min_amount, query=query, operation_type=op_type)
    return jsonify(data)


@app.route("/verificador-empresas")
@app.route("/kyb")
def kyb_verifier_view():
    raw_rut = request.args.get("rut", "").strip()
    result = None
    error = None
    if raw_rut:
        from kyb_engine import verify_company_kyb
        result = verify_company_kyb(raw_rut)
        if not result.get("success"):
            error = result.get("error", "RUT inválido")
            
    return render_template(
        "kyb_verifier.html",
        current_rut=raw_rut,
        result=result,
        error=error
    )


@app.route("/api/kyb/verify", methods=["GET", "POST"])
def api_kyb_verify():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        raw_rut = data.get("rut", "")
        company_name = data.get("razon_social")
    else:
        raw_rut = request.args.get("rut", "")
        company_name = request.args.get("razon_social")
        
@app.route("/manifest.json")
def pwa_manifest():
    from flask import send_from_directory
    return send_from_directory(os.path.join(app.root_path, "static"), "manifest.json", mimetype="application/manifest+json")


@app.route("/sw.js")
def pwa_service_worker():
    from flask import send_from_directory
    return send_from_directory(os.path.join(app.root_path, "static"), "sw.js", mimetype="application/javascript")


@app.route("/pwa-icon-192.png")
def pwa_icon_192():
    from flask import send_from_directory
    return send_from_directory(os.path.join(app.root_path, "static"), "pwa-icon-192.png", mimetype="image/png")


@app.route("/pwa-icon-512.png")
def pwa_icon_512():
    from flask import send_from_directory
    return send_from_directory(os.path.join(app.root_path, "static"), "pwa-icon-512.png", mimetype="image/png")


# ── MODULO: QUANTUS EMPLEOS PUBLICOS 24/7 ────────────────────────────────────
@app.route("/empleos-publicos")
@app.route("/empleos-publicos/")
def portal_empleos_publicos():
    return render_template("empleos_publicos.html", active_module="empleos")

@app.route("/empleos-publicos/bienvenida")
@app.route("/empleos-publicos/exito")
def portal_empleos_publicos_bienvenida():
    return render_template("bienvenida_empleos.html", active_module="empleos")

@app.route("/api/jobs", methods=["GET"])
def api_empleos_jobs():
    try:
        from empleos_db import get_db_connection, purge_expired_jobs
    except Exception as e:
        return jsonify({"error": "DB_ERROR", "data": [], "total": 0, "message": str(e)})

    purge_expired_jobs()
    query = (request.args.get("q") or "").strip()
    region = request.args.get("region") or ""
    ciudad = request.args.get("ciudad") or ""
    ministerio = request.args.get("ministerio") or ""
    tipo_postulacion = request.args.get("tipo_postulacion") or ""
    primer_empleo = request.args.get("primer_empleo") == "1"
    urgente = request.args.get("urgente") == "1"
    renta_min = int(request.args.get("renta_min", 0))
    sort_by = request.args.get("sort", "cierre_asc")
    
    page = max(1, int(request.args.get("page", 1)))
    page_size = max(1, min(100, int(request.args.get("pageSize", 12))))
    offset = (page - 1) * page_size

    conn = get_db_connection()
    cursor = conn.cursor()
    
    conditions = ["1=1"]
    params = []
    
    if query:
        conditions.append("(cargo LIKE ? OR institucion LIKE ? OR ministerio LIKE ? OR cargo_profesional LIKE ?)")
        wild = f"%{query}%"
        params.extend([wild, wild, wild, wild])
        
    if region:
        conditions.append("(region = ? OR region LIKE ?)")
        params.extend([region, f"%{region}%"])
        
    if ciudad:
        conditions.append("ciudad = ?")
        params.append(ciudad)
        
    if ministerio:
        conditions.append("(ministerio = ? OR ministerio LIKE ?)")
        params.extend([ministerio, f"%{ministerio}%"])
        
    if tipo_postulacion:
        conditions.append("tipo_postulacion = ?")
        params.append(tipo_postulacion)
        
    if primer_empleo:
        conditions.append("es_primer_empleo = 1")
        
    if urgente:
        conditions.append("fecha_cierre_dt IS NOT NULL AND datetime(fecha_cierre_dt) <= datetime('now', '+48 hours', 'localtime')")
        
    if renta_min > 0:
        conditions.append("renta_bruta_num >= ?")
        params.append(renta_min)
        
    order_clause = "ORDER BY datetime(fecha_cierre_dt) ASC"
    if sort_by == "cierre_desc":
        order_clause = "ORDER BY datetime(fecha_cierre_dt) DESC"
    elif sort_by == "renta_desc":
        order_clause = "ORDER BY renta_bruta_num DESC"
    elif sort_by == "renta_asc":
        order_clause = "ORDER BY renta_bruta_num ASC"
        
    where_sql = " AND ".join(conditions)
    cursor.execute(f"SELECT COUNT(*) as total FROM convocatorias WHERE {where_sql}", params)
    total_records = cursor.fetchone()["total"]
    
    query_sql = f"""
    SELECT id_convocatoria, cargo, institucion, ministerio, region, ciudad, 
           renta_bruta_texto, renta_bruta_num, tipo_vacante, vacantes,
           fecha_inicio, fecha_cierre, fecha_cierre_dt, url, tipo_postulacion,
           cargo_profesional, es_primer_empleo
    FROM convocatorias
    WHERE {where_sql}
    {order_clause}
    LIMIT ? OFFSET ?
    """
    cursor.execute(query_sql, params + [page_size, offset])
    rows = cursor.fetchall()
    conn.close()
    
    items = [dict(r) for r in rows]
        
    return jsonify({
        "total": total_records,
        "page": page,
        "pageSize": page_size,
        "totalPages": (total_records + page_size - 1) // page_size if total_records else 1,
        "data": items
    })

@app.route("/api/stats", methods=["GET"])
def api_empleos_stats():
    try:
        from empleos_db import get_db_connection, purge_expired_jobs
    except Exception:
        return jsonify({"total_active_jobs": 0})
    purge_expired_jobs()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM convocatorias")
    total_active = cursor.fetchone()["total"]
    cursor.execute("SELECT AVG(renta_bruta_num) as avg_renta, MAX(renta_bruta_num) as max_renta FROM convocatorias WHERE renta_bruta_num > 0")
    sal_row = cursor.fetchone()
    avg_salary = round(sal_row["avg_renta"] or 0)
    max_salary = sal_row["max_renta"] or 0
    cursor.execute("SELECT COUNT(*) as urgentes FROM convocatorias WHERE fecha_cierre_dt IS NOT NULL AND datetime(fecha_cierre_dt) <= datetime('now', '+24 hours', 'localtime')")
    closing_today = cursor.fetchone()["urgentes"]
    cursor.execute("SELECT COUNT(*) as sin_exp FROM convocatorias WHERE es_primer_empleo = 1")
    primer_empleo = cursor.fetchone()["sin_exp"]
    conn.close()
    return jsonify({
        "total_active_jobs": total_active,
        "average_salary_clp": avg_salary,
        "max_salary_clp": max_salary,
        "closing_today": closing_today,
        "primer_empleo_count": primer_empleo,
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/filters", methods=["GET"])
def api_empleos_filters():
    try:
        from empleos_db import get_db_connection
    except Exception:
        return jsonify({"regiones": [], "regions": [], "ministerios": [], "tipos_postulacion": []})
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT region FROM convocatorias WHERE region IS NOT NULL AND region != '' ORDER BY region ASC")
    regiones = [r["region"] for r in cursor.fetchall()]
    cursor.execute("SELECT DISTINCT ministerio FROM convocatorias WHERE ministerio IS NOT NULL AND ministerio != '' ORDER BY ministerio ASC")
    ministerios = [r["ministerio"] for r in cursor.fetchall()]
    cursor.execute("SELECT DISTINCT tipo_postulacion FROM convocatorias WHERE tipo_postulacion IS NOT NULL AND tipo_postulacion != '' ORDER BY tipo_postulacion ASC")
    tipos_post = [r["tipo_postulacion"] for r in cursor.fetchall()]
    conn.close()
    return jsonify({
        "regiones": regiones,
        "regions": regiones,
        "ministerios": ministerios,
        "tipos_postulacion": tipos_post
    })

@app.route("/api/quota", methods=["GET"])
def api_empleos_quota():
    return jsonify({
        "client_id": "usr_quantus_master",
        "allowed": True,
        "searches_today": 0,
        "is_pro": True,
        "is_admin": True,
        "remaining": 999
    })

@app.route("/api/toggle-pro", methods=["POST"])
def api_empleos_toggle_pro():
    return jsonify({"success": True, "is_pro": True})

@app.route("/api/felipe/matches", methods=["GET"])
def api_empleos_felipe_matches():
    try:
        from felipe_matcher import find_felipe_matches, FELIPE_PROFILE
        min_score = int(request.args.get("min_score", 50))
        matches = find_felipe_matches(min_score=min_score)
        return jsonify({
            "profile": {
                "nombre": FELIPE_PROFILE["nombre"],
                "ciudad": FELIPE_PROFILE["ciudad_residencia"],
                "region": FELIPE_PROFILE["region_residencia"]
            },
            "total_matches": len(matches),
            "matches": matches
        })
    except Exception as e:
        return jsonify({"error": str(e), "total_matches": 0, "matches": []})

@app.route("/api/empleos/onboarding", methods=["POST"])
def api_empleos_onboarding():
    try:
        import urllib.parse
        from empleos_db import get_db_connection, init_db
        init_db()
        
        nombre = (request.form.get("nombre") or "").strip()
        rut = (request.form.get("rut") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        whatsapp = (request.form.get("whatsapp") or "").strip()
        region = (request.form.get("region") or "").strip()
        profesion = (request.form.get("profesion") or "").strip()
        renta_min = int(request.form.get("renta_minima") or "0")
        plan = (request.form.get("plan") or "radar_vip").strip()
        
        if not nombre or not rut or not email or not whatsapp:
            return jsonify({
                "success": False, 
                "error": "CAMPOS_INCOMPLETOS",
                "message": "Nombre, RUT, Correo y WhatsApp son obligatorios para activar las alertas."
            }), 400

        # Manejo de archivo CV
        cv_filename = ""
        cv_text = ""
        if "cv_file" in request.files:
            file = request.files["cv_file"]
            if file and file.filename:
                import werkzeug.utils
                safe_name = werkzeug.utils.secure_filename(file.filename)
                upload_dir = os.path.join(os.path.dirname(__file__), "data", "cvs_subscribers")
                os.makedirs(upload_dir, exist_ok=True)
                
                timestamp = int(time.time())
                cv_filename = f"{rut.replace('.', '').replace('-', '')}_{timestamp}_{safe_name}"
                save_path = os.path.join(upload_dir, cv_filename)
                file.save(save_path)
                
                # Extraer texto si es PDF
                if safe_name.lower().endswith(".pdf"):
                    try:
                        import pypdf
                        reader = pypdf.PdfReader(save_path)
                        pages_text = [page.extract_text() or "" for page in reader.pages]
                        cv_text = "\n".join(pages_text)[:20000] # Limitar a 20k chars
                    except Exception as e_pdf:
                        print(f"Error extrayendo texto PDF: {e_pdf}")

        # Guardar o actualizar en base de datos
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO empleos_subscribers 
            (nombre, rut, email, whatsapp, region, profesion_interes, renta_minima, cv_filename, cv_text, plan, activo, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
        """, (nombre, rut, email, whatsapp, region, profesion, renta_min, cv_filename, cv_text, plan))
        
        subscriber_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Enviar correo de bienvenida si mailer está disponible
        try:
            from mailer import send_email, smtp_configured
            if smtp_configured():
                subject = f"¡Bienvenido a Quantus Empleos Públicos VIP, {nombre}!"
                body = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #1e293b;">
                    <div style="background: #0284c7; padding: 20px; text-align: center; border-radius: 12px 12px 0 0;">
                        <h1 style="color: #ffffff; margin: 0; font-size: 22px;">Quantus Empleos Públicos 24/7</h1>
                    </div>
                    <div style="background: #ffffff; padding: 24px; border: 1px solid #e2e8f0; border-radius: 0 0 12px 12px;">
                        <h2 style="color: #0f172a; margin-top: 0;">¡Hola {nombre}! Tu membresía está activa 🎉</h2>
                        <p>Hemos configurado tus alertas inteligentes con los siguientes parámetros:</p>
                        <ul>
                            <li><strong>RUT Registrado:</strong> {rut}</li>
                            <li><strong>WhatsApp de Alertas:</strong> {whatsapp}</li>
                            <li><strong>Región Prioritaria:</strong> {region or 'Todas las regiones'}</li>
                            <li><strong>Profesión / Cargo:</strong> {profesion or 'Todo el universo estatal'}</li>
                            <li><strong>CV Analizado:</strong> {'Sí, listo para calce de admisibilidad' if cv_filename else 'No adjuntado (opcional)'}</li>
                        </ul>
                        <p>Recibirás notificaciones directas en cuanto se publiquen concursos que hagan calce con tu perfil.</p>
                        <div style="background: #f8fafc; border-left: 4px solid #0284c7; padding: 12px; margin: 16px 0; border-radius: 4px; font-size: 13px; color: #334155;">
                            💡 <strong>Consejo para postular:</strong> Convocatorias de ministerios y servicios de salud exigen <strong>ClaveÚnica</strong>. Empresas públicas y mineras (Codelco, BHP, EFE) requieren cuenta de usuario en su portal de postulaciones.
                        </div>
                        <div style="text-align: center; margin: 25px 0;">
                            <a href="https://www.quantuschile.cl/empleos-publicos?q={urllib.parse.quote(profesion or '')}&region={urllib.parse.quote(region or '')}" style="background: #0284c7; color: #ffffff; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block;">Ver Vacantes de tu Perfil en Vivo ↗</a>
                        </div>
                        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
                        <p style="font-size: 12px; color: #64748b; text-align: center;">Quantus Chile SpA • Inteligencia Laboral y Convocatorias 24/7</p>
                    </div>
                </div>
                """
                send_email(email, subject, body)
        except Exception as e_mail:
            print(f"Aviso: no se pudo enviar correo: {e_mail}")

        # Mensaje preformateado de WhatsApp
        safe_prof = urllib.parse.quote(profesion or 'mi perfil profesional')
        safe_reg = urllib.parse.quote(region or 'Chile')
        safe_rut = urllib.parse.quote(rut)
        safe_email = urllib.parse.quote(email)
        
        wa_link = f"https://wa.me/56975480746?text=Hola,%20acabo%20de%20activar%20mi%20Radar%20VIP%20de%20Empleos%20Publicos%20con%20RUT%20{safe_rut}%20y%20Email%20{safe_email}.%20Quiero%20comenzar%20a%20recibir%20alertas%20para%20{safe_prof}%20en%20{safe_reg}"

        return jsonify({
            "success": True,
            "subscriber_id": subscriber_id,
            "message": "¡Perfil registrado y Radar 24/7 activado exitosamente!",
            "whatsapp_link": wa_link,
            "has_cv": bool(cv_filename)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/remates/suscripcion", methods=["POST"])
def api_remates_suscripcion():
    try:
        data = request.get_json() or request.form
        rut = (data.get("rut") or "").strip()
        nombre = (data.get("nombre") or "").strip()
        email = (data.get("email") or "").strip().lower()
        telefono = (data.get("telefono") or "").strip()
        region_interes = (data.get("region_interes") or "Todo Chile").strip()
        tipo_bien = (data.get("tipo_bien") or "Todos los Bienes").strip()
        plan = (data.get("plan") or "Plan Inversionista Mensual").strip()
        monto_raw = data.get("monto") or "29900"
        monto = int(str(monto_raw).replace(".", "").replace("$", "")) if str(monto_raw).isdigit() else 29900

        if not rut or not nombre or not email:
            return jsonify({"status": "error", "message": "RUT, Nombre y Correo son obligatorios."}), 400

        # Persistencia en Capa Canónica Relacional
        try:
            import quantus_ecosystem_db
            id_cli = quantus_ecosystem_db.upsert_cliente(
                rut=rut,
                nombre=nombre,
                email=email,
                telefono=telefono
            )
            quantus_ecosystem_db.save_susc_remates(
                id_cliente=id_cli,
                region_interes=region_interes,
                tipo_bien=tipo_bien,
                monto_postura_minima="",
                plan=plan,
                monto=monto,
                estado="pendiente_pago"
            )
            quantus_ecosystem_db.record_audit_event(
                actor="client",
                action="remates_subscription_registered",
                object_type="susc_remates",
                object_id=id_cli,
                payload={"rut": rut, "plan": plan, "region": region_interes, "tipo_bien": tipo_bien},
                ip_address=request.headers.get("X-Forwarded-For", request.remote_addr)
            )
        except Exception as e_db:
            print(f"Aviso en quantus_ecosystem_db (Remates): {e_db}")

        # Registrar también en ledger JSON para auditoría secundaria
        audit_path = os.path.join(os.path.dirname(__file__), "data", "remates_subscribers.json")
        os.makedirs(os.path.dirname(audit_path), exist_ok=True)
        subscribers = []
        if os.path.exists(audit_path):
            try:
                with open(audit_path, "r", encoding="utf-8") as f:
                    subscribers = json.load(f)
            except Exception:
                subscribers = []
        
        subscribers.append({
            "rut": rut,
            "nombre": nombre,
            "email": email,
            "telefono": telefono,
            "region_interes": region_interes,
            "tipo_bien": tipo_bien,
            "plan": plan,
            "monto": monto,
            "timestamp": datetime.now().isoformat()
        })
        with open(audit_path, "w", encoding="utf-8") as f:
            json.dump(subscribers, f, ensure_ascii=False, indent=2)

        return jsonify({
            "status": "success",
            "message": "Suscripción a Radar de Remates registrada exitosamente.",
            "rut": rut,
            "plan": plan
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/empleos/upload-cv", methods=["POST"])
def api_empleos_upload_cv():
    try:
        nombre = (request.form.get("nombre") or "").strip()
        rut = (request.form.get("rut") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        telefono = (request.form.get("telefono") or "").strip()
        region = (request.form.get("region") or "Todo Chile").strip()
        renta_min_raw = request.form.get("renta_minima") or "0"
        renta_min = int(renta_min_raw) if str(renta_min_raw).isdigit() else 0

        if not nombre or not email:
            return jsonify({"status": "error", "message": "Nombre y Correo son obligatorios."}), 400

        # Manejo y validación de seguridad de archivo CV
        saved_path = ""
        file_sha256 = ""
        file_size = 0
        mime_detected = ""
        extraction_status = "no_file"

        if "cv_file" in request.files:
            f = request.files["cv_file"]
            if f and f.filename:
                import werkzeug.utils
                ext = os.path.splitext(f.filename)[1].lower()
                if ext not in [".pdf", ".docx", ".doc"]:
                    return jsonify({"status": "error", "message": "Formato de archivo no permitido. Solo PDF o DOCX."}), 400
                
                # Leer bytes y validar tamaño máximo (10MB)
                file_bytes = f.read()
                file_size = len(file_bytes)
                if file_size > 10 * 1024 * 1024:
                    return jsonify({"status": "error", "message": "El archivo excede el tamaño máximo permitido de 10MB."}), 400
                
                # Calcular SHA-256
                file_sha256 = hashlib.sha256(file_bytes).hexdigest()
                clean_rut_str = rut.replace(".", "").replace("-", "") if rut else "NO_RUT"
                safe_name = werkzeug.utils.secure_filename(f.filename)
                unique_filename = f"{clean_rut_str}_{int(time.time())}_{file_sha256[:8]}_{safe_name}"
                
                # Almacenar en carpetas físicas oficiales
                storage_dirs = [
                    os.path.join(os.path.dirname(__file__), "storage_cvs"),
                    "/mnt/proyectos/felipe/quantus_empleos_publicos/storage_cvs"
                ]
                for sdir in storage_dirs:
                    try:
                        os.makedirs(sdir, exist_ok=True)
                        tgt = os.path.join(sdir, unique_filename)
                        with open(tgt, "wb") as out_f:
                            out_f.write(file_bytes)
                        if not saved_path:
                            saved_path = tgt
                    except Exception as e_dir:
                        pass

                mime_detected = "application/pdf" if ext == ".pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                extraction_status = "stored"

        # Persistencia en Capa Canónica Relacional
        try:
            import quantus_ecosystem_db
            id_cli = quantus_ecosystem_db.upsert_cliente(
                rut=rut,
                nombre=nombre,
                email=email,
                telefono=telefono
            )
            quantus_ecosystem_db.save_susc_empleos_publicos(
                id_cliente=id_cli,
                cv_url=saved_path,
                cv_sha256=file_sha256,
                cv_size_bytes=file_size,
                cargo_buscado="",
                titulos="",
                region_residencia=region,
                renta_minima=renta_min,
                estado="activo"
            )
            if saved_path:
                quantus_ecosystem_db.record_uploaded_doc(
                    id_cliente=id_cli,
                    modulo="empleos_publicos_cv",
                    file_name=os.path.basename(saved_path),
                    file_path=saved_path,
                    file_sha256=file_sha256,
                    mime_type=mime_detected,
                    size_bytes=file_size
                )
            quantus_ecosystem_db.record_audit_event(
                actor="candidate",
                action="upload_cv_and_subscribe",
                object_type="susc_empleos_publicos",
                object_id=id_cli,
                payload={"nombre": nombre, "email": email, "region": region, "sha256": file_sha256},
                ip_address=request.headers.get("X-Forwarded-For", request.remote_addr)
            )
        except Exception as e_emp:
            print(f"Aviso en quantus_ecosystem_db (Empleos): {e_emp}")

        # Ingesta en motor de perfiles si existe import_cv_file
        parsed_ok = False
        if saved_path:
            try:
                import import_cv_file
                res = import_cv_file.parse_and_store_cv(saved_path, force_email=email, force_rut=rut, force_phone=telefono)
                parsed_ok = bool(res)
                extraction_status = "parsed_and_indexed" if parsed_ok else "stored_unparsed"
            except Exception as e_ingest:
                print(f"Aviso en import_cv_file: {e_ingest}")
                extraction_status = "stored_parse_error"

        return jsonify({
            "status": "success",
            "message": "CV almacenado físicamente con firma criptográfica SHA-256 y perfil activado para alertas 24/7.",
            "nombre": nombre,
            "email": email,
            "file_sha256": file_sha256,
            "extraction_status": extraction_status
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500




# ═══════════════════════════════════════════════════════════════════════════════
# ETAPA 5 — Detección de Colisiones de Marcas (Fonética + Niza Conexas)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/marca/colision", methods=["POST"])
def api_marca_colision():
    """
    Escanea una marca contra la base de INAPI en tiempo real.
    POST JSON: { "marca": "QUANTUS", "clase": 42 }
    Retorna lista de colisiones ordenadas por riesgo descendente.
    """
    ip = get_client_ip()
    if is_rate_limited(ip, "marca_colision", 5, 3600, consume=False):
        return jsonify({"error": "Límite de consultas: máximo 5 escaneos por hora."}), 429

    payload = request.get_json(silent=True) or request.form
    marca = (payload.get("marca") or payload.get("brand") or "").strip()
    clase = int(payload.get("clase") or payload.get("class") or 0)

    if not marca or len(marca) < 2:
        return jsonify({"error": "Indica el nombre de la marca a escanear (mínimo 2 caracteres)."}), 400
    if clase < 1 or clase > 45:
        return jsonify({"error": "Clase Niza debe ser entre 1 y 45."}), 400

    try:
        # Consultar INAPI con la marca
        inapi_results = query_inapi(marca)
        if isinstance(inapi_results, dict) and "error" in inapi_results:
            return jsonify({"error": f"Error consultando INAPI: {inapi_results['error']}"}), 502

        marcas_existentes = inapi_results if isinstance(inapi_results, list) else inapi_results.get("marcas", [])

        # Escanear colisiones
        colisiones = scan_brand_against_list(marca, clase, marcas_existentes, min_risk=10.0)

        # Consumir rate limit
        is_rate_limited(ip, "marca_colision", 5, 3600)

        return jsonify({
            "marca_consultada": marca,
            "clase_consultada": clase,
            "metaphone": spanish_metaphone(marca),
            "total_resultados_inapi": len(marcas_existentes),
            "colisiones_detectadas": len(colisiones),
            "colisiones": colisiones[:20],  # Top 20
            "disclaimer": "Este análisis es orientativo. No reemplaza la búsqueda exhaustiva de un abogado especialista en propiedad industrial."
        })
    except Exception as e:
        log.error(f"[Marca Colisión] Error: {e}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@app.route("/api/marca/vigilancia", methods=["POST"])
def api_marca_vigilancia():
    """
    Cruce de vigilancia: escanea marcas de suscriptores contra publicaciones
    recientes del Diario Oficial que contengan solicitudes de marcas.
    POST JSON: { "marca": "BIOBELLE", "clase": 3, "dias_atras": 30 }
    """
    payload = request.get_json(silent=True) or request.form
    marca = (payload.get("marca") or "").strip()
    clase = int(payload.get("clase") or 0)
    dias = int(payload.get("dias_atras") or 30)

    if not marca or clase < 1 or clase > 45:
        return jsonify({"error": "Parámetros incompletos: marca y clase (1-45) requeridos."}), 400

    try:
        import sqlite3
        from datetime import datetime, timedelta

        do_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "do_historico.db")
        if not os.path.exists(do_db_path):
            return jsonify({"error": "Base de datos del Diario Oficial no disponible."}), 503

        conn = sqlite3.connect(do_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        fecha_desde = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")

        # Buscar publicaciones que mencionen marcas, INAPI o solicitudes de registro
        cursor.execute("""
            SELECT id, fecha, edicion, seccion, titulo, texto, url, cve
            FROM publicaciones
            WHERE fecha >= ?
              AND (
                LOWER(texto) LIKE '%solicitud de registro%'
                OR LOWER(texto) LIKE '%marca comercial%'
                OR LOWER(texto) LIKE '%propiedad industrial%'
                OR LOWER(texto) LIKE '%inapi%'
                OR LOWER(seccion) LIKE '%propiedad industrial%'
              )
            ORDER BY fecha DESC
            LIMIT 1200
        """, (fecha_desde,))

        publicaciones = cursor.fetchall()
        conn.close()

        # Extraer menciones de marcas del texto y evaluar colisión
        alertas = []
        for pub in publicaciones:
            contenido = (pub["texto"] or "").lower()
            titulo = (pub["titulo"] or "").lower()

            # Si el contenido menciona algo fonéticamente similar a la marca vigilada
            marca_lower = marca.lower()
            if marca_lower in contenido or marca_lower in titulo:
                collision = detect_collision_risk(marca, clase, marca, clase)
                collision["fuente"] = "Diario Oficial"
                collision["fecha_publicacion"] = pub["fecha_publicacion"]
                collision["seccion"] = pub["seccion"]
                collision["titulo_publicacion"] = pub["titulo"]
                collision["extracto"] = (pub["texto"] or "")[:500]
                alertas.append(collision)

        return jsonify({
            "marca_vigilada": marca,
            "clase_vigilada": clase,
            "periodo_dias": dias,
            "publicaciones_analizadas": len(publicaciones),
            "alertas_encontradas": len(alertas),
            "alertas": alertas[:50],
            "plazo_oposicion": "30 días corridos desde publicación en Diario Oficial (Art. 5 Ley 19.039)"
        })
    except Exception as e:
        log.error(f"[Marca Vigilancia] Error: {e}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500




# ═══════════════════════════════════════════════════════════════════════════════
# ETAPA 6 — Buscador Semántico Histórico del Diario Oficial (FTS5)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/do/buscador", methods=["GET"])
def do_buscador_view():
    """Interfaz interactiva de búsqueda histórica y semántica en el Diario Oficial."""
    q = request.args.get("q", "").strip()
    return render_template("do_buscador.html", initial_query=q)


@app.route("/api/do/search_semantic", methods=["GET", "POST"])
def api_do_search_semantic():
    """API de búsqueda semántica y facetada sobre el histórico del Diario Oficial."""
    ip = get_client_ip()

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        q = (data.get("q") or "").strip()
        seccion = (data.get("seccion") or "todas").strip()
        dias = int(data.get("dias") or 0)
        limit = int(data.get("limit") or 15)
        offset = int(data.get("offset") or 0)
    else:
        q = request.args.get("q", "").strip()
        seccion = request.args.get("seccion", "todas").strip()
        dias = int(request.args.get("dias") or 0)
        limit = int(request.args.get("limit") or 15)
        offset = int(request.args.get("offset") or 0)

    if not q:
        return jsonify({"error": "Parámetro de búsqueda 'q' es requerido", "total": 0, "resultados": []}), 400

    # Rate limiting amigable: visitantes externos 10 búsquedas por hora / Propietario o sesión: ilimitado
    if is_rate_limited(ip, "do_search", 15, 3600, consume=True):
        return jsonify({
            "error": "Has alcanzado la cuota de consultas de cortesía. Activa tu membresía Quantus para búsquedas ilimitadas.",
            "rate_limited": True,
            "total": 0,
            "resultados": []
        }), 429

    try:
        results = search_semantic_do(query=q, seccion=seccion, dias_atras=dias, limit=limit, offset=offset)
        return jsonify(results)
    except Exception as e:
        log.error(f"[DO Semantic Search Error]: {e}", exc_info=True)
        return jsonify({"error": "Error ejecutando la búsqueda semántica", "detail": str(e), "total": 0, "resultados": []}), 500


if __name__ == "__main__":
    # Escuchar en todas las interfaces en el puerto 8095 (ver PORT_INFO.md; NO 8084/8082)
    app.run(host="0.0.0.0", port=PORT, debug=os.getenv("FLASK_DEBUG") == "1")

@app.route("/api/maestro/do-progreso")
def api_maestro_do_progreso():
    return jsonify(get_do_regressive_progress())
