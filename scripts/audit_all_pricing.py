#!/usr/bin/env python3
import os
import re

templates_dir = "/Users/felipe/proyectos/quantuschile.cl/do/templates"
results = {}

for root, dirs, files in os.walk(templates_dir):
    for f in files:
        if f.endswith(".html") and not ".bak" in f and not "prev-" in f:
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8", errors="ignore") as fp:
                content = fp.read()
            
            has_price = bool(re.search(r"(\$\s*\d+[\d\.,]*|\bCLP\b|\bUF\b|\bplanes\b)", content, re.I))
            forms = re.findall(r"<form\b[^>]*action=[\"']([^\"'>]+)", content, re.I)
            
            # Search for buttons linking to whatsapp or checkout or mailto
            buttons = re.findall(r"href=[\"'](https://mpago\.la/[^\s\"']+|/payment[^\s\"']*|/contratar[^\s\"']*|mailto:[^\s\"']+|https://wa\.me/[^\s\"']+|/demo/[^\s\"']*)[\"']", content, re.I)
            
            if has_price or forms or buttons:
                results[f] = {
                    "forms": forms,
                    "has_price": has_price,
                    "buttons": buttons
                }

print("=== REPORTE DE PLANTILLAS CON COBRO, PRECIOS O FORMULARIOS DE CONTRATACIÓN ===")
for k, v in sorted(results.items()):
    print(f"\n[{k}]")
    print(f"  Precios mencionados: {v['has_price']}")
    print(f"  Formularios POST/GET: {v['forms']}")
    if v['buttons']:
        print(f"  Botones de acción/pago/contacto: {v['buttons'][:5]}")
