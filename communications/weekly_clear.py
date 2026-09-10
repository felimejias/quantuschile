"""
Reporte semanal de tranquilidad - Radar Diario Oficial
------------------------------------------------------
Evento: weekly_clear_report

Objetivo psicologico: que el cliente sienta acompanamiento y proteccion
activa sin fatiga. Distinto de las alertas reales (official_match_alert):
tono tranquilo, sin la palabra ALERTA y con diseno diferente.

Reglas anti-fatiga:
- maximo 1 envio por semana por cliente (dedup por periodo semanal);
- no se envia si hubo una alerta real muy reciente (lookback configurable);
- preferentemente lunes o viernes en horario laboral (el operador agenda el
  cron; el dedup por periodo impide envios duplicados);
- la alerta real siempre destaca por asunto, apertura, prioridad, PDF y accion.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PEOPLE_FILE = BASE_DIR / "do_people.json"
WEEKLY_CLEAR_ALERT_LOOKBACK_DAYS = int(os.getenv("WEEKLY_CLEAR_ALERT_LOOKBACK_DAYS", "3"))

ACTIVE_STATES = {"activo", "activo_permanente", "activo_sin_vencimiento"}


def period_key_for(period_start):
    iso = period_start.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def monitored_terms_for(person):
    terms = []
    seen = set()
    for key in ("nombre_completo", "nombre_empresa", "rut"):
        value = person.get(key)
        if value and str(value).strip().lower() not in seen:
            seen.add(str(value).strip().lower())
            terms.append(str(value).strip())
    for key in ("ruts_asociados", "alias_busqueda", "nombres_anteriores", "empresas_anteriores"):
        for value in person.get(key) or []:
            if value and str(value).strip().lower() not in seen:
                seen.add(str(value).strip().lower())
                terms.append(str(value).strip())
    return terms


def recent_real_alert_sent(client_key, since_iso):
    """True si existe una alerta real entregada ('sent') para el cliente desde `since_iso`."""
    try:
        from communications.audit_log import ensure_audit_storage, DB_PATH
        import sqlite3
        ensure_audit_storage()
        with sqlite3.connect(DB_PATH) as conn:
            row = conn.execute(
                """
                SELECT id FROM communications_log
                WHERE client_key = ? AND event_type = 'official_match_alert'
                  AND status = 'sent' AND created_at >= ?
                LIMIT 1
                """,
                (client_key, since_iso),
            ).fetchone()
            return bool(row)
    except Exception:
        return False


def run_weekly_clear_report(dry_run=False):
    from communications.dispatcher import dispatch

    people = []
    if PEOPLE_FILE.exists():
        people = json.loads(PEOPLE_FILE.read_text(encoding="utf-8"))

    today = datetime.now().date()
    period_start = today - timedelta(days=today.weekday())
    period_end = today
    period_key = period_key_for(period_start)
    since_iso = (today - timedelta(days=WEEKLY_CLEAR_ALERT_LOOKBACK_DAYS)).strftime("%Y-%m-%d %H:%M:%S")

    results = {"period_start": period_start.strftime("%Y-%m-%d"), "period_end": period_end.strftime("%Y-%m-%d"),
               "period_key": period_key, "checked": 0, "sent": 0, "skipped_recent_alert": 0, "errors": 0, "items": []}

    for person in people:
        estado = (person.get("estado") or "").strip().lower()
        plan = (person.get("plan") or "").strip().lower()
        if estado not in ACTIVE_STATES and plan not in {"gratis_maestro", "grupo_familiar_24x7"}:
            continue
        email = (person.get("alertar_a") or person.get("email") or "").strip()
        if not email:
            continue

        results["checked"] += 1
        nombre = person.get("nombre_completo") or person.get("nombre_empresa") or "Cliente"
        rut = person.get("rut") or ""
        client_key = None
        try:
            from app import client_key_for
            client_key = client_key_for("diario_oficial", nombre, rut, email)
        except Exception:
            client_key = ""
        client = {
            "key": client_key,
            "nombre": nombre,
            "rut": rut,
            "email": email,
            "whatsapp": person.get("whatsapp") or "",
            "whatsapp_consent": bool(person.get("whatsapp_consent")),
            "nombre_completo": nombre,
            "ruts_asociados": person.get("ruts_asociados") or [],
            "alias_busqueda": person.get("alias_busqueda") or [],
            "nombres_anteriores": person.get("nombres_anteriores") or [],
            "empresas_anteriores": person.get("empresas_anteriores") or [],
        }

        if recent_real_alert_sent(client_key, since_iso):
            results["skipped_recent_alert"] += 1
            results["items"].append({"nombre": nombre, "rut": rut, "result": "skipped_recent_alert"})
            continue

        terms = monitored_terms_for(person)
        payload = {
            "datos_monitoreados": terms,
            "period_start": period_start.strftime("%Y-%m-%d"),
            "period_end": period_end.strftime("%Y-%m-%d"),
        }
        event_meta = {
            "period_start": period_start.strftime("%Y-%m-%d"),
            "period_end": period_end.strftime("%Y-%m-%d"),
            "monitored_terms_count": len(terms),
            "matches_found": 0,
        }
        if dry_run:
            results["items"].append({"nombre": nombre, "rut": rut, "result": "dry_run"})
            continue

        outcome = dispatch(
            "diario_oficial",
            "weekly_clear_report",
            client,
            payload=payload,
            dedup_source=f"weekly:{period_key}",
            event_meta=event_meta, manual=True,
        )
        sent_any = any(ch.get("status") in {"pending", "queued"} for ch in outcome.get("channels", {}).values())
        results["items"].append({"nombre": nombre, "rut": rut, "result": outcome})
        if sent_any:
            results["sent"] += 1
        print(f"[Weekly Clear] {nombre} ({rut or 'sin rut'}): {outcome.get('channels')}")

    return results


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    result = run_weekly_clear_report(dry_run=dry)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
