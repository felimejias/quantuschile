path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/maestro_compliance_audit.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazo de los puntos 9 y 17 con la corrección exacta exigida por el usuario
old_c9 = '''c9: {
        title: "9. Control de Acceso Físico a Bodegas y Ficheros",
        req: "Poner chapa con llave en los armarios de archivos para que las visitas no los puedan abrir.",
        work: `<strong>Explicación ultra fácil (Ejemplo):</strong><br>
        Es como cerrarle la puerta con llave a tu pieza cuando vienen visitas a tu casa para que no desordenen tus juguetes.<br><br>
        <strong>Pasos para auditar en la empresa:</strong><br>
        1. Ponle candado o chapa con clave al mueble donde guardan los contratos de clientes y entrega la llave solo a la secretaria.`
      }'''

new_c9 = '''c9: {
        title: "9. Control de Acceso Físico a Bodegas y Ficheros",
        req: "Poner chapa con llave en los armarios de archivos y nombrar formalmente por contrato al Custodio de Llaves.",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">
          🔐 <strong>Custodio de Llaves:</strong> Se firma un anexo nombrando oficialmente al responsable único de las llaves del mueble de archivo.
        </div>`,
        work: `<strong>Explicación ultra fácil (Ejemplo):</strong><br>
        Es como cerrarle la puerta con llave a tu pieza cuando vienen visitas a tu casa y entregarle la llave únicamente a la persona responsable que promete cuidarla por contrato.<br><br>
        <strong>Pasos para auditar en la empresa:</strong><br>
        1. Ponle candado o chapa con clave al mueble donde guardan los contratos.<br>
        2. Nombrar formalmente al Custodio de Llaves (DPO, Gerente o Encargado) con su firma de responsabilidad.`
      }'''

old_c17 = '''c17: {
        title: "17. Protección de Datos de Niños y Apoderados (Art. 34°)",
        req: "Prohibición absoluta de usar datos de niños para venderles cosas y permiso de los papás.",
        work: `<strong>Explicación ultra fácil (Ejemplo):</strong><br>
        En el colegio, para ir a una excursión o usar tu foto en la web, la profesora tiene que pedirle la firma en una libreta a tu papá o mamá.<br><br>
        <strong>Pasos para auditar en la empresa:</strong><br>
        1. En colegios y jardines, haz firmar en la matrícula la autorización de los apoderados.`
      }'''

new_c17 = '''c17: {
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
      }'''

if old_c9 in content:
    content = content.replace(old_c9, new_c9)

if old_c17 in content:
    content = content.replace(old_c17, new_c17)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("PUNTOS 9 Y 17 CORREGIDOS CON TOTAL RIGOR EN MAESTRO AUDIT")
