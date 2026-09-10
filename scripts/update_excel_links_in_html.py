path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/maestro_compliance_audit.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar todas las extensiones .csv por .xlsx en los botones de descarga de Excel
content = content.replace('Plantilla_Oficial_RAT_Ley21719_Quantus.csv', 'Plantilla_Oficial_RAT_Ley21719_Quantus.xlsx')
content = content.replace('Plantilla_Matriz_PIA_Evaluacion_Riesgos_Ley21719.csv', 'Plantilla_Matriz_PIA_Evaluacion_Riesgos_Ley21719.xlsx')

# También actualizar los textos de los botones para decir de forma destacada ".XLSX"
content = content.replace('📥 Descargar Excel RAT', '📥 Descargar Excel RAT Oficial (.xlsx)')
content = content.replace('📥 Descargar Matriz PIA', '📥 Descargar Matriz PIA en Excel (.xlsx)')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("ENLACES ACTUALIZADOS A ARCHIVOS EXCEL NATIVOS (.XLSX) EN EL PANEL MAESTRO")
