import os

base_static = "/Users/felipe/proyectos/quantuschile.cl/do/static"

# 1. Anexo de Contrato de Trabajo de Protección de Datos (Punto 23)
hr_doc = """ANEXO DE CONTRATO DE TRABAJO: PROTECCIÓN DE DATOS PERSONALES DEL TRABAJADOR
Cumplimiento Ley N° 21.719 — Chile

En [Ciudad], a [Fecha], entre la empresa [NOMBRE EMPRESA], RUT [RUT EMPRESA], y el trabajador Don/Doña [NOMBRE TRABAJADOR], RUT [RUT TRABAJADOR], se acuerda el siguiente anexo:

PRIMERO: La empresa informa al trabajador que sus datos personales (liquidaciones de sueldo, licencias médicas, cargas familiares y datos bancarios) serán tratados exclusivamente para el cumplimiento de las obligaciones laborales, previsionales y tributarias.
SEGUNDO: El trabajador tendrá derecho a ejercer sus derechos de acceso, rectificación y supresión ante el DPO en privacidad@[empresa].cl.

____________________________________        ____________________________________
Firma Empleador                             Firma Trabajador
"""
with open(os.path.join(base_static, "Plantilla_Anexo_Contrato_Trabajo_Proteccion_Datos_Ley21719.txt"), "w", encoding="utf-8") as f:
    f.write(hr_doc)

# 2. Cartel Informativo Oficial de Videovigilancia (Punto 24)
cam_doc = """CARTEL MANDATORIO DE VIDEOVIGILANCIA Y CAMARAS DE SEGURIDAD
Cumplimiento Ley N° 21.719 (Datos Biométricos) & Dirección del Trabajo

ZONA VIDEOVIGILADA 🎥
Por motivos de seguridad, las imágenes de este recinto son grabadas y monitoreadas.

- Responsable del Tratamiento: [NOMBRE EMPRESA / RUT]
- Finalidad: Seguridad de personas e instalaciones.
- Ejercicio de Derechos: privacidad@[empresa].cl

Queda prohibido el uso de estas imágenes para fines distintos a la seguridad.
"""
with open(os.path.join(base_static, "Plantilla_Cartel_Oficial_Videovigilancia_Camaras.txt"), "w", encoding="utf-8") as f:
    f.write(cam_doc)

print("PLANTILLAS DE RRHH Y VIDEOVIGILANCIA CREADAS CON ÉXITO")
