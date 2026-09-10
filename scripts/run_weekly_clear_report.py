#!/usr/bin/env python3
"""
Runner del Reporte Semanal de Tranquilidad - Radar Diario Oficial
------------------------------------------------------------------
Ejecuta el evento weekly_clear_report para todos los clientes activos.

Uso:
    python3 scripts/run_weekly_clear_report.py            # envia (max 1/semana por cliente)
    python3 scripts/run_weekly_clear_report.py --dry-run  # solo revisa

Sugerencia de agenda (cron): lunes o viernes en horario laboral.
El dedup por periodo semanal impide envios duplicados.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from communications.weekly_clear import run_weekly_clear_report  # noqa: E402

if __name__ == "__main__":
    import json
    result = run_weekly_clear_report(dry_run="--dry-run" in sys.argv)
    print(json.dumps({k: v for k, v in result.items() if k != "items"}, ensure_ascii=False, indent=2, default=str))
