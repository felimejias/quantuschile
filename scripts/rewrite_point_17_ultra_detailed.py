path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/maestro_compliance_audit.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Redacción ultra detallada en español simple para el Punto 17 basada en el Artículo 14°
detailed_c17_guide = '''      c17: {
        title: "17. Datos de Niños, Niñas y Adolescentes (Art. 14° Ley 21.719)",
        req: "El Artículo 14° exige que los datos de menores se traten siempre para su propio bien (Interés Superior). Si el niño tiene menos de 14 años, es OBLIGATORIO que los papás firmen la autorización por escrito.",
        toolHtml: `<div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8;">
          <span style="font-size:12px; color:#38bdf8; font-weight:800;">🛠️ Herramienta Rápida:</span>
          <a href="/static/Plantilla_Autorizacion_Opcional_Fotos_Ninos_RedesSociales.txt" download style="background:#10b981; color:#0f172a; padding:6px 12px; border-radius:8px; font-weight:800; font-size:11px; text-decoration:none;">📥 Descargar Permiso Firmado de Apoderados (Art. 14°)</a>
        </div>`,
        work: `<strong>Explicación ultra fácil y detallada en 4 puntos simples:</strong><br><br>

        1. <strong>¿Qué son los datos de un niño?</strong><br>
        Son su RUT, su nombre, su certificado de nacimiento, su ficha de salud, sus notas y sus fotos o videos.<br><br>

        2. <strong>Regla de los 14 años (Lo que manda la Ley):</strong><br>
        - <strong>Menores de 14 años:</strong> La ley prohíbe usar sus datos a menos que el papá, la mamá o el apoderado legal firme una hoja de autorización express.<br>
        - <strong>Adolescentes (14 a 17 años):</strong> Pueden opinar y dar permiso para ciertas cosas sencillas de su edad, pero si es algo delicado o sensible, igual se exige la firma de los papás.<br><br>

        3. <strong>Prohibición Total de Vender o Hacer Publicidad (Art. 15°):</strong><br>
        Queda estrictamente prohibido usar la información de los niños para enviarles anuncios comerciales, venderles productos o rastrear qué miran en internet.<br><br>

        4. <strong>Pasos para auditar en un Colegio, Jardín o Club Deportivo:</strong><br>
        - <strong>Paso 1:</strong> Revisa las fichas de matrícula o inscripción. Debe existir una hoja independiente donde el apoderado autorice por escrito el uso de los datos del alumno.<br>
        - <strong>Paso 2:</strong> Verifica que no se vendan ni compartan las listas de alumnos con empresas externas de fotos, paseos o uniformes.<br>
        - <strong>Paso 3:</strong> Si un papá manda un correo pidiendo borrar los datos de su hijo, la institución tiene 10 días hábiles para responder e informarle que ya se eliminaron.`
      },'''

start_c17 = content.find('c17: {')
end_c17 = content.find('c18: {')

if start_c17 != -1 and end_c17 != -1:
    content = content[:start_c17] + detailed_c17_guide + '\n' + content[end_c17:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("REACCIÓN DETALLADA EN ESPAÑOL SIMPLE DEL PUNTO 17 APLICADA EN MAESTRO")
else:
    print("No se encontró el bloque c17")
