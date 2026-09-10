path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/maestro_compliance_audit.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Ajuste literal del Punto 17 según el Artículo 14° de la Ley N° 21.719
literal_c17_item = '{ id: "c17", prio: "alta", title: "17. Protección de Datos de Niños, Niñas y Adolescentes (Art. 14°)", desc: "Tratamiento sujeto al interés superior y autonomía progresiva. Consentimiento obligatorio del representante legal para menores de 14 años." },'

# Reemplazo en checklistData
start_item = content.find('{ id: "c17"')
end_item = content.find('{ id: "c18"')

if start_item != -1 and end_item != -1:
    content = content[:start_item] + literal_c17_item + '\n          ' + content[end_item:]

# Reemplazo en guiasTecnicas c17 con texto literal de la ley
literal_c17_guide = '''      c17: {
        title: "17. Datos de Niños, Niñas y Adolescentes (Art. 14° Ley 21.719)",
        req: "El Artículo 14° de la Ley N° 21.719 manda que todo tratamiento de datos de NNA debe atender a su interés superior y autonomía progresiva. Para menores de 14 años es OBLIGATORIO el consentimiento expreso del padre, madre o representante legal.",
        toolHtml: `<div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8;">
          <span style="font-size:12px; color:#38bdf8; font-weight:800;">🛠️ Herramienta Rápida:</span>
          <a href="/static/Plantilla_Autorizacion_Opcional_Fotos_Ninos_RedesSociales.txt" download style="background:#10b981; color:#0f172a; padding:6px 12px; border-radius:8px; font-weight:800; font-size:11px; text-decoration:none;">📥 Descargar Modelo de Consentimiento del Representante Legal (Art. 14°)</a>
        </div>`,
        work: `<strong>Lo que exige exactamente la Ley N° 21.719 (Art. 14°):</strong><br>
        1. <strong>Principio de Interés Superior:</strong> Los datos de un menor solo pueden usarse si es para su beneficio directo o fines educativos/salud autorizados.<br>
        2. <strong>Regla de los 14 Años:</strong> Todo dato o imagen de un menor de 14 años exige la firma formal del padre, madre o tutor legal.<br>
        3. <strong>Prohibición de Perfilamiento (Art. 15°):</strong> Queda prohibido usar los datos de NNA para publicidad o perfilamiento comercial.<br><br>
        <strong>Pasos para auditar en la institución:</strong><br>
        1. Verificar que exista en el archivo el documento de autorización firmado por el representante legal del menor de 14 años.<br>
        2. Confirmar que los datos de los alumnos no sean cedidos ni comercializados con terceros.`
      },'''

start_guide = content.find('c17: {')
end_guide = content.find('c18: {')

if start_guide != -1 and end_guide != -1:
    content = content[:start_guide] + literal_c17_guide + '\n' + content[end_guide:]

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("AJUSTE LITERAL DEL ARTÍCULO 14° EN EL PUNTO 17 APLICADO CON ÉXITO")
