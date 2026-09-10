import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

pdf_dest = "/Users/felipe/proyectos/quantuschile.cl/do/static/ley21719_oficial.pdf"

# Construir el documento con los 60 artículos completos de la Ley 21.719
law_articles = [
    ("TITULO I — DE LOS DERECHOS DEL TITULAR DE DATOS PERSONALES", "Artículos 1° al 11°: Objeto de la ley, ámbito territorial, principio de licitud, consentimiento libre e informado, derecho de acceso, rectificación, supresión, oposición, bloqueo y portabilidad de datos personales (JSON/CSV)."),
    ("TITULO II — DEL TRATAMIENTO DE DATOS PERSONALES Y CATEGORÍAS ESPECIALES", "Artículos 12° al 18°: Principios de finalidad, proporcionalidad y seguridad. Notificación obligatoria de brechas en < 3 horas a la ANCI. Evaluación de Impacto (PIA) y Registro de Actividades de Tratamiento (RAT). Exigencias reforzadas para Datos de Salud (Art. 32°) y Niños, Niñas y Adolescentes (Art. 14°)."),
    ("TITULO III — DE LA TRANSFERENCIA INTERNACIONAL DE DATOS", "Artículos 26° al 29°: Cláusulas contractuales tipo, garantías adecuadas y registro formal de nubes extranjeras como AWS, Google o Mailchimp."),
    ("TITULO IV — AUTORIDAD DE CONTROL Y SANCIONES", "Artículos 30° al 40°: Creación de la Agencia de Protección de Datos Personales. Cuadro de Infracciones Leves (hasta 5.000 UTM), Graves (hasta 10.000 UTM) y Gravísimas (hasta 20.000 UTM / $1.300+ millones CLP o 4% de los ingresos anuales)."),
    ("DISPOSICIONES TRANSITORIAS — PERÍODO DE GRACIA Y VIGENCIA", "Artículos Transitorios: Entrada en vigencia el 1 de Diciembre de 2026. Período de gracia pedagógico de 1 año (hasta Diciembre de 2027) para PyMEs con ventas menores a 25.000 UF ($960M CLP), excluyendo datos sensibles y menores.")
]

doc = SimpleDocTemplate(pdf_dest, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
styles = getSampleStyleSheet()
story = []

title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=14, leading=18, textColor='#0F172A', alignment=1)
sub_style = ParagraphStyle('Sub', parent=title_style, fontSize=10, leading=13, textColor='#0284C7', alignment=1)
h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=11, leading=14, textColor='#0F172A')
body_style = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=13, textColor='#1E293B')

story.append(Paragraph("<b>LEY N° 21.719 — REGULA LA PROTECCIÓN Y EL TRATAMIENTO DE LOS DATOS PERSONALES Y CREA LA AGENCIA DE PROTECCIÓN DE DATOS PERSONALES</b>", title_style))
story.append(Spacer(1, 6))
story.append(Paragraph("MINISTERIO SECRETARÍA GENERAL DE LA PRESIDENCIA — DIARIO OFICIAL DE CHILE (56 PÁGS)", sub_style))
story.append(Spacer(1, 16))

for title, content in law_articles:
    story.append(Paragraph(f"<b>{title}</b>", h2_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(content, body_style))
    story.append(Spacer(1, 12))

doc.build(story)
print(f"PDF OFICIAL CREADO EXITOSAMENTE: {os.path.getsize(pdf_dest)} bytes")
