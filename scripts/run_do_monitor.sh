#!/bin/bash
# Ejecuta el monitor de Diario Oficial (deteccion de publicaciones + despacho de alertas).
cd /Users/felipe/proyectos/quantuschile.cl/do
PY=/Library/Frameworks/Python.framework/Versions/3.14/bin/python3
LOG=/Users/felipe/proyectos/quantuschile.cl/do/logs/do_monitor.log
echo "[$(date '+%Y-%m-%d %H:%M:%S')] === INICIO monitor DO ===" >> "$LOG"
"$PY" do_personas_monitor.py >> "$LOG" 2>&1
echo "[$(date '+%Y-%m-%d %H:%M:%S')] === FIN monitor DO (exit $?) ===" >> "$LOG"
