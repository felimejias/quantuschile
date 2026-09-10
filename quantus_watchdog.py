#!/usr/bin/env python3
"""
Quantus Watchdog 🐕
Servicio de Vigilancia de Marca y Detección de Conflictos INAPI.
Se ejecuta periódicamente (e.g. vía cron) para buscar coincidencias.
"""

import os
import json
import logging
import difflib
from datetime import datetime

# Importamos el scraper de INAPI desde app.py
from app import query_inapi

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] WATCHDOG: %(message)s'
)
log = logging.getLogger('QuantusWatchdog')

CLIENTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'watchdog_clients.json')
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'watchdog_history.json')

def similar_ratio(a, b):
    """Calcula la similitud de Levenshtein (ratio) entre dos strings."""
    return difflib.SequenceMatcher(None, a.upper(), b.upper()).ratio()

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)

def run_watchdog():
    log.info("🐕 Iniciando patrullaje de Quantus Watchdog...")
    
    if not os.path.exists(CLIENTS_FILE):
        log.error(f"No se encontró archivo de clientes: {CLIENTS_FILE}")
        return

    with open(CLIENTS_FILE, "r", encoding="utf-8") as f:
        clients = json.load(f)
        
    history = load_history()
        
    for client in clients:
        marca = client['marca_protegida']
        titular = client['nombre_titular']
        email = client['email_cliente']
        
        log.info(f"🔎 Analizando amenazas para la marca protegida: '{marca}' (Titular: {titular})")
        
        # Consultamos a INAPI por la marca. INAPI retorna variaciones por defecto (búsqueda parcial).
        results = query_inapi(marca)
        
        if "error" in results:
            log.error(f"Error consultando '{marca}': {results['error']}")
            continue
            
        marcas_encontradas = results.get("marcas", [])
        amenazas = []
        
        for hallazgo in marcas_encontradas:
            denominacion = hallazgo['denominacion']
            estado = hallazgo['estado'].lower()
            titular_hallazgo = hallazgo['titular'].upper()
            
            # Filtro 1: Descartar si el titular es exactamente nuestro cliente
            if difflib.SequenceMatcher(None, titular.upper(), titular_hallazgo).ratio() > 0.85:
                continue
                
            # Filtro 2: Calcular similitud fonética/textual con la marca protegida
            similitud = similar_ratio(marca, denominacion)
            
            # ID único de la amenaza
            threat_id = f"{denominacion.upper()}_{titular_hallazgo}"
            
            # Umbral de peligro: Si es más del 70% similar y está en estado activo
            if similitud >= 0.70 and estado in ["en trámite", "publicada", "solicitada"]:
                if threat_id not in history:
                    amenazas.append({
                        "denominacion_conflicto": denominacion,
                        "titular_rival": titular_hallazgo,
                        "similitud": f"{similitud*100:.1f}%",
                        "estado": estado,
                        "clase": hallazgo['clase']
                    })
                    history.append(threat_id)
                
        if amenazas:
            log.warning(f"🚨 ¡PELIGRO DETECTADO PARA '{marca}'! Se encontraron {len(amenazas)} nuevas amenazas.")
            
            cuerpo = f"<h2>⚠️ Alerta de Marca: {marca}</h2>"
            cuerpo += f"<p>Se han detectado {len(amenazas)} intentos de registro similares a tu marca protegida <strong>{marca}</strong>.</p>"
            cuerpo += "<ul>"
            
            for a in amenazas:
                log.warning(f"   -> [SIMILITUD {a['similitud']}] Marca: '{a['denominacion_conflicto']}' | Titular: {a['titular_rival']} | Estado: {a['estado']} | Clase: {a['clase']}")
                cuerpo += f"<li><strong>{a['denominacion_conflicto']}</strong> ({a['similitud']} similar) - Titular: {a['titular_rival']} - Estado: {a['estado']} - Clase: {a['clase']}</li>"
            
            cuerpo += "</ul>"
            cuerpo += "<p>Te recomendamos presentar una oposición de marca lo antes posible para evitar que estos registros se concedan.</p>"
            
            # Enviar correo real
            from mailer import send_email
            send_email(email, f"🚨 ALERTA ROJA: Posible copia de tu marca {marca}", cuerpo)
            log.info(f"📧 ALERTA ENVIADA: Correo real enviado a {email} ofreciendo Interposición de Oposición.")
        else:
            log.info(f"✅ La marca '{marca}' está segura. No se detectaron conflictos nuevos.")

    save_history(history)
    log.info("🐕 Patrullaje finalizado con éxito.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    run_watchdog()
