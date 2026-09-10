import os, sys

BASE_DIR = "/opt/quantus/portal"
sys.path.insert(0, BASE_DIR)

from do_ediciones import _url_sumario, descargar_pdf, _leer_texto_pdf_rapido, _parsear_sumario, _url_articulo
from do_historico import guardar_publicaciones

print("Testing sumario download and parsing for Edicion 44515 (2026-08-03)...")
url = _url_sumario("2026-08-03", 44515)
print("Sumario URL:", url)
data = descargar_pdf(url)
print("Sumario PDF bytes downloaded:", len(data) if data else 0)

if data:
    txt = _leer_texto_pdf_rapido(data)
    print("Sumario PDF text length:", len(txt))
    articulos = _parsear_sumario(txt, "2026-08-03", 44515)
    print("Articulos parsed from sumario:", len(articulos))
    if articulos:
        print("First 3 articulos parsed:", articulos[:3])
        # Download first article
        art0 = articulos[0]
        art0_url = _url_articulo("2026-08-03", 44515, art0["carpeta"], art0["cve"])
        print("First article URL:", art0_url)
        art0_data = descargar_pdf(art0_url)
        print("First article PDF bytes:", len(art0_data) if art0_data else 0)
        if art0_data:
            txt0 = _leer_texto_pdf_rapido(art0_data)
            art0["texto"] = txt0
            art0["bytes"] = len(art0_data)
            art0["url"] = art0_url
            ins = guardar_publicaciones([art0])
            print("Articles inserted into DB:", ins)
