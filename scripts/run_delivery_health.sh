#!/bin/bash
# 1) Reintenta envios fallidos/pendientes (correo + WhatsApp).
# 2) Revisa la salud de entregas y alerta por correo interno si hay fallos.
cd /Users/felipe/proyectos/quantuschile.cl/do
PY=/Library/Frameworks/Python.framework/Versions/3.14/bin/python3
LOG=/Users/felipe/proyectos/quantuschile.cl/do/logs/delivery_health.log
"$PY" -c "from communications.retry_worker import run_retries; run_retries()" >> "$LOG" 2>&1
"$PY" -c "from communications.delivery_health import alert_if_issues; alert_if_issues()" >> "$LOG" 2>&1
