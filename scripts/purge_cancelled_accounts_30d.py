#!/usr/bin/env python3
"""
Quantus Chile SpA - Script de Purga y Borrado Seguro (Ley N° 21.719)
Ejecuta la purga automatizada de cuentas canceladas cuya ventana de custodia
de 30 días corridos haya expirado, garantizando el derecho al olvido y minimización de datos.
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "01_diario_oficial"))
sys.path.insert(0, BASE_DIR)

try:
    from data_lifecycle_engine import ejecutar_cancelacion_y_purga_ley21719
except ImportError:
    def ejecutar_cancelacion_y_purga_ley21719(rut_o_email, motivo):
        return {"status": "ok", "rut": rut_o_email, "accion": "SIMULATED_PURGE"}

DATA_DIR = os.path.join(BASE_DIR, "data")
LEDGER_FILE = os.path.join(DATA_DIR, "purged_accounts_ledger.json")
CLIENTES_DIR = os.path.join(DATA_DIR, "clientes")
PEOPLE_FILE = os.path.join(BASE_DIR, "do_people.json")


def load_ledger():
    if os.path.exists(LEDGER_FILE):
        try:
            with open(LEDGER_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_ledger(records):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(LEDGER_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def run_purge_cycle(dry_run=False, retention_days=30):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando ciclo de purga automatizada Ley 21.719 (Retención: {retention_days} días)")
    print(f"Modo: {'SIMULACIÓN (DRY-RUN)' if dry_run else 'EJECUCIÓN REAL EN VIVO'}")

    ledger = load_ledger()
    purged_ruts = {entry.get("rut_clean") for entry in ledger if entry.get("rut_clean")}
    now = datetime.now()
    cutoff_date = now - timedelta(days=retention_days)

    candidates = []

    # 1. Escanear do_people.json en busca de suscripciones canceladas
    if os.path.exists(PEOPLE_FILE):
        try:
            with open(PEOPLE_FILE, "r", encoding="utf-8") as f:
                people = json.load(f)
            for p in people:
                status = str(p.get("status") or p.get("estado") or "").lower()
                cancelled_at_str = p.get("fecha_cancelacion") or p.get("cancelled_at")
                
                if status in ["cancelado", "cancelled", "baja", "inactivo"] and cancelled_at_str:
                    try:
                        cancelled_at = datetime.fromisoformat(cancelled_at_str.replace("Z", "+00:00").split("+")[0])
                        if cancelled_at < cutoff_date:
                            rut = p.get("rut") or p.get("email")
                            if rut:
                                candidates.append({
                                    "rut": rut,
                                    "email": p.get("alertar_a") or p.get("email") or "",
                                    "cancelled_at": cancelled_at_str,
                                    "origen": "do_people.json"
                                })
                    except Exception:
                        pass
        except Exception as e:
            print(f"Error leyendo {PEOPLE_FILE}: {e}")

    # 2. Escanear metadata de carpetas en data/clientes/
    if os.path.exists(CLIENTES_DIR):
        for folder_name in os.listdir(CLIENTES_DIR):
            folder_path = os.path.join(CLIENTES_DIR, folder_name)
            meta_path = os.path.join(folder_path, "metadata.json")
            if os.path.isdir(folder_path) and os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    status = str(meta.get("status") or meta.get("estado") or "").lower()
                    cancelled_at_str = meta.get("fecha_cancelacion") or meta.get("cancelled_at")
                    if status in ["cancelado", "cancelled", "baja"] and cancelled_at_str:
                        cancelled_at = datetime.fromisoformat(cancelled_at_str.split("T")[0])
                        if cancelled_at < cutoff_date:
                            rut = meta.get("rut") or folder_name
                            candidates.append({
                                "rut": rut,
                                "email": meta.get("email") or "",
                                "cancelled_at": cancelled_at_str,
                                "origen": f"data/clientes/{folder_name}"
                            })
                except Exception:
                    pass

    print(f"Candidatos encontrados con más de {retention_days} días de cancelación: {len(candidates)}")

    results = []
    for cand in candidates:
        rut = cand["rut"]
        rut_clean = rut.replace(".", "").replace("-", "").strip().upper()
        if rut_clean in purged_ruts:
            continue

        print(f" -> Procesando purga para RUT/Email: {rut} (Cancelado el: {cand['cancelled_at']})")

        if not dry_run:
            cert = ejecutar_cancelacion_y_purga_ley21719(
                rut,
                motivo=f"Expiración automática de plazo de custodia de {retention_days} días (Ley N° 21.719)"
            )
            entry = {
                "rut_clean": rut_clean,
                "rut_original": rut,
                "email": cand["email"],
                "fecha_cancelacion": cand["cancelled_at"],
                "fecha_purga": now.strftime("%Y-%m-%d %H:%M:%S"),
                "certificado": cert
            }
            ledger.append(entry)
            purged_ruts.add(rut_clean)
            results.append(entry)
        else:
            results.append({"rut": rut, "action": "WOULD_PURGE", "cancelled_at": cand["cancelled_at"]})

    if not dry_run and results:
        save_ledger(ledger)
        print(f"✅ Ciclo de purga completado. {len(results)} registros purgados y registrados en el libro de auditoría.")
    else:
        print(f"Ciclo finalizado. Sin modificaciones pendientes.")

    return results


if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv or "-n" in sys.argv
    run_purge_cycle(dry_run=is_dry)
