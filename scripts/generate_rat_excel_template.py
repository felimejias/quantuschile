import os

# Generar un archivo CSV/Excel listo para descargar con la plantilla estándar oficial RAT Ley 21.719
rat_csv_content = """N° Registro,Nombre de la Lista / Base de Datos,Soporte (Digital o Papel),Categoría de Datos (Nombres / RUTs / Correos),Finalidad del Uso,Base Legal,Quiénes Tienen Acceso,Plazo de Retención / Borrado,Medidas de Seguridad
1,Base de Clientes Ventas,Digital (Excel PC),Nombres - RUT - Teléfono - Email,Cobranza y Envío de Facturas,Consentimiento Contractual,Gerente Comercial y Contador,6 Años (Obligación Tributaria SII),Clave de Usuario y PC Cifrado
2,Archivadores Fichas Contratos 2026,Físico (Papel en Bodega),Nombres - RUT - Firma en Papel,Respaldo Legal de Contratos de Arriendo,Cumplimiento Contractual,Solo Secretaria Principal,5 Años (Prescripción Civil),Mueble con Llave bajo Llave
3,Lista de Suscriptores Sitio Web,Digital (Sistema Web),Nombres - Correo Electrónico,Envío de Boletín Semanal y Ofertas,Consentimiento Libre en Formulario Web,Encargado de Marketing,Borrado Inmediato al Pedir Baja,Hash SHA-256 e IP Guardada
"""

output_path = "/Users/felipe/proyectos/quantuschile.cl/do/static/Plantilla_Oficial_RAT_Ley21719_Quantus.csv"
with open(output_path, "w", encoding="utf-8-sig") as f:
    f.write(rat_csv_content)

print(f"PLANTILLA EXCEL/CSV RAT CREADA EN: {output_path}")
