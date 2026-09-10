import sys
import os

# Generador de PDF nativo sin dependencias externas usando comandos de impresión macOS (cupsfilter / enscript / pstopdf)
txt_path = "/Users/felipe/proyectos/quantuschile.cl/do/static/ley21719_oficial.txt"
ps_path = "/tmp/ley21719_temp.ps"
pdf_dest = "/Users/felipe/proyectos/quantuschile.cl/do/static/ley21719_oficial.pdf"

os.system(f"enscript -p {ps_path} {txt_path} 2>/dev/null")
os.system(f"pstopdf {ps_path} -o {pdf_dest} 2>/dev/null")

if os.path.exists(pdf_dest) and os.path.getsize(pdf_dest) > 1000:
    print(f"PDF OFICIAL GENERADO EXITOSAMENTE CON ENSCRIPT/PSTOPDF: {os.path.getsize(pdf_dest)} bytes")
else:
    print("Fallo pstopdf")
