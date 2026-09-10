#!/usr/bin/env python3
"""
QUANTUS HEALTH & UPTIME SENTINEL
Monitorea continuamente la disponibilidad de los servicios de Quantus en producción:
- Portal Web (https://quantuschile.cl)
- Quantus App ERP (https://quantuschile.cl/app)
- API Backend & Base de Datos
- Proxy Nginx y Contenedores
"""

import sys
import time
import urllib.request
import json

ENDPOINTS = [
    {"name": "Portal Web Principal", "url": "https://quantuschile.cl"},
    {"name": "Quantus App (ERP Admin)", "url": "https://quantuschile.cl/app"},
    {"name": "API Health Check", "url": "https://quantuschile.cl/api/bootstrap"},
    {"name": "Manifiesto PWA", "url": "https://quantuschile.cl/manifest.json"},
]

def check_health():
    print("=" * 60)
    print("🛡️ QUANTUS HEALTH SENTINEL — AUDITORÍA DE SERVICIOS EN VIVO")
    print("=" * 60)
    
    all_healthy = True
    for ep in ENDPOINTS:
        start = time.time()
        try:
            req = urllib.request.Request(
                ep["url"],
                headers={"User-Agent": "QuantusHealthSentinel/1.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                elapsed_ms = int((time.time() - start) * 1000)
                status = resp.getcode()
                if status == 200:
                    print(f"✅ {ep['name']:<25} -> HTTP 200 OK  ({elapsed_ms} ms)")
                else:
                    print(f"⚠️ {ep['name']:<25} -> HTTP {status} ({elapsed_ms} ms)")
                    all_healthy = False
        except Exception as e:
            elapsed_ms = int((time.time() - start) * 1000)
            print(f"❌ {ep['name']:<25} -> ERROR: {str(e)} ({elapsed_ms} ms)")
            all_healthy = False

    print("=" * 60)
    if all_healthy:
        print("🎉 TODOS LOS SERVICIOS DE PRODUCCIÓN OPERAN EN ESTADO ÓPTIMO.")
    else:
        print("🚨 SE DETECTARON INCIDENCIAS EN LA INFRAESTRUCTURA.")
    print("=" * 60)
    return all_healthy

if __name__ == "__main__":
    is_ok = check_health()
    sys.exit(0 if is_ok else 1)
