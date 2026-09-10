"""
Quantus Delivery Health
-----------------------
Monitorea la salud de las entregas (correo + WhatsApp) y dispara una
alarma interna al administrador cuando existen envios fallidos o
pendientes de configuracion. Reutilizable desde cron y desde el panel
Maestro (route /maestro/salud-entregas).
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

from communications.audit_log import communications_snapshot
from mailer import send_email

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _smtp_status():
    from mailer import smtp_configured
    return {
        "configured": smtp_configured(),
        "user": os.environ.get("GMAIL_USER", "contacto@quantuschile.cl"),
    }


def _whatsapp_status():
    try:
        from app import whatsapp_enabled, load_meta_whatsapp_config
    except Exception:
        return {"configured": False, "note": "app no disponible"}
    env_ok = bool(os.environ.get("WHATSAPP_ACCESS_TOKEN") and os.environ.get("WHATSAPP_PHONE_NUMBER_ID"))
    per_client = 0
    try:
        from app import iter_client_workspace_metadata
        for folder, _ in iter_client_workspace_metadata():
            if whatsapp_enabled(load_meta_whatsapp_config(folder)):
                per_client += 1
    except Exception:
        pass
    return {"configured": env_ok or per_client > 0, "env": env_ok, "clientes_config": per_client}


def _outbox_status():
    try:
        from app import whatsapp_outbox_snapshot
        snap = whatsapp_outbox_snapshot(limit=50)
        items = snap.get("items", [])
        stuck = [i for i in items if i.get("status") in {"pending_config", "error", "failed"}]
        return {"total": snap.get("total", 0), "sent": snap.get("sent", 0),
                "pending": snap.get("pending", 0), "stuck": stuck}
    except Exception as exc:
        return {"error": str(exc)[:200], "stuck": []}


def delivery_health_snapshot(hours=24):
    from communications.audit_log import now_iso
    email = communications_snapshot(limit=40, channel="email")
    whatsapp = communications_snapshot(limit=40, channel="whatsapp")
    failed_recent = [i for i in email["items"] if i.get("status") in {"failed", "error"}] + \
                    [i for i in whatsapp["items"] if i.get("status") in {"failed", "error"}]
    pending_recent = [i for i in email["items"] if i.get("status") in {"pending_config", "pending", "queued"}] + \
                     [i for i in whatsapp["items"] if i.get("status") in {"pending_config", "pending", "queued"}]
    return {
        "generado": now_iso(),
        "smtp": _smtp_status(),
        "whatsapp": _whatsapp_status(),
        "outbox": _outbox_status(),
        "email": {"totals": email["totals"], "items": email["items"][:10]},
        "whatsapp_log": {"totals": whatsapp["totals"], "items": whatsapp["items"][:10]},
        "failed_recent": failed_recent[:10],
        "pending_recent": pending_recent[:10],
    }


def has_issues(snapshot=None):
    snapshot = snapshot or delivery_health_snapshot()
    if not snapshot["smtp"]["configured"]:
        return True, "SMTP no configurado (GMAIL_APP_PASSWORD ausente)."
    if not snapshot["whatsapp"]["configured"]:
        return True, "WhatsApp Business API no configurada (sin credenciales Meta)."
    if snapshot["failed_recent"]:
        return True, f"{len(snapshot['failed_recent'])} envio(s) fallidos recientes."
    if snapshot["outbox"].get("stuck"):
        return True, f"{len(snapshot['outbox']['stuck'])} WhatsApp(s) atascado(s) en el outbox."
    return False, "Sin problemas detectados."


def alert_if_issues(silent_if_ok=True):
    snapshot = delivery_health_snapshot()
    has, reason = has_issues(snapshot)
    if not has and silent_if_ok:
        print(f"[DeliveryHealth] OK: {reason}")
        return {"alerted": False, "reason": reason}
    admin_email = os.environ.get("QUANTUS_MASTER_EMAIL", "felipe.mejias.g@gmail.com")
    failed_rows = ""
    for item in snapshot["failed_recent"][:8]:
        failed_rows += (f"<li><b>{item.get('client_name') or '?'}</b> ({item.get('module')} / "
                        f"{item.get('channel')}) · <code>{item.get('status')}</code> · "
                        f"{item.get('provider_response') or ''} · {item.get('created_at') or ''}</li>")
    stuck_rows = ""
    for item in snapshot["outbox"].get("stuck", [])[:8]:
        stuck_rows += (f"<li><b>{item.get('client_name') or '?'}</b> · <code>{item.get('status')}</code> · "
                       f"{item.get('whatsapp') or ''} · {item.get('created_at') or ''}</li>")
    body = (
        "<h2>Alerta de salud de entregas Quantus</h2>"
        f"<p><b>Estado:</b> {reason}</p>"
        f"<p><b>SMTP:</b> {'OK' if snapshot['smtp']['configured'] else 'NO configurado'} "
        f"({snapshot['smtp']['user']})</p>"
        f"<p><b>WhatsApp API:</b> {'OK' if snapshot['whatsapp']['configured'] else 'NO configurada'} "
        f"({snapshot['whatsapp'].get('clientes_config', 0)} cliente(s) con Meta configurado)</p>"
        f"<p><b>Outbox WhatsApp:</b> total={snapshot['outbox'].get('total')}, "
        f"enviados={snapshot['outbox'].get('sent')}, atascados={len(snapshot['outbox'].get('stuck', []))}</p>"
        "<h3>Envios fallidos recientes</h3><ul>"
        + (failed_rows or "<li>Ninguno</li>") + "</ul>"
        "<h3>WhatsApp atascados (pending_config/error)</h3><ul>"
        + (stuck_rows or "<li>Ninguno</li>") + "</ul>"
        "<p><i>Panel de salud: iniciar sesion en el Centro Maestro → Salud de entregas.</i></p>"
    )
    try:
        ok = send_email(admin_email, "[Quantus] Alerta de entregas: " + reason[:80], body)
    except Exception as exc:
        ok = False
        print(f"[DeliveryHealth] Error enviando alerta interna: {exc}")
    print(f"[DeliveryHealth] Alerta interna a {admin_email}: {'enviada' if ok else 'FALLO'} ({reason})")
    return {"alerted": True, "reason": reason, "email_sent": ok, "admin": admin_email}


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
    alert_if_issues(silent_if_ok=False)
