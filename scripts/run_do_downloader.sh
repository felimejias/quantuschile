#!/bin/bash
# Descarga diaria de la edicion del Diario Oficial (anti-bot resuelto).
# 1) Intenta la edicion de HOY (09:30).
# 2) Si hoy no esta publicada (retraso/feriado), reintenta en la corrida del monitor (cada 2h).
# 3) Completa corridas parciales (cache con fallidos) de forma idempotente.
cd /Users/felipe/proyectos/quantuschile.cl/do
PY=/Library/Frameworks/Python.framework/Versions/3.14/bin/python3
LOG=/Users/felipe/proyectos/quantuschile.cl/do/logs/do_downloader.log
echo "[$(date '+%Y-%m-%d %H:%M:%S')] === INICIO descarga diaria DO ===" >> "$LOG"
"$PY" do_ediciones.py >> "$LOG" 2>&1 || echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR corrida (WAF bloqueado o red)" >> "$LOG"
# Volcar a la base historica lo que se haya completado
"$PY" -c "
import sys; sys.path.insert(0, '/Users/felipe/proyectos/quantuschile.cl/do')
import json, glob
from do_historico import guardar_publicaciones
for idx in sorted(glob.glob('/Users/felipe/proyectos/quantuschile.cl/do/data/do_ediciones/*/articulos.json')):
    try:
        d = json.load(open(idx, encoding='utf-8'))
        if d.get('articulos'):
            n = guardar_publicaciones(d['articulos'])
            print(f'  {d[\"fecha\"]}: {n} nuevos en BD')
    except Exception as e:
        print('  no se pudo insertar', idx, str(e)[:60])
" >> "$LOG" 2>&1
echo "[$(date '+%Y-%m-%d %H:%M:%S')] === FIN descarga diaria DO ===" >> "$LOG"