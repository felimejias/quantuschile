import urllib.request
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

pdf_dest = "/Users/felipe/proyectos/quantuschile.cl/do/static/ley21719_oficial.pdf"

url_html = "https://www.leychile.cl/Navegar?idNorma=1209272"

req = urllib.request.Request(url_html, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'})
try:
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8', errors='ignore')
    
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
except Exception as e:
    with open("/Users/felipe/proyectos/quantuschile.cl/do/static/ley21719_oficial.txt", "r", encoding="utf-8") as f:
        text = f.read()

doc = SimpleDocTemplate(pdf_dest, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
styles = getSampleStyleSheet()
story = []

title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=13, leading=16, textColor='#0F172A', alignment=1)
sub_style = ParagraphStyle('Sub', parent=title_style, fontSize=9, leading=12, textColor='#0284C7', alignment=1)
body_style = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=11, textColor='#1E293B')

story.append(Paragraph("<b>LEY N° 21.719 — REGULA LA PROTECCIÓN Y EL TRATAMIENTO DE LOS DATOS PERSONALES</b>", title_style))
story.append(Spacer(1, 4))
story.append(Paragraph("TEXTO OFICIAL COMPLETO — DIARIO OFICIAL DE LA REPÚBLICA DE CHILE & BCN", sub_style))
story.append(Spacer(1, 14))

paragraphs = text.split('\n\n')
for p in paragraphs:
    clean = p.strip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    if len(clean) > 5 and not "JavaScript" in clean and not "cookies" in clean:
        story.append(Paragraph(clean.replace("\n", "<br/>"), body_style))
        story.append(Spacer(1, 4))

doc.build(story)
print(f"PDF COMPLETO GENERADO CON ÉXITO: {len(story)} párrafos, {os.path.getsize(pdf_dest)} bytes")
