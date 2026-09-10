path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/maestro_compliance_audit.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Actualizar títulos de c9 y c17 en guiasTecnicas
c9_new = '''      c9: {
        title: "9. Control de Acceso Físico a Bodegas y Ficheros",
        req: "Poner chapa con llave en los armarios de archivos y nombrar formalmente por contrato al Custodio de Llaves.",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">
          🔐 <strong>Custodio de Llaves:</strong> Se nombra oficialmente al encargado de las llaves del mueble de archivo por contrato de responsabilidad.
        </div>`,
        work: `<strong>Explicación ultra fácil (Ejemplo):</strong><br>
        Es como cerrarle la puerta con llave a tu pieza cuando vienen visitas a tu casa y entregarle la llave únicamente a la persona responsable nombrada por contrato.<br><br>
        <strong>Pasos para auditar en la empresa:</strong><br>
        1. Ponle candado o chapa con clave al mueble donde guardan los contratos.<br>
        2. Nombrar formalmente al Custodio de Llaves (DPO, Gerente o Encargado autorizado) con su firma de responsabilidad.`
      },'''

c17_new = '''      c17: {
        title: "17. Protección de Datos de Niños, Fotos y Redes Sociales (Art. 32° y 34°)",
        req: "La foto de un niño es un Dato Biométrico y Sensible. Queda ESTRICTAMENTE PROHIBIDO obligar al apoderado a firmar permisos de fotos como condición para matricularlo.",
        toolHtml: `<div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8;">
          <span style="font-size:12px; color:#38bdf8; font-weight:800;">🛠️ Herramienta Rápida:</span>
          <a href="/static/Plantilla_Autorizacion_Opcional_Fotos_Ninos_RedesSociales.txt" download style="background:#10b981; color:#0f172a; padding:6px 12px; border-radius:8px; font-weight:800; font-size:11px; text-decoration:none;">📥 Descargar Formulario Opcional Fotos Niños</a>
        </div>`,
        work: `<strong>Explicación ultra fácil y de alto cuidado (Ejemplo):</strong><br>
        Subir la foto de un niño a Instagram o Facebook es muy delicado porque expone su cara al mundo entero. <strong>El colegio NUNCA puede obligar a un papá a autorizar fotos para poder matricular a su hijo</strong>. Debe ser una hoja completamente separada y opcional. Si el papá dice que NO, el colegio está obligado a matricularlo exactamente igual y proteger la cara del alumno.<br><br>
        <strong>Pasos para auditar en el colegio:</strong><br>
        1. Descarga el Formulario Opcional de Arriba.<br>
        2. Verifica que el colegio entregue la hoja de fotos de forma 100% independiente a la matrícula.<br>
        3. Si un apoderado revoca el permiso por correo, el colegio tiene 10 días hábiles para borrar las fotos del menor de sus redes sociales.`
      },'''

# Buscar c9: { hasta },
start_c9 = content.find('c9: {')
end_c9 = content.find('c10: {')
if start_c9 != -1 and end_c9 != -1:
    content = content[:start_c9] + c9_new + '\n' + content[end_c9:]

# Buscar c17: { hasta },
start_c17 = content.find('c17: {')
end_c17 = content.find('c18: {')
if start_c17 != -1 and end_c17 != -1:
    content = content[:start_c17] + c17_new + '\n' + content[end_c17:]

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("CORRECCIÓN DE PUNTOS 9 Y 17 APLICADA CON ÉXITO")
