import os
import sys
import time
import datetime
import json
import sqlite3

# Import DO modules
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from do_ediciones import _url_sumario, descargar_pdf, _leer_texto_pdf_rapido, _parsear_sumario, _url_articulo, EDICIONES_DIR
from do_historico import guardar_publicaciones, purgar_raw

STATE_FILE = os.path.join(BASE_DIR, "data", "ingesta_historica_estado.json")
PAUSE_BETWEEN_EDITIONS_SEC = 300  # 5 minutos entre ediciones

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"proxima_edicion": 44514, "total_ediciones_procesadas": 0, "status": "active"}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def run_historical_ingestion_step():
    state = load_state()
    edicion = state.get("proxima_edicion", 44514)
    
    if edicion < 37000:  # Ediciones anteriores a 2001 (limite alcanzado)
        print(f"[Ingesta Historica] Limite de 25 años alcanzado en edicion {edicion}.")
        state["status"] = "completed"
        save_state(state)
        return False

    print(f"\n[Ingesta Historica] === Procesando Edicion Historica N° {edicion} ===", flush=True)
    
    # Try fetching sumario (search date candidates if needed, or scan direct sumario)
    # Estimate ISO date from edition number (44515 = 2026-08-03, 1 edition = ~1 working day)
    # Default attempt date estimation:
    base_edicion = 44515
    base_date = datetime.date(2026, 8, 3)
    diff = base_edicion - edicion
    # Approximate date
    approx_date = base_date - datetime.timedelta(days=int(diff * 1.25))
    fecha_iso = approx_date.isoformat()
    
    sumario_url = _url_sumario(fecha_iso, edicion)
    data = descargar_pdf(sumario_url)
    
    if not data:
        # Retry with dates +/- 5 days
        for offset in range(-5, 6):
            if offset == 0:
                continue
            alt_date = (approx_date + datetime.timedelta(days=offset)).isoformat()
            data = descargar_pdf(_url_sumario(alt_date, edicion))
            if data:
                fecha_iso = alt_date
                break

    if not data:
        print(f"[Ingesta Historica] No se encontro sumario para edicion {edicion}. Saltando...", flush=True)
        state["proxima_edicion"] = edicion - 1
        save_state(state)
        return True

    texto = _leer_texto_pdf_rapido(data)
    articulos = _parsear_sumario(texto, fecha_iso, edicion)
    
    # Download PDFs of articles and extract text
    articulos_con_texto = []
    print(f"[Ingesta Historica] Edicion {edicion} ({fecha_iso}): {len(articulos)} articulos en sumario.", flush=True)
    
    for art in articulos:
        art_url = _url_articulo(fecha_iso, edicion, art["carpeta"], art["cve"])
        art["url"] = art_url
        art_data = descargar_pdf(art_url)
        if art_data:
            txt_art = _leer_texto_pdf_rapido(art_data)
            art["texto"] = txt_art
            art["bytes"] = len(art_data)
            articulos_con_texto.append(art)
        time.sleep(0.15)  # Micro-pausa respetuosa de 150ms

    # Guardar en SQLite
    insertados = guardar_publicaciones(articulos_con_texto)
    print(f"[Ingesta Historica] Edicion {edicion}: {insertados} articulos guardados en DB. Borrando PDFs crudos...", flush=True)

    # Borrado inmediato de PDFs crudos descargados para esta edicion historica
    purgar_raw(retener_dias=9)

    # Actualizar estado
    state["proxima_edicion"] = edicion - 1
    state["total_ediciones_procesadas"] = state.get("total_ediciones_procesadas", 0) + 1
    state["ultima_fecha_procesada"] = fecha_iso
    state["ultima_ejecucion_utc"] = datetime.datetime.utcnow().isoformat()
    save_state(state)
    
    return True

def main_loop():
    print("[Ingesta Historica Worker] Iniciado en segundo plano...", flush=True)
    while True:
        try:
            cont = run_historical_ingestion_step()
            if not cont:
                break
        except Exception as exc:
            print(f"[Ingesta Historica Worker] Error en paso: {exc}. Reintentando en 60s...", flush=True)
            time.sleep(60)
            continue
        
        print(f"[Ingesta Historica Worker] Pausa de {PAUSE_BETWEEN_EDITIONS_SEC}s (5 min)...", flush=True)
        time.sleep(PAUSE_BETWEEN_EDITIONS_SEC)

if __name__ == "__main__":
    main_loop()
