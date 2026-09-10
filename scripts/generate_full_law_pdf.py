import os
import urllib.request
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

pdf_dest = "/Users/felipe/proyectos/quantuschile.cl/do/static/ley21719_oficial.pdf"

# Obtener texto oficial completo de la BCN mediante su API pública
url_txt = "https://www.bcn.cl/leychile/obtenerfoto?idMateria=0&idNorma=1209272&f=txt"

req = urllib.request.Request(url_txt, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as response:
        text_bcn = response.read().decode('utf-8', errors='ignore')
except Exception as e:
    with open("/Users/felipe/proyectos/quantuschile.cl/do/static/ley21719_oficial.txt", "r", encoding="utf-8") as f:
        text_bcn = f.read()

doc = SimpleDocTemplate(pdf_dest, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
styles = getSampleStyleSheet()
story = []

title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=13, leading=16, textColor='#0F172A', alignment=1)
sub_style = ParagraphStyle('Sub', parent=title_style, fontSize=9, leading=12, textColor='#0284C7', alignment=1)
body_style = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=11, textColor='#1E293B')

story.append(Paragraph("<b>LEY N° 21.719 — REGULA LA PROTECCIÓN Y EL TRATAMIENTO DE LOS DATOS PERSONALES</b>", title_style))
story.append(Spacer(1, 4))
story.append(Paragraph("DOCUMENTO OFICIAL COMPLETO — DIARIO OFICIAL DE LA REPÚBLICA DE CHILE (BCN)", sub_style))
story.append(Spacer(1, 14))

lines = text_bcn.split('\n')
chunk = []
for line in lines:
    if line.strip() == "":
        if chunk:
            p_text = "<br/>".join(chunk).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Paragraph(p_text, body_style))
            story.append(Spacer(1, 4))
            chunk = []
    else:
        chunk.append(line)

if chunk:
    p_text = "<br/>".join(chunk).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    story.append(Paragraph(p_text, body_style))

doc.build(story)
print(f"PDF COMPLETO OFICIAL DE LA LEY N° 21.719 GENERADO CON ÉXITO: {os.path.getsize(pdf_dest)} bytes")
