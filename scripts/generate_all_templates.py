import os

base_static = "/Users/felipe/proyectos/quantuschile.cl/do/static"

# 1. Carta Nombramiento DPO (Punto 2)
dpo_doc = """CARTA DE NOMBRAMIENTO OFICIAL DELEGADO DE PROTECCIÓN DE DATOS (DPO)
Ley N° 21.719 — Chile

Por medio de la presente, la empresa [NOMBRE EMPRESA], RUT [RUT EMPRESA], designa oficialmente a Don/Doña [NOMBRE DPO], RUT [RUT DPO], en el cargo de DELEGADO DE PROTECCIÓN DE DATOS (DPO), con facultades para velar por el cumplimiento de la Ley N° 21.719, atender las solicitudes de los titulares de datos y representar a la empresa ante la Agencia de Protección de Datos Personales.

Canal de atención oficial: privacidad@[empresa].cl
Fecha de Nombramiento: [FECHA]

____________________________________
Firma Representante Legal
"""
with open(os.path.join(base_static, "Plantilla_Carta_Nombramiento_DPO_Ley21719.txt"), "w", encoding="utf-8") as f:
    f.write(dpo_doc)

# 2. Matriz PIA Evaluación de Impacto (Punto 3)
pia_csv = """N° Proyecto / Sistema,Tipo de Datos Tratados,Peligro / Riesgo Identificado,Nivel de Riesgo (Alto/Medio/Bajo),Medida de Seguridad y Mitigación,Estado
1,Software de Ventas Web,Nombres - RUT - Tarjetas de Crédito,Alto (Fuga de datos por clave débil),Exigir clave de 10 dígitos y cifrado SSL HTTPS,ACTIVADO
2,Fichas de Clientes en Bodega,Nombres - Contratos firmados en Papel,Medio (Acceso no autorizado de visitas),Instalar chapa con llave en bodega y mueble,ACTIVADO
"""
with open(os.path.join(base_static, "Plantilla_Matriz_PIA_Evaluacion_Riesgos_Ley21719.csv"), "w", encoding="utf-8") as f:
    f.write(pia_csv)

# 3. Acta de Trituración y Destrucción Física de Papeles (Punto 8)
acta_doc = """ACTA DIGITAL DE DESTRUCCIÓN Y TRITURACIÓN DE DOCUMENTACIÓN EN PAPEL
Cumplimiento Ley N° 21.719 & Código Tributario

Fecha de Ejecución: [FECHA]
Responsable de Destrucción: [NOMBRE RESPONSABLE]

Se certifica que se ha procedido a la destrucción física e irreversible mediante máquina trituradora de corte cruzado (Norma DIN 66399 P-4) de los siguientes archivadores/documentos en papel cuyo plazo legal de retención de 6 años ha expirado:

- Archivadores / Carpetas Destruidas: [DESCRIPCIÓN DE DOCUMENTOS]
- Cantidad de Carpetas / Hojas: [CANTIDAD]

____________________________________
Firma Responsable de Destrucción
"""
with open(os.path.join(base_static, "Plantilla_Acta_Destruccion_Fisica_Papel_Ley21719.txt"), "w", encoding="utf-8") as f:
    f.write(acta_doc)

# 4. Manual de Protocolo de Brechas de Ciberseguridad en 3 Horas (Punto 11)
brecha_doc = """PROTOCOLO DE RESPUESTA Y NOTIFICACIÓN DE INCIDENTES DE CIBERSEGURIDAD (3 HORAS)
Ley N° 21.663 & Ley N° 21.719

En caso de detectar un hackeo, virus, pérdida de computador o filtración de datos:

1. PASO 1 (Aislamiento Inmediato - Minuto 0 a 15): Desconectar el equipo afectado de la red Wi-Fi o cable de red.
2. PASO 2 (Notificación Interna - Minuto 15 a 30): Avisar inmediatamente al DPO y al Gerente General.
3. PASO 3 (Evaluación del Impacto - Minuto 30 a 60): Determinar si afectó RUTs, claves o datos sensibles de clientes.
4. PASO 4 (Aviso Obligatorio a la ANCI y Agencia - Máximo 3 Horas): Enviar el formulario de incidente a la Agencia Nacional de Ciberseguridad (ANCI) y a la Agencia de Protección de Datos Personales.
5. PASO 5 (Notificación a Clientes): Enviar alerta preventiva por WhatsApp/Email a los usuarios afectados con las recomendaciones de seguridad.
"""
with open(os.path.join(base_static, "Plantilla_Protocolo_Notificacion_Brechas_Ciberseguridad.txt"), "w", encoding="utf-8") as f:
    f.write(brecha_doc)

print("PLANTILLAS Y RECURSOS DESCARGABLES PARA TODOS LOS PUNTOS CREADOS CON ÉXITO")
