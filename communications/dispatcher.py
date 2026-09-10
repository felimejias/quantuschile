"""
Quantus Communications Dispatcher
---------------------------------
Capa unica de despacho de comunicaciones a clientes:

1. Renderiza plantillas (correo HTML / WhatsApp texto) desde communications/templates.
2. Aplica anti-duplicado (dedup_key) por modulo + cliente + evento + canal.
3. Envia correo via mailer (SMTP) o registra el fallo para reenvio manual.
4. Encola WhatsApp en el outbox de app.py (Meta Cloud API o cola pendiente).
5. Registra todo en el historial auditable (communications.audit_log).

Reutilizable por Diario Oficial, Licitaciones, INAPI y Remates.
"""

import json
import os
import threading
from pathlib import Path

import jinja2

from communications.audit_log import (
    already_sent,
    dedup_key_for,
    ensure_audit_storage,
    get_communication,
    mark_communication_status,
    now_iso,
    record_communication,
)
from communications.linkedin import linkedin_configured, send_linkedin
from mailer import send_email

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = BASE_DIR / "communications" / "templates"
CORPORATE_FILE = BASE_DIR / "data" / "datos_corporativos_quantus.json"
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "https://www.quantuschile.cl")
if "localhost" in PUBLIC_BASE_URL or "127.0.0.1" in PUBLIC_BASE_URL:
    PUBLIC_BASE_URL = "https://www.quantuschile.cl"
DIARIO_OFICIAL_FUENTE = "https://www.diariooficial.interior.gob.cl"

EMAIL_TEMPLATES = {
    "activation": "diario_oficial_email_activacion.html",
    "official_match_alert": "diario_oficial_match_alert_email.html",
    "weekly_clear_report": "diario_oficial_weekly_clear_email.html",
}
WHATSAPP_TEMPLATES = {
    "activation": "diario_oficial_whatsapp_activacion.txt",
    "official_match_alert": "diario_oficial_match_alert_whatsapp.txt",
    "weekly_clear_report": "diario_oficial_weekly_clear_whatsapp.txt",
}
DEFAULT_SUBJECTS = {
    "activation": "Radar Diario Oficial activado",
    "official_match_alert": "ALERTA Quantus Diario Oficial: coincidencia detectada",
    "weekly_clear_report": "Radar Diario Oficial activo: sin coincidencias esta semana",
}


def _template_env():
    loader = jinja2.FileSystemLoader(str(TEMPLATE_DIR))
    html_env = jinja2.Environment(loader=loader, autoescape=True, trim_blocks=True, lstrip_blocks=True)
    txt_env = jinja2.Environment(loader=loader, autoescape=False, trim_blocks=True, lstrip_blocks=True)
    return html_env, txt_env


def corporate_context():
    data = {}
    try:
        data = json.loads(CORPORATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    emp = data.get("empresa", {}) if isinstance(data, dict) else {}
    return {
        "empresa": emp.get("razon_social", "Quantus Chile SpA"),
        "rut_empresa": emp.get("rut", "78.478.612-9"),
        "email_contacto": emp.get("email_corporativo", "contacto@quantuschile.cl"),
        "email_privacidad": emp.get("email_privacidad_arco", "privacidad@quantuschile.cl"),
        "web": emp.get("web_oficial", "https://www.quantuschile.cl"),
    }


def recommended_lawyer():
    try:
        from do_intelligence import recommended_lawyer as _rl
        return _rl()
    except Exception:
        return None


def monitored_terms_for(client):
    terms = []
    seen = set()
    for key in ("nombre_completo", "nombre_empresa", "rut"):
        value = (client or {}).get(key)
        if value and str(value).strip() not in seen:
            seen.add(str(value).strip())
            terms.append(str(value).strip())
    for key in ("ruts_asociados", "alias_busqueda", "nombres_anteriores", "empresas_anteriores"):
        for value in (client or {}).get(key) or []:
            if value and str(value).strip() not in seen:
                seen.add(str(value).strip())
                terms.append(str(value).strip())
    return terms


def audit_retroactive_do(rut, dias=9):
    """Audita los ultimos N dias en do_historico.db para balance limpio de bienvenida."""
    if not rut:
        return f"Balance Limpio · Sin publicaciones registradas en los últimos {dias} días corridos."
    db_paths = [
        "/opt/quantus/portal/data/do_historico.db",
        "/mnt/proyectos/felipe/inapi_portal/data/do_historico.db"
    ]
    db_file = None
    for p in db_paths:
        if os.path.exists(p):
            db_file = p
            break
    if not db_file:
        return f"Balance Limpio · Sin publicaciones judiciales ni societarias en los últimos {dias} días corridos."
    try:
        clean_rut = rut.replace(".", "").replace("-", "").strip().upper()
        cutoff = (datetime.now().date() - timedelta(days=dias)).strftime("%Y-%m-%d")
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("SELECT count(*), fecha, titulo, cve FROM publicaciones WHERE (texto LIKE ? OR texto_norm LIKE ?) AND fecha >= ? LIMIT 1", (f"%{clean_rut}%", f"%{clean_rut}%", cutoff))
        row = c.fetchone()
        conn.close()
        if row and row[0] > 0:
            return f"Alerta Preventiva: Se detectó 1 publicación en el Diario Oficial el día {row[1]} (CVE: {row[3]}). Estás a tiempo para revisión y defensa legal."
    except Exception as err:
        pass
    return f"Balance Limpio · Sin publicaciones judiciales ni societarias detectadas en los últimos {dias} días corridos."

def build_context(client, payload, event_type, comm_id=None, corporate=None):
    payload = payload or {}
    client = client or {}
    corporate = corporate or corporate_context()
    nombre = (client.get("nombre") or client.get("name") or client.get("nombre_completo") or "Cliente")
    
    # 1. Evaluacion de Identidad (Los 2 Formatos Canonicos de AGENTS.md Seccion 5)
    tokens = [t for t in nombre.strip().split() if len(t) > 1]
    nombre_incompleto = payload.get("nombre_incompleto")
    if nombre_incompleto is None:
        nombre_incompleto = len(tokens) < 3

    # 2. Convenio Juridico (9 dias por defecto, o 30/60 dias con codigo de estudio)
    codigo_convenio = (payload.get("codigo_convenio") or client.get("codigo_convenio") or "").strip().upper()
    dias_auditoria = 9
    estudio_convenio = None
    if codigo_convenio:
        try:
            import quantus_ecosystem_db as db
            conv = db.get_convenio_juridico(codigo_convenio)
            if conv:
                dias_auditoria = conv.get("dias_auditoria_retroactiva", 30)
                estudio_convenio = conv.get("nombre_estudio")
        except Exception:
            pass
    if "dias_auditoria" in payload:
        dias_auditoria = payload["dias_auditoria"]
    if "estudio_convenio" in payload:
        estudio_convenio = payload["estudio_convenio"]

    # 3. Auditoria Retroactiva Inmediata
    auditoria_resultado = payload.get("auditoria_resultado")
    if not auditoria_resultado:
        auditoria_resultado = audit_retroactive_do(client.get("rut") or "", dias=dias_auditoria)
    rut = (client.get("rut") or "").strip() or "No informado"
    report_url = payload.get("report_url") or ""
    if not report_url or "diariooficial.interior.gob.cl" in report_url:
        report_url = f"/diario-oficial/informes/{comm_id or 'biobelle_20260814'}"
    report_url_abs = report_url if report_url.startswith("http") else f"{PUBLIC_BASE_URL}{report_url}"
    acciones = payload.get("acciones_recomendadas") or []
    if isinstance(acciones, str):
        acciones = [acciones]
    abogado = None
    if payload.get("recomendar_abogado", True):
        abogado = payload.get("abogado") or recommended_lawyer()
    datos_monitoreados = payload.get("datos_monitoreados") or monitored_terms_for(client)
    match_type = payload.get("match_type") or ""
    match_labels = {
        "exacta_rut": "Coincidencia exacta por RUT",
        "exacta_nombre": "Coincidencia exacta por nombre",
        "posible": "Posible coincidencia (verificar en fuente oficial)",
        "parcial": "Coincidencia parcial (posible errata en la fuente)",
        "alias": "Alias / empresa asociada",
    }
    return {
        "subject": payload.get("subject") or DEFAULT_SUBJECTS.get(event_type, "Comunicacion Quantus"),
        "cliente": nombre,
        "nombre": nombre,
        "rut": rut,
        "email": client.get("email") or "",
        "whatsapp": client.get("whatsapp") or "",
        "fecha_generacion": now_iso(),
        "informe_id": payload.get("informe_id") or comm_id or "",
        "id_comunicacion": comm_id or "",
        "report_url": report_url,
        "report_url_abs": report_url_abs,
        "fuente_oficial": payload.get("fuente_oficial") or DIARIO_OFICIAL_FUENTE,
        "tipo_publicacion": payload.get("tipo_publicacion") or "Publicacion oficial",
        "nivel_urgencia": payload.get("nivel_urgencia") or "medio",
        "resumen": (
            payload.get("resumen")
            or payload.get("resumen_ejecutivo")
            or payload.get("mensaje_cliente")
            or ""
        ),
        "mensaje_cliente": payload.get("mensaje_cliente") or "",
        "acciones": acciones[:5],
        "plazos_posibles": payload.get("plazos_posibles") or "",
        "datos_a_verificar": payload.get("datos_a_verificar") or [],
        "cruce_modules": payload.get("cruce_modules") or [],
        "match_type": match_type,
        "match_label": match_labels.get(match_type, ""),
        "abogado": abogado,
        "plan": payload.get("plan") or "",
        "plan_label": payload.get("plan_label") or "",
        "vigencia": payload.get("vigencia") or "",
        "referencia": payload.get("referencia") or "",
        "datos_monitoreados": datos_monitoreados,
        "canales_alerta": payload.get("canales_alerta") or [],
        "period_start": payload.get("period_start") or "",
        "period_end": payload.get("period_end") or "",
        "nota_semanal": "Este mensaje es un reporte preventivo de tranquilidad, no una alerta legal.",
        "nombre_incompleto": nombre_incompleto,
        "codigo_convenio": codigo_convenio,
        "dias_auditoria": dias_auditoria,
        "estudio_convenio": estudio_convenio,
        "auditoria_resultado": auditoria_resultado,
        "corp": corporate,
    }


def render_email(event_type, context):
    env, _ = _template_env()
    template = env.get_template(EMAIL_TEMPLATES[event_type])
    body = template.render(**context)
    subject = context.get("subject") or DEFAULT_SUBJECTS.get(event_type, "Comunicacion Quantus")
    return subject, body


def render_whatsapp(event_type, context):
    _, env = _template_env()
    template = env.get_template(WHATSAPP_TEMPLATES[event_type])
    return template.render(**context).strip()


def compose_linkedin(context):
    """Texto del post de LinkedIn: publicacion oficial + resumen + fuentes."""
    label = context.get("match_label") or context.get("tipo_publicacion") or "Publicacion Diario Oficial"
    lineas = [f"{label} | {context.get('cliente') or 'Cliente Quantus'}"]
    resumen = (context.get("resumen") or "").strip()
    if resumen:
        lineas.append("")
        lineas.append(resumen[:700])
    lineas.append("")
    if context.get("report_url_abs"):
        lineas.append(f"Informe completo: {context['report_url_abs']}")
    if context.get("fuente_oficial"):
        lineas.append(f"Fuente oficial: {context['fuente_oficial']}")
    lineas.append("")
    lineas.append("Publicado automaticamente por Quantus Radar.")
    return "\n".join(lineas)


def _queue_whatsapp(module, client, message, report_url):
    try:
        from app import client_key_for, queue_whatsapp_alert
    except Exception as exc:
        print(f"[Communications] No se pudo encolar WhatsApp: {exc}")
        return None
    try:
        return queue_whatsapp_alert(
            module,
            {
                "key": client.get("key") or client_key_for(module, client.get("nombre") or client.get("name"), client.get("rut"), client.get("email")),
                "nombre": client.get("nombre") or client.get("name"),
                "rut": client.get("rut"),
                "whatsapp": client.get("whatsapp"),
            },
            message,
            report_url=report_url,
            send_now=True,
        )
    except Exception as exc:
        print(f"[Communications] Error encolando WhatsApp: {exc}")
        return None


def _send_email_worker(comm_id, subject, body, to_email, attachments=None):
    try:
        ok = send_email(to_email, subject, body, attachments=attachments or None)
    except Exception as exc:
        print(f"[Communications] Error SMTP para {to_email}: {exc}")
        ok = False
    status = "sent" if ok else "failed"
    provider = "SMTP enviado" if ok else "SMTP no disponible (GMAIL_APP_PASSWORD ausente o error)"
    mark_communication_status(comm_id, status, provider_response=provider, sent_at=now_iso() if ok else None)
    return ok


def dispatch(
    module,
    event_type,
    client,
    payload=None,
    channels=("email", "whatsapp"),
    dedup_source=None,
    attachments=None,
    event_meta=None,
    manual=False,
    bypass_dedup=False,
):
    """
    Despacha una comunicacion a un cliente con auditoria y anti-duplicado.

    - module: "diario_oficial" (u otro modulo futuro).
    - event_type: activation | official_match_alert | weekly_clear_report | ...
    - client: {key, nombre, rut, email, whatsapp, whatsapp_consent, ...}
    - payload: contexto de la plantilla (tipo, urgencia, resumen, report_url, ...).
    - dedup_source: clave anti-duplicado (link de la publicacion, periodo semanal,
      id de activacion). Si se omite, se usa evento + cliente.
    - manual: True cuando el operador reenvia desde el Panel Maestro (envio inline).
    - bypass_dedup: True solo para reenvio manual explícito del operador.
    """
    ensure_audit_storage()
    payload = payload or {}
    event_meta = event_meta or {}
    client = client or {}
    client_key = client.get("key") or ""
    client_name = (client.get("nombre") or client.get("name") or "").strip()
    client_rut = (client.get("rut") or "").strip()
    email = (client.get("email") or "").strip()
    whatsapp = (client.get("whatsapp") or "").strip()
    whatsapp_consent = bool(client.get("whatsapp_consent"))
    dedup_source = dedup_source or f"{event_type}:{client_key or client_rut or client_name}"
    report_url = payload.get("report_url") or ""
    urgency = event_meta.get("urgency") or payload.get("nivel_urgencia") or ""
    results = {}
    duplicate = False

    corporate = corporate_context()
    for channel in channels:
        if channel not in ("email", "whatsapp", "linkedin"):
            continue
        dedup_key = dedup_key_for(module, client_key, dedup_source, event_type, channel)
        if not bypass_dedup and already_sent(dedup_key):
            record_communication(
                module=module, client_key=client_key, client_name=client_name,
                client_rut=client_rut, channel=channel, event_type=event_type,
                subject=DEFAULT_SUBJECTS.get(event_type, ""),
                message="", report_url=report_url, status="skipped",
                provider_response="duplicate_already_sent",
                dedup_key=dedup_key, source_hash=dedup_source, urgency=urgency,
                client=client, payload=payload, extra=event_meta,
            )
            results[channel] = {"status": "skipped_duplicate"}
            duplicate = True
            continue

        context = build_context(client, payload, event_type, corporate=corporate)

        if channel == "email":
            if not email:
                record_communication(
                    module=module, client_key=client_key, client_name=client_name,
                    client_rut=client_rut, channel=channel, event_type=event_type,
                    status="skipped", provider_response="no_email_contact",
                    dedup_key=dedup_key, source_hash=dedup_source, urgency=urgency,
                    client=client, payload=payload, extra=event_meta,
                )
                results[channel] = {"status": "skipped_no_contact"}
                continue
            subject, body = render_email(event_type, context)
            comm = record_communication(
                module=module, client_key=client_key, client_name=client_name,
                client_rut=client_rut, channel=channel, event_type=event_type,
                subject=subject, message=body, body=body, report_url=report_url,
                status="pending", dedup_key=dedup_key, source_hash=dedup_source,
                urgency=urgency, client=client, payload=payload, extra=event_meta,
            )
            if manual:
                _send_email_worker(comm["id"], subject, body, email, attachments=attachments)
                refreshed = get_communication(comm["id"])
                results[channel] = {"status": refreshed["status"], "id": comm["id"], "subject": subject}
            else:
                threading.Thread(
                    target=_send_email_worker,
                    args=(comm["id"], subject, body, email),
                    kwargs={"attachments": attachments},
                    daemon=True,
                ).start()
                results[channel] = {"status": "pending", "id": comm["id"], "subject": subject}

        elif channel == "whatsapp":
            if not (whatsapp and whatsapp_consent):
                record_communication(
                    module=module, client_key=client_key, client_name=client_name,
                    client_rut=client_rut, channel=channel, event_type=event_type,
                    status="skipped", provider_response="no_whatsapp_or_consent",
                    dedup_key=dedup_key, source_hash=dedup_source, urgency=urgency,
                    client=client, payload=payload, extra=event_meta,
                )
                results[channel] = {"status": "skipped_no_consent"}
                continue
            message = render_whatsapp(event_type, context)
            outbox_id = _queue_whatsapp(module, client, message, report_url)
            if outbox_id:
                record_communication(
                    module=module, client_key=client_key, client_name=client_name,
                    client_rut=client_rut, channel=channel, event_type=event_type,
                    subject=DEFAULT_SUBJECTS.get(event_type, ""), message=message,
                    report_url=report_url, status="queued",
                    provider_response=f"outbox_id={outbox_id}",
                    dedup_key=dedup_key, source_hash=dedup_source, urgency=urgency,
                    client=client, payload=payload, extra=event_meta,
                )
                results[channel] = {"status": "queued", "outbox_id": outbox_id}
            else:
                record_communication(
                    module=module, client_key=client_key, client_name=client_name,
                    client_rut=client_rut, channel=channel, event_type=event_type,
                    subject=DEFAULT_SUBJECTS.get(event_type, ""), message=message,
                    report_url=report_url, status="skipped",
                    provider_response="whatsapp_queue_failed",
                    dedup_key=dedup_key, source_hash=dedup_source, urgency=urgency,
                    client=client, payload=payload, extra=event_meta,
                )
                results[channel] = {"status": "skipped_no_whatsapp"}

        elif channel == "linkedin":
            if not linkedin_configured():
                record_communication(
                    module=module, client_key=client_key, client_name=client_name,
                    client_rut=client_rut, channel=channel, event_type=event_type,
                    subject=DEFAULT_SUBJECTS.get(event_type, ""), message="",
                    report_url=report_url, status="skipped",
                    provider_response="linkedin_pending_config",
                    dedup_key=dedup_key, source_hash=dedup_source, urgency=urgency,
                    client=client, payload=payload, extra=event_meta,
                )
                results[channel] = {"status": "skipped_pending_config"}
                continue
            message = compose_linkedin(context)
            ok, detail = send_linkedin(message, report_url)
            if ok:
                record_communication(
                    module=module, client_key=client_key, client_name=client_name,
                    client_rut=client_rut, channel=channel, event_type=event_type,
                    subject=DEFAULT_SUBJECTS.get(event_type, ""), message=message,
                    report_url=report_url, status="sent",
                    provider_response=detail,
                    dedup_key=dedup_key, source_hash=dedup_source, urgency=urgency,
                    client=client, payload=payload, extra=event_meta,
                )
                results[channel] = {"status": "sent", "detail": detail}
            else:
                record_communication(
                    module=module, client_key=client_key, client_name=client_name,
                    client_rut=client_rut, channel=channel, event_type=event_type,
                    subject=DEFAULT_SUBJECTS.get(event_type, ""), message=message,
                    report_url=report_url, status="failed",
                    provider_response=detail,
                    dedup_key=dedup_key, source_hash=dedup_source, urgency=urgency,
                    client=client, payload=payload, extra=event_meta,
                )
                results[channel] = {"status": "failed", "detail": detail}

    return {
        "module": module,
        "event_type": event_type,
        "dedup_key": dedup_key_for(module, client_key, dedup_source, event_type, "email"),
        "dedup_source": dedup_source,
        "duplicate": duplicate,
        "channels": results,
    }


def resend(comm_id):
    """Reenvio manual desde Panel Maestro. Genera un nuevo evento auditado."""
    comm = get_communication(comm_id)
    if not comm:
        return {"error": "Comunicacion no encontrada."}
    if comm["status"] == "sent":
        return {"error": "Esta comunicacion ya fue entregada; no se reenvia para evitar duplicados."}
    if comm["channel"] not in ("email", "whatsapp", "linkedin"):
        return {"error": "Este canal no admite reenvio manual."}

    payload = {}
    try:
        payload = json.loads(comm.get("payload_json") or "{}")
    except Exception:
        pass
    client = {}
    try:
        client = json.loads(comm.get("client_json") or "{}")
    except Exception:
        pass

    result = dispatch(
        module=comm["module"],
        event_type=comm["event_type"],
        client=client,
        payload=payload,
        channels=(comm["channel"],),
        dedup_source=comm.get("source_hash") or comm.get("dedup_key") or "resend",
        manual=True,
        bypass_dedup=True,
    )
    return {
        "comm": comm,
        "result": result,
        "note": "Reenvio manual creado como nuevo evento auditable (no reemplaza el registro original).",
    }
