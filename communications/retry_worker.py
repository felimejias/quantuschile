"""
Quantus Retry Worker
--------------------
Reintenta automaticamente envios que quedaron sin entregar:

- Emails: communications_log con status 'failed'/'error' de los ultimos
  MAX_AGE_DAYS dias. Maximo MAX_ATTEMPTS intentos (contador en extra_json).
- WhatsApp: whatsapp_outbox con status 'pending_config'/'error'. Solo se
  envia cuando la configuracion de Meta existe (whatsapp_enabled). Se
  omiten errores permanentes del proveedor (token invalido, plantilla no
  aprobada) para no golpear la API.

Se ejecuta desde cron (cada hora) antes de la revision de salud de entregas.
"""

import json
import os
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

from communications.audit_log import DB_PATH, ensure_audit_storage, now_iso
from mailer import send_email

MAX_ATTEMPTS = 3
MAX_AGE_DAYS = 7
PERMANENT_ERROR_PATTERNS = re.compile(
    r"invalid|unauthorized|not approved|login|permission|disabled", re.IGNORECASE
)


def _load_extra(extra_json):
    try:
        data = json.loads(extra_json or "{}")
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def retry_failed_emails(limit=20, dry_run=False):
    ensure_audit_storage()
    cutoff = (datetime.now() - timedelta(days=MAX_AGE_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = [dict(r) for r in conn.execute(
            """
            SELECT * FROM communications_log
            WHERE channel = 'email' AND status IN ('failed', 'error') AND created_at >= ?
            ORDER BY created_at ASC LIMIT ?
            """,
            (cutoff, int(limit)),
        ).fetchall()]
    results = {"attempted": 0, "sent": 0, "still_failed": 0, "skipped": 0, "items": []}
    for comm in rows:
        attempts = _load_extra(comm.get("extra_json")).get("retry_attempts", 0)
        if attempts >= MAX_ATTEMPTS:
            results["skipped"] += 1
            results["items"].append({"id": comm["id"], "result": "max_attempts"})
            continue
        try:
            client = json.loads(comm.get("client_json") or "{}")
        except Exception:
            client = {}
        email = (client.get("email") or "").strip()
        body = comm.get("body") or comm.get("message") or ""
        if not email or not body:
            results["skipped"] += 1
            results["items"].append({"id": comm["id"], "result": "no_contact_or_body"})
            continue
        results["attempted"] += 1
        attempts += 1
        if dry_run:
            results["items"].append({"id": comm["id"], "result": "dry_run", "to": email})
            continue
        ok = send_email(email, comm.get("subject") or "Comunicacion Quantus", body)
        extra = _load_extra(comm.get("extra_json"))
        extra["retry_attempts"] = attempts
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                """
                UPDATE communications_log
                SET status = ?, provider_response = ?, sent_at = ?, extra_json = ?
                WHERE id = ?
                """,
                (
                    "sent" if ok else "failed",
                    f"Reintento automatico {attempts}/{MAX_ATTEMPTS}: {'OK' if ok else 'fallo SMTP'}",
                    now_iso() if ok else None,
                    json.dumps(extra, ensure_ascii=False),
                    comm["id"],
                ),
            )
        if ok:
            results["sent"] += 1
        else:
            results["still_failed"] += 1
        results["items"].append({"id": comm["id"], "result": "sent" if ok else "failed", "to": email})
    print(f"[RetryWorker] Emails: intentados={results['attempted']} enviados={results['sent']} "
          f"aun_fallidos={results['still_failed']} omitidos={results['skipped']}")
    return results


def retry_whatsapp_outbox(limit=20, dry_run=False):
    cutoff = (datetime.now() - timedelta(days=MAX_AGE_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = [dict(r) for r in conn.execute(
            """
            SELECT * FROM whatsapp_outbox
            WHERE status IN ('pending_config', 'error') AND created_at >= ?
            ORDER BY created_at ASC LIMIT ?
            """,
            (cutoff, int(limit)),
        ).fetchall()]
    if not rows:
        print("[RetryWorker] WhatsApp: nada que reintentar.")
        return {"attempted": 0, "sent": 0, "skipped": 0, "items": []}
    try:
        from app import load_meta_whatsapp_for_outbox_row, send_whatsapp_outbox_item, whatsapp_enabled
    except Exception as exc:
        print(f"[RetryWorker] WhatsApp: app no disponible: {exc}")
        return {"attempted": 0, "sent": 0, "skipped": 0, "items": []}
    results = {"attempted": 0, "sent": 0, "skipped": 0, "items": []}
    for row in rows:
        provider = (row.get("provider_response") or "")
        if row.get("status") == "error" and PERMANENT_ERROR_PATTERNS.search(provider):
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("UPDATE whatsapp_outbox SET status = 'failed_permanent' WHERE id = ?", (row["id"],))
            results["skipped"] += 1
            results["items"].append({"id": row["id"], "result": "permanent_error"})
            continue
        config = load_meta_whatsapp_for_outbox_row(row)
        if not whatsapp_enabled(config):
            results["skipped"] += 1
            results["items"].append({"id": row["id"], "result": "sin_config_meta"})
            continue
        results["attempted"] += 1
        if dry_run:
            results["items"].append({"id": row["id"], "result": "dry_run"})
            continue
        try:
            ok = send_whatsapp_outbox_item(row["id"])
        except Exception as exc:
            ok = False
            print(f"[RetryWorker] Error enviando outbox {row['id']}: {exc}")
        if ok:
            results["sent"] += 1
        results["items"].append({"id": row["id"], "result": "sent" if ok else "failed"})
    print(f"[RetryWorker] WhatsApp: intentados={results['attempted']} enviados={results['sent']} "
          f"omitidos={results['skipped']}")
    return results


def run_retries(limit=20, dry_run=False):
    emails = retry_failed_emails(limit=limit, dry_run=dry_run)
    whatsapp = retry_whatsapp_outbox(limit=limit, dry_run=dry_run)
    return {"emails": emails, "whatsapp": whatsapp}


if __name__ == "__main__":
    run_retries(dry_run=True)
