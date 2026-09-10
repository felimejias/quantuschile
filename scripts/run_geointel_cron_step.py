#!/usr/bin/env python3
"""
Script de ejecución periódica automatizada para GeoIntel Sales Radar B2B.
- Extrae de forma continua publicaciones del Diario Oficial e Ingesta de Patentes.
- Filtra y detecta constituciones de nuevas empresas en Rancagua, Machalí y comunas clave.
- Despacha alertas críticas por correo electrónico y WhatsApp a los operadores.
"""
import os
import sys
from datetime import datetime

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

from geointel_sales_radar import (
    run_do_extraction,
    run_patentes_municipales_extraction,
    dispatch_geointel_alerts,
    run_contact_enrichment_batch,
)

def main():
    now_str = datetime.now().isoformat()
    print(f"[{now_str}] === INICIANDO PASO DE INGESTA PERIODICA GEOINTEL ===")
    
    # 1. Extraction from Diario Oficial
    try:
        do_res = run_do_extraction(limit=500)
        print(f"Diario Oficial: found={do_res.get('found')}, saved={do_res.get('saved')}, blocked={do_res.get('blocked')}")
    except Exception as exc:
        print(f"Error en extracción Diario Oficial: {exc}")
        
    # 2. Extraction from Patentes Municipales
    try:
        pat_res = run_patentes_municipales_extraction(max_resources=2, max_rows_per_resource=800)
        print(f"Patentes Municipales: found={pat_res.get('found')}, saved={pat_res.get('saved')}")
    except Exception as exc:
        print(f"Error en extracción Patentes Municipales: {exc}")

    # 3. Enrich leads with real company contacts (domain probing)
    try:
        enrich_res = run_contact_enrichment_batch(batch_size=35)
        print(f"Enriquecimiento de contactos: attempted={enrich_res.get('attempted')}, enriched={enrich_res.get('enriched')}")
    except Exception as exc:
        print(f"Error en enriquecimiento de contactos: {exc}")

    # 4. Dispatch Alerts for O'Higgins Region (now has enriched contact info!)
    try:
        alerts_sent = dispatch_geointel_alerts()
        print(f"Alertas despachadas para 6ta Región: {alerts_sent}")
    except Exception as exc:
        print(f"Error al despachar alertas: {exc}")

    # 5. Purge Expired Real Estate Auctions & Replenish Catalog
    try:
        from app import load_and_purge_remates
        active_remates = load_and_purge_remates()
        print(f"Purga de Remates Inmobiliarios: {len(active_remates)} remates vigentes activos.")
    except Exception as exc:
        print(f"Error en purga de remates: {exc}")


    print(f"[{datetime.now().isoformat()}] === FINALIZADO PASO DE INGESTA GEOINTEL & REMATES ===")

if __name__ == "__main__":
    main()
