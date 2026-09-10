import os

base_static = "/Users/felipe/proyectos/quantuschile.cl/do/static"

photo_doc = """FORMULARIO SEPARADO Y OPCIONAL DE AUTORIZACIÓN DE USO DE IMAGEN Y REDES SOCIALES
Ley N° 21.719 (Artículos 32° y 34° - Datos Biométricos de Menores de Edad)

Establecimiento Educacional / Institución: [NOMBRE COLEGIO / JARDÍN]
Nombre del Alumno / Menor: [NOMBRE ALUMNO]
Nombre del Padre / Madre / Apoderado: [NOMBRE APODERADO], RUT [RUT APODERADO]

IMPORTANTE: El presente formulario es TOTALMENTE VOLUNTARIO E INDEPENDIENTE del proceso de matrícula escolar. Su rechazo NO afectará en modo alguno la matrícula ni la entrega de servicios educativos al alumno.

Marque con una X su decisión:

[  ] SÍ AUTORIZO el uso de la imagen/fotografía de mi hijo(a) exclusivamente para actividades institucionales del colegio.
[  ] NO AUTORIZO el uso ni publicación de la imagen/fotografía de mi hijo(a) en redes sociales, página web ni folletos comerciales.

NOTA DE REVOCACIÓN: El apoderado podrá revocar la presente autorización en cualquier momento mediante correo enviado a privacidad@[colegio].cl, obligándose el colegio a eliminar las imágenes en un plazo máximo de 10 días hábiles.

____________________________________
Firma del Apoderado
"""

with open(os.path.join(base_static, "Plantilla_Autorizacion_Opcional_Fotos_Ninos_RedesSociales.txt"), "w", encoding="utf-8") as f:
    f.write(photo_doc)

print("PLANTILLA SEPARADA Y OPCIONAL DE FOTOS DE NIÑOS CREADA EN STATIC")
