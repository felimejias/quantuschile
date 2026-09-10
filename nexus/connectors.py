# -*- coding: utf-8 -*-
"""QUANTUS NEXUS — Conectores read-only a todos los sistemas.
Cada función devuelve un dict con {ok, datos|error} y nunca modifica nada."""
import json
import os
from datetime import datetime

NEXUS_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(NEXUS_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")


def _leer_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _ultima_linea(path, n=1):
    try:
        with open(path, encoding="utf-8") as f:
            lineas = [l.strip() for l in f.read().splitlines() if l.strip()]
        return lineas[-n:] if lineas else []
    except Exception:
        return []


def _ultimo_mtime(path):
    try:
        return datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return ""


def conector_web():
    """Salud del sitio: uptime de producción + auditoría QA + respuesta en vivo."""
    uptime = _leer_json(os.path.join(DATA_DIR, "uptime_state.json")) or {}
    qa_bugs = _leer_json(os.path.join(DATA_DIR, "qa_bugs_log.json")) or []
    abiertos = [b for b in qa_bugs if b.get("severidad") != "INFO"]
    criticos = sum(1 for b in abiertos if b.get("severidad") == "CRÍTICA")
    altos = sum(1 for b in abiertos if b.get("severidad") == "ALTA")
    qa_ts = max([b.get("timestamp", "") for b in qa_bugs] or [""])
    return {
        "ok": True,
        "produccion": {
            "estado": uptime.get("estado", "sin datos"),
            "ultimo_check": uptime.get("ultimo_check", ""),
            "detalle": uptime.get("detalle", ""),
        },
        "qa": {
            "abiertos": len(abiertos),
            "criticos": criticos,
            "altos": altos,
            "ultima_auditoria": qa_ts,
        },
        "origen": "uptime_state.json + qa_bugs_log.json",
    }


def conector_entregas():
    """Correo + WhatsApp: health snapshot de la capa de comunicaciones."""
    try:
        from communications.delivery_health import delivery_health_snapshot

        snap = delivery_health_snapshot(hours=24)
        outbox = snap.get("outbox", {})
        email = snap.get("email", {})
        return {
            "ok": True,
            "smtp": snap.get("smtp", {}),
            "whatsapp": snap.get("whatsapp", {}),
            "outbox": outbox,
            "email": {
                "total": email.get("totals", {}).get("total", 0),
                "enviados": email.get("totals", {}).get("sent", 0),
                "fallidos": email.get("totals", {}).get("failed", 0),
                "pendientes": email.get("totals", {}).get("pending", 0),
            },
            "generado": snap.get("generado", ""),
            "origen": "delivery_health_snapshot()",
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}


def conector_do():
    """Radar Diario Oficial: histórico indexado, edición del día, clientes activos, último cron."""
    resumen = {}
    try:
        from do_historico import resumen

        resumen = resumen() or {}
    except Exception:
        pass
    estado = _leer_json(os.path.join(DATA_DIR, "do_ediciones", "estado.json")) or {}
    people = _leer_json(os.path.join(BASE_DIR, "do_people.json")) or []
    lista = people if isinstance(people, list) else people.get("personas", people.get("clients", []))
    activos = sum(1 for p in lista if p.get("estado", "inactivo") == "activo")
    mon = _ultima_linea(os.path.join(LOGS_DIR, "do_monitor.log"), 2)
    desc = _ultima_linea(os.path.join(LOGS_DIR, "do_downloader.log"), 2)
    return {
        "ok": True,
        "historico": resumen,
        "edicion_dia": {"fecha": estado.get("fecha", ""), "edicion": estado.get("edicion", "")},
        "clientes_activos": activos,
        "ultimo_cron_monitor": " | ".join(mon),
        "ultimo_cron_descarga": " | ".join(desc),
        "origen": "do_historico.db + estado.json + do_people.json",
    }


def conector_erp():
    """ERP (solo lectura): sincronización de registro vía puente; requiere LXC/docker (servidor)."""
    try:
        from app import sync_registry_from_erp

        sincronizados = sync_registry_from_erp()
        return {
            "ok": True,
            "sincronizados": sincronizados,
            "nota": "puente read-only psql (LXC 100 / quantus_demo)",
            "origen": "sync_registry_from_erp()",
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc)[:160],
            "nota": "requiere pct/docker del servidor: en la Mac solo lectura local; el panel superadmin sigue en el servidor.",
            "origen": "sync_registry_from_erp()",
        }


def conector_infra():
    """Cron local: última ejecución y salud de cada worker + puerto de la web."""
    logs = [
        ("Descarga DO", "do_downloader.log"),
        ("Monitor DO", "do_monitor.log"),
        ("Delivery Health", "delivery_health.log"),
        ("Auditoría QA", "qa_auditor.log"),
        ("Keepalive web", "keepalive.log"),
        ("Uptime producción", "uptime.log"),
        ("Briefing Nexus", "nexus_briefing.log"),
    ]
    filas = []
    for nombre, archivo in logs:
        path = os.path.join(LOGS_DIR, archivo)
        filas.append({"nombre": nombre, "ultimo": _ultimo_mtime(path), "linea": _ultima_linea(path, 1)})
    web_up = False
    try:
        import urllib.request

        urllib.request.urlopen("http://127.0.0.1:8095/", timeout=3)
        web_up = True
    except Exception:
        pass
    return {"ok": True, "workers": filas, "web_local_up": web_up, "origen": "logs/"}


def conector_maestro():
    """MAESTRO en modo lectura pura: clientes DO, pagos, riesgos IA, registro ERP.
    Replica KPIs del panel maestro sin ninguna escritura (sin persist/lifecycle)."""
    try:
        from do_intelligence import dashboard_snapshot, registry_snapshot
        from app import (
            do_subscription_state,
            load_do_payment_events,
            load_do_people,
        )

        people = load_do_people()
        total = len(people)
        activos = sum(
            1 for p in people
            if do_subscription_state(p) in {"activo", "activo_permanente", "activo_sin_vencimiento"}
        )
        eventos = load_do_payment_events()
        pendientes = sum(
            1 for e in eventos
            if (e.get("estado") or e.get("status") or "").lower()
            in {"pendiente", "pending", "expirado", "fallido", "failed"}
        )
        pagados = sum(
            1 for e in eventos
            if (e.get("estado") or e.get("status") or "").lower()
            in {"aprobado", "paid", "pagado", "recibido"}
        )
        reports = (dashboard_snapshot(limit=100) or {}).get("reports") or []
        riesgos = sum(1 for r in reports if (r.get("urgency") or "").lower() in {"alto", "critico"})
        registry = (registry_snapshot(limit=80) or {}).get("totals") or {}
        return {
            "ok": True,
            "clientes": {"activos": activos, "total": total},
            "pagos": {"pendientes": pendientes, "pagados": pagados, "eventos": len(eventos)},
            "riesgos_reports": riesgos,
            "registry_total": registry.get("total", 0),
            "origen": "read-only: do_people.json, payment events, do_ai_reports, registry",
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}


def snapshot_nexus():
    """Snapshot completo de todos los sistemas para el dashboard y el briefing."""
    return {
        "generado": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "web": conector_web(),
        "maestro": conector_maestro(),
        "entregas": conector_entregas(),
        "do": conector_do(),
        "erp": conector_erp(),
        "infra": conector_infra(),
    }


def guardar_estado():
    """Persiste el snapshot en data/nexus_estado.json (lo usa el briefing, IA y plantilla)."""
    snap = snapshot_nexus()
    path = os.path.join(DATA_DIR, "nexus_estado.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, indent=2, default=str)
    return snap, path
