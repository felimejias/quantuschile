"""
Quantus Communications Audit Log
--------------------------------
Registro auditable y anti-duplicado de todas las comunicaciones con clientes
(correo, whatsapp, pdf, portal). Base reutilizable por todos los modulos
(Diario Oficial, Licitaciones, INAPI, Remates).

Anti-spam / idempotencia:

    dedup_key = sha256(module + client_key + source_hash + event_type + channel)

Si ya existe una comunicacion activa ('sent', 'queued' o 'pending') para esa
clave, no se envia de nuevo de forma automatica; se registra un evento
'skipped' con motivo duplicate. El reenvio manual desde el Panel Maestro crea
un nuevo evento auditado.
"""

import hashlib
import json
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "do_intelligence.sqlite3"

CHANNELS = ("email", "whatsapp", "linkedin", "pdf", "portal")
EVENT_TYPES = (
    "activation",
    "official_match_alert",
    "weekly_clear_report",
    "report_ready",
    "expiration_notice",
    "cancellation",
    "internal_notice",
)


def now_iso():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_audit_storage():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS communications_log (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                module TEXT NOT NULL,
                client_key TEXT,
                client_name TEXT,
                client_rut TEXT,
                channel TEXT NOT NULL,
                event_type TEXT NOT NULL,
                subject TEXT,
                message_preview TEXT,
                body TEXT,
                report_url TEXT,
                status TEXT NOT NULL,
                provider_response TEXT,
                sent_at TEXT,
                dedup_key TEXT,
                source_hash TEXT,
                period_start TEXT,
                period_end TEXT,
                monitored_terms_count INTEGER NOT NULL DEFAULT 0,
                matches_found INTEGER,
                urgency TEXT,
                client_json TEXT,
                payload_json TEXT,
                extra_json TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_comm_log_created ON communications_log(created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_comm_log_client ON communications_log(client_key)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_comm_log_dedup ON communications_log(dedup_key, status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_comm_log_chan_status ON communications_log(channel, status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_comm_log_event ON communications_log(event_type)")


def dedup_key_for(module, client_key, source_hash, event_type, channel):
    raw = "|".join(str(value or "").strip().lower() for value in (module, client_key, source_hash, event_type, channel))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def already_sent(dedup_key):
    """
    True si el evento ya fue procesado para esta clave anti-duplicado:
    'sent' (entregada), 'queued' (whatsapp en cola), 'pending' (envio en curso),
    'failed' o 'error' (intento fallido). Asi un mismo hallazgo nunca se
    vuelve a despachar automaticamente; el operador puede reenviarlo
    manualmente desde el Panel Maestro.
    """
    ensure_audit_storage()
    if not dedup_key:
        return False
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT id FROM communications_log WHERE dedup_key = ? AND status IN ('sent', 'queued', 'pending', 'failed', 'error') LIMIT 1",
            (dedup_key,),
        ).fetchone()
        return bool(row)


def record_communication(
    module,
    client_key,
    client_name,
    client_rut,
    channel,
    event_type,
    subject="",
    message="",
    body="",
    report_url="",
    status="pending",
    provider_response="",
    dedup_key="",
    source_hash="",
    period_start="",
    period_end="",
    monitored_terms_count=0,
    matches_found=None,
    urgency="",
    client=None,
    payload=None,
    extra=None,
):
    ensure_audit_storage()
    comm_id = secrets.token_hex(12)
    created_at = now_iso()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO communications_log (
                id, created_at, module, client_key, client_name, client_rut, channel,
                event_type, subject, message_preview, body, report_url, status,
                provider_response, sent_at, dedup_key, source_hash, period_start,
                period_end, monitored_terms_count, matches_found, urgency,
                client_json, payload_json, extra_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                comm_id,
                created_at,
                module,
                client_key,
                client_name,
                client_rut,
                channel,
                event_type,
                subject,
                (message or "")[:400],
                body,
                report_url,
                status,
                provider_response,
                "" if status == "pending" else created_at,
                dedup_key,
                source_hash,
                period_start,
                period_end,
                int(monitored_terms_count or 0),
                matches_found,
                urgency,
                json.dumps(client or {}, ensure_ascii=False),
                json.dumps(payload or {}, ensure_ascii=False),
                json.dumps(extra or {}, ensure_ascii=False),
            ),
        )
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM communications_log WHERE id = ?", (comm_id,)).fetchone()
    return dict(row)


def mark_communication_status(comm_id, status, provider_response=None, sent_at=None):
    ensure_audit_storage()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            UPDATE communications_log
            SET status = ?, provider_response = ?, sent_at = COALESCE(?, sent_at)
            WHERE id = ?
            """,
            (status, provider_response, sent_at or (now_iso() if status in {"sent", "failed", "error"} else None), comm_id),
        )
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM communications_log WHERE id = ?", (comm_id,)).fetchone()
    return dict(row) if row else None


def get_communication(comm_id):
    ensure_audit_storage()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM communications_log WHERE id = ?", (comm_id,)).fetchone()
    return dict(row) if row else None


def _parse_json(value, fallback=None):
    try:
        parsed = json.loads(value or "null")
        return parsed if isinstance(parsed, dict) else (fallback or {})
    except Exception:
        return fallback or {}


def list_communications(
    limit=60,
    module=None,
    client_key=None,
    channel=None,
    status=None,
    event_type=None,
    search=None,
):
    ensure_audit_storage()
    clauses = []
    params = []
    if module:
        clauses.append("module = ?")
        params.append(module)
    if client_key:
        clauses.append("client_key = ?")
        params.append(client_key)
    if channel:
        clauses.append("channel = ?")
        params.append(channel)
    if status:
        clauses.append("status = ?")
        params.append(status)
    if event_type:
        clauses.append("event_type = ?")
        params.append(event_type)
    if search:
        clauses.append("(client_name LIKE ? OR client_rut LIKE ? OR subject LIKE ?)")
        like = f"%{search}%"
        params.extend([like, like, like])
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = [dict(row) for row in conn.execute(
            f"SELECT * FROM communications_log{where} ORDER BY created_at DESC LIMIT ?",
            (*params, int(limit)),
        ).fetchall()]
        totals = dict(conn.execute(
            f"SELECT COUNT(*) AS total, "
            f"SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) AS sent, "
            f"SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed, "
            f"SUM(CASE WHEN status IN ('pending','queued','pending_config') THEN 1 ELSE 0 END) AS pending, "
            f"SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) AS skipped "
            f"FROM communications_log{where}",
            params,
        ).fetchone())
    return rows, totals


def communications_snapshot(
    limit=60,
    module=None,
    client_key=None,
    channel=None,
    status=None,
    event_type=None,
    search=None,
):
    items, totals = list_communications(
        limit=limit,
        module=module,
        client_key=client_key,
        channel=channel,
        status=status,
        event_type=event_type,
        search=search,
    )
    resendable_statuses = {"failed", "error", "pending_config", "skipped", "queued", "pending"}
    for item in items:
        item["resendable"] = (
            item.get("channel") in {"email", "whatsapp"}
            and item.get("status") in resendable_statuses
        )
    return {
        "items": items,
        "totals": totals,
        "channels": list(CHANNELS),
        "event_types": list(EVENT_TYPES),
        "filters": {
            "module": module or "",
            "client_key": client_key or "",
            "client": search or "",
            "channel": channel or "",
            "status": status or "",
            "event": event_type or "",
        },
    }
