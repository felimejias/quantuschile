import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

pdf_dest = "/Users/felipe/proyectos/quantuschile.cl/do/static/ley21719_oficial.pdf"
txt_src = "/Users/felipe/proyectos/quantuschile.cl/do/static/ley21719_oficial.txt"

with open(txt_src, "r", encoding="utf-8") as f:
    lines = f.readlines()

doc = SimpleDocTemplate(pdf_dest, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
styles = getSampleStyleSheet()
story = []

title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=13, leading=16, textColor='#0F172A', alignment=1)
sub_style = ParagraphStyle('Sub', parent=title_style, fontSize=9, leading=12, textColor='#0284C7', alignment=1)
body_style = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=11, textColor='#1E293B')

story.append(Paragraph("<b>LEY N° 21.719 — REGULA LA PROTECCIÓN Y EL TRATAMIENTO DE LOS DATOS PERSONALES</b>", title_style))
story.append(Spacer(1, 4))
story.append(Paragraph("DOCUMENTO OFICIAL COMPLETO — DIARIO OFICIAL DE LA REPÚBLICA DE CHILE & BCN (56 PÁGS)", sub_style))
story.append(Spacer(1, 14))

chunk = []
for line in lines:
    if line.strip() == "":
        if chunk:
            p_text = "<br/>".join(chunk).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Paragraph(p_text, body_style))
            story.append(Spacer(1, 4))
            chunk = []
    else:
        chunk.append(line.strip())

if chunk:
    p_text = "<br/>".join(chunk).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    story.append(Paragraph(p_text, body_style))

doc.build(story)
print(f"PDF ROBUSTO GENERADO EXITOSAMENTE: {os.path.getsize(pdf_dest)} bytes")
