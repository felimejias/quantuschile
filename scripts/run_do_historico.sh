#!/bin/bash
# Mantenimiento semanal del historico del Diario Oficial:
# 1) Vuelca a la BD (do_historico.db) lo pendiente de las ediciones descargadas.
# 2) Borra los PDFs crudos con mas de 9 dias (la BD conserva texto e indice para siempre).
cd /Users/felipe/proyectos/quantuschile.cl/do
PY=/Library/Frameworks/Python.framework/Versions/3.14/bin/python3
LOG=/Users/felipe/proyectos/quantuschile.cl/do/logs/do_historico.log
echo "[$(date '+%Y-%m-%d %H:%M:%S')] === INICIO mantenimiento historico ===" >> "$LOG"
"$PY" -c "
import sys; sys.path.insert(0, '/Users/felipe/proyectos/quantuschile.cl/do')
import json, glob
from do_historico import guardar_publicaciones, purgar_raw, resumen
for idx in sorted(glob.glob('/Users/felipe/proyectos/quantuschile.cl/do/data/do_ediciones/*/articulos.json')):
    try:
        d = json.load(open(idx, encoding='utf-8'))
        if d.get('articulos'):
            n = guardar_publicaciones(d['articulos'])
            print(f'  {d[\"fecha\"]}: {n} nuevos en BD')
    except Exception as e:
        print('  error', idx, str(e)[:60])
borrados = purgar_raw()
print('  carpetas raw purgadas (>9 dias):', borrados)
print('  resumen BD:', resumen())
" >> "$LOG" 2>&1
echo "[$(date '+%Y-%m-%d %H:%M:%S')] === FIN mantenimiento historico ===" >> "$LOG"