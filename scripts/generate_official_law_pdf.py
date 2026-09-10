import urllib.request
import os

pdf_path = "/Users/felipe/proyectos/quantuschile.cl/do/static/ley21719_oficial.pdf"

url_bcn_pdf = "https://www.leychile.cl/Navegar?idNorma=1209272&idVersion=2026-12-01"

print(f"Descargando PDF oficial de la Ley 21.719...")
try:
    req = urllib.request.Request(
        "https://www.bcn.cl/leychile/navegar?idNorma=1209272&exportar=pdf",
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    with urllib.request.urlopen(req) as response, open(pdf_path, 'wb') as out_file:
        data = response.read()
        out_file.write(data)
    print(f"PDF OFICIAL DESCARGADO DE BCN CON ÉXITO: {len(data)} bytes")
except Exception as e:
    print(f"Error descargando directo de BCN: {e}")
