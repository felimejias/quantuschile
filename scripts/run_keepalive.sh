#!/bin/bash
# Watchdog del portal local (app.py en 8095): si el puerto no responde, lo relanza.
cd /Users/felipe/proyectos/quantuschile.cl/do
LOG=/Users/felipe/proyectos/quantuschile.cl/do/logs/keepalive.log
if curl -sf -m 5 -o /dev/null http://127.0.0.1:8095/; then
  exit 0
fi
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Puerto 8095 sin respuesta. Relanzando app.py..." >> "$LOG"
pgrep -f "app.py" | xargs kill 2>/dev/null
sleep 2
nohup ./run_local.sh >> logs/local_recovered.log 2>&1 &
disown
sleep 12
if curl -sf -m 5 -o /dev/null http://127.0.0.1:8095/; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] App relanzada OK en 8095." >> "$LOG"
else
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] FALLO al relanzar (revisar logs/local_recovered.log)." >> "$LOG"
fi

# QUANTUS NEXUS (8096)
NLOG=/Users/felipe/proyectos/quantuschile.cl/do/logs/nexus_web.log
if ! curl -sf -m 5 -o /dev/null http://127.0.0.1:8096/login; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Puerto 8096 sin respuesta. Relanzando Nexus..." >> "$NLOG"
  pgrep -f "nexus_app.py" | xargs kill 2>/dev/null
  sleep 2
  nohup /Library/Frameworks/Python.framework/Versions/3.14/bin/python3 nexus/nexus_app.py >> $NLOG 2>&1 &
  disown
  sleep 8
  if curl -sf -m 5 -o /dev/null http://127.0.0.1:8096/login; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Nexus relanzado OK en 8096." >> "$NLOG"
  else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] FALLO al relanzar Nexus." >> "$NLOG"
  fi
fi