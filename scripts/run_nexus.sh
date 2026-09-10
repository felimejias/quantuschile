#!/bin/bash
# QUANTUS NEXUS: dashboard unificado en 8096.
cd /Users/felipe/proyectos/quantuschile.cl/do
LOG=/Users/felipe/proyectos/quantuschile.cl/do/logs/nexus_web.log
if curl -sf -m 5 -o /dev/null http://127.0.0.1:8096/login; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Nexus ya activo." >> "$LOG"
  exit 0
fi
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Arrancando QUANTUS NEXUS en 8096..." >> "$LOG"
nohup /Library/Frameworks/Python.framework/Versions/3.14/bin/python3 nexus/nexus_app.py >> logs/nexus_web.log 2>&1 &
disown
sleep 8
if curl -sf -m 5 -o /dev/null http://127.0.0.1:8096/login; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Nexus OK en 8096." >> "$LOG"
else
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] FALLO al arrancar Nexus." >> "$LOG"
fi