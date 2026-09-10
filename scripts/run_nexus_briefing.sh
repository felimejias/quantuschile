#!/bin/bash
# Informe diario QUANTUS NEXUS (por defecto plantilla confiable).
# Para que el briefing lo redacte la IA (opencode run), ponga NEXUS_BRIEFING_IA=1
# cuando la cuota del modelo headless lo permita.
cd /Users/felipe/proyectos/quantuschile.cl/do
LOG=/Users/felipe/proyectos/quantuschile.cl/do/logs/nexus_briefing.log
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Inicio briefing diario." >> "$LOG"
NEXUS_BRIEFING_IA="${NEXUS_BRIEFING_IA:-0}" \
  /Library/Frameworks/Python.framework/Versions/3.14/bin/python3 nexus/briefing.py >> "$LOG" 2>&1