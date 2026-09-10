import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from scripts.ingesta_historica_background import run_historical_ingestion_step

if __name__ == "__main__":
    print("[Ingesta Historica Cron Step] Iniciando ejecucion de 1 edicion...", flush=True)
    try:
        run_historical_ingestion_step()
    except Exception as exc:
        print(f"[Ingesta Historica Cron Step] Error: {exc}", flush=True)
