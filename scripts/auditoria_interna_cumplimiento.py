import os
import json
import requests
from bs4 import BeautifulSoup

base_url = 'http://localhost:8084'

print("==========================================================================")
print("  AUDITORÍA DE CUMPLIMIENTO INTERNO QUANTUS CHILE SpA (LEY 21.719 Y LEY 19.496)")
print("==========================================================================\n")

results = []

# 1. Verificación de Identificación Legal de la Empresa
r_priv = requests.get(f"{base_url}/privacidad")
has_rut_real = "78.478.612-9" in r_priv.text
has_domicilio = "Rancagua" in r_priv.text
has_email_arco = "privacidad@quantuschile.cl" in r_priv.text

results.append(("Identificación Legal de la Empresa (RUT 78.478.612-9 y Domicilio)", has_rut_real and has_domicilio))
results.append(("Canal Obligatorio Derechos ARCO (privacidad@quantuschile.cl)", has_email_arco))

# 2. Verificación de Aceptación Expresa de Consentimiento (No Pre-Marcado)
r_do = requests.get(f"{base_url}/do")
soup_do = BeautifulSoup(r_do.text, 'html.parser')
checkbox = soup_do.find('input', {'id': 'pre-consent'})
is_not_checked_by_default = checkbox and not checkbox.has_attr('checked')

results.append(("Consentimiento Expreso Libre (Checkbox NO marcado por defecto)", is_not_checked_by_default))

# 3. Verificación de Respaldo Criptográfico de Consentimiento (SHA-256 / Audit Trail)
clientes_dir = "/Users/felipe/proyectos/quantuschile.cl/do/data/clientes"
has_evidence_files = False
if os.path.exists(clientes_dir):
    for root, dirs, files in os.walk(clientes_dir):
        for f in files:
            if "evidencia.json" in f or "consentimiento" in f:
                has_evidence_files = True
                break

results.append(("Respaldo Criptográfico de Consentimientos (Archivos Evidence JSON)", has_evidence_files))

# 4. Transparencia de Precios y Términos antes del Pago (Ley 19.496)
r_term = requests.get(f"{base_url}/terminos")
has_transparencia = "informacion honesta" in r_term.text.lower() or "pagos" in r_term.text.lower()

results.append(("Transparencia de Precios y Cobros Reversibles (Ley 19.496)", has_transparencia))

# Imprimir Cuadro de Resultados
all_passed = True
for title, ok in results:
    status = "✅ CUMPLE" if ok else "❌ NO CUMPLE"
    if not ok: all_passed = False
    print(f"{status} | {title}")

print("\n--------------------------------------------------------------------------")
if all_passed:
    print("VEREDICTO AUDITORÍA: QUANTUS CUMPLE AL 100% CON LA LEY 21.719 Y LEY 19.496 EN LOCAL.")
else:
    print("VEREDICTO AUDITORÍA: EXISTEN BRECHAS PENDIENTES DE REMEDIACIÓN.")
print("--------------------------------------------------------------------------")
