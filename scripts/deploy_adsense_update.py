#!/usr/bin/env python3
"""
Deploy script for AdSense compliance update (app.py + templates)
"""
import os
import subprocess

print("=== INICIANDO EMPAQUETADO Y DESPLIEGUE DE ACTUALIZACIÓN ADSENSE ===")

BASE_DIR = "/Users/felipe/proyectos/quantuschile.cl/do"
TARBALL = "/tmp/quantus_adsense_update.tar.gz"

# 1. Create tarball with app.py and templates
cmd_tar = f"cd {BASE_DIR} && tar -czf {TARBALL} app.py templates/"
print(f"Generando paquete: {TARBALL}...")
subprocess.run(cmd_tar, shell=True, check=True)
print("Paquete generado con éxito.")

# 2. Instructions for production deployment
print("\nPara sincronizar con producción:")
print("1. Enviar el paquete al host:")
print(f"   scp {TARBALL} root@100.117.44.3:/tmp/")
print("2. Descomprimir en el servidor (/mnt/proyectos/felipe/inapi_portal/ o contenedor LXC):")
print(f"   tar -xzf {TARBALL} -C /mnt/proyectos/felipe/inapi_portal/")
print("3. Reiniciar el servicio gunicorn.")
print("\n=== SCRIPT LISTO ===")
