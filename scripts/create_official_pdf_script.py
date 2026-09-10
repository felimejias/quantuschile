import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

pdf_dest = "/Users/felipe/proyectos/quantuschile.cl/do/static/ley21719_oficial.pdf"
txt_src = "/Users/felipe/proyectos/quantuschile.cl/do/static/ley21719_oficial.txt"

with open(txt_src, "r", encoding="utf-8") as f:
    text = f.read()

doc = SimpleDocTemplate(pdf_dest, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
styles = getSampleStyleSheet()
story = []

title_style = ParagraphStyle(
    'TitleStyle',
    parent=styles['Heading1'],
    fontName='Helvetica-Bold',
    fontSize=13,
    leading=16,
    textColor='#0F172A',
    alignment=1
)

sub_style = ParagraphStyle(
    'SubStyle',
    parent=title_style,
    fontSize=9,
    leading=12,
    textColor='#0284C7',
    alignment=1
)

body_style = ParagraphStyle(
    'BodyStyle',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=8,
    leading=11,
    textColor='#1E293B'
)

story.append(Paragraph("<b>LEY N° 21.719 — REGULA LA PROTECCIÓN Y EL TRATAMIENTO DE LOS DATOS PERSONALES</b>", title_style))
story.append(Spacer(1, 4))
story.append(Paragraph("DOCUMENTO OFICIAL COMPLETO — DIARIO OFICIAL DE CHILE & BIBLIOTECA DEL CONGRESO NACIONAL (BCN)", sub_style))
story.append(Spacer(1, 14))

for paragraph in text.split("\n\n"):
    if paragraph.strip():
        clean_p = paragraph.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>").strip()
        story.append(Paragraph(clean_p, body_style))
        story.append(Spacer(1, 5))

doc.build(story)
print(f"PDF OFICIAL GENERADO EXITOSAMENTE CON REPORTLAB: {os.path.getsize(pdf_dest)} bytes")
