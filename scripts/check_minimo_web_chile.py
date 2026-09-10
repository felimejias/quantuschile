import re

html_path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/vigilancia_do.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

checks = {
    "DOCTYPE html": "<!DOCTYPE html>" in html or "<!doctype html>" in html.lower(),
    "Lang es-CL": 'lang="es-CL"' in html or 'lang="es"' in html,
    "Charset UTF-8": 'charset="UTF-8"' in html or 'charset="utf-8"' in html.lower(),
    "Viewport Responsive": 'name="viewport"' in html,
    "Title Tag": "<title>" in html and "</title>" in html,
    "Meta Description": 'name="description"' in html,
    "H1 Semantic Tag": "<h1" in html and "</h1>" in html,
    "Terminos y Condiciones Link": "términos" in html.lower() or "terms" in html.lower(),
    "Politica Privacidad Link": "privacidad" in html.lower() or "privacy" in html.lower(),
    "Ley 21.719 ARCO Mention": "21.719" in html or "arco" in html.lower(),
    "Derecho ARCO Contacto": "@quantuschile.cl" in html,
    "Footer Corporativo": "<footer" in html and "</footer>" in html
}

print("=== VERIFICACIÓN DE REQUISITOS MÍNIMOS WEB CHILE & LEY 21.719 ===")
for req, ok in checks.items():
    print(f" {'✅' if ok else '❌'} {req}")
