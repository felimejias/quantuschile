path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/maestro_compliance_audit.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Diccionario con guías ultra detalladas paso a paso en español simple (A prueba de principiantes)
new_guides = '''    const guiasTecnicas = {
      c1: {
        title: "1. Registro de Actividades de Tratamiento (RAT)",
        req: "La Ley 21.719 exige que la empresa tenga un inventario formal declarando cada lista o sistema donde guarda RUTs, correos, nombres o teléfonos de personas.",
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1 (Entrevista Inicial):</strong> Junta a los encargados de Venta, Marketing y Contabilidad. Pregúntales: <em>'¿Dónde guardan la lista de clientes?'</em> (Excels en el PC, cuadernos de papel, Google Drive, programa de ventas o correos).</li>
          <li><strong>Paso 2 (Listar las fuentes):</strong> En una hoja o Excel anotan cada lista encontrada (Ejemplo: 'Excel de clientes', 'Fichas de clientes en archivador azul', 'Base de datos del sitio web').</li>
          <li><strong>Paso 3 (Llenar el Formulario RAT):</strong> Por cada lista, escribe:
            <ul style="margin-top:4px;">
              <li><strong>Para qué usan los datos:</strong> (Ej: 'Para cobrar', 'Para mandar ofertas').</li>
              <li><strong>Quién tiene acceso:</strong> (Ej: 'Solo la secretaria y el contador').</li>
              <li><strong>Plazo de borrado:</strong> (Ej: '6 años por boletas').</li>
            </ul>
          </li>
          <li><strong>Paso 4 (Cargar en Quantus):</strong> Entra al panel Quantus de la empresa y adjunta este inventario listo.</li>
        </ol>`
      },
      c2: {
        title: "2. Designación de Responsable de Datos / DPO",
        req: "La empresa debe nombrar por escrito a una persona física (con nombre y RUT) encargada de responder si un cliente reclama o si la fiscalía de datos investiga.",
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1 (Elegir al encargado):</strong> La empresa debe elegir a alguien interno (ej: el Gerente General, Administrador o Jefe de TI) o contratar el servicio de DPO Externo de Quantus.</li>
          <li><strong>Paso 2 (Firmar Carta de Nombramiento):</strong> Imprime la plantilla de Quantus que dice: <em>'Se nombra a Don/Doña [Nombre] como Delegado de Protección de Datos'</em>. El representante legal de la empresa firma el papel.</li>
          <li><strong>Paso 3 (Publicar Correo de Contacto):</strong> Crea una cuenta de correo oficial (Ej: <code>privacidad@empresa.cl</code> o <code>dpo@empresa.cl</code>) y colócala visible en el pie de página de su sitio web.</li>
        </ol>`
      },
      c3: {
        title: "3. Evaluación de Impacto en Protección de Datos (PIA)",
        req: "Un estudio preventivo de riesgos obligatorio antes de instalar un software nuevo, usar IA o manejar datos delicados.",
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1 (Revisar datos delicados):</strong> Pregunta si la empresa guarda datos de salud, fichas médicas, fotos de rut, cuentas bancarias o datos de niños.</li>
          <li><strong>Paso 2 (Identificar el riesgo):</strong> Pregúntale al informático: <em>'¿Qué pasa si nos hackean o se nos pierde este computador?'</em>. Anota el peligro.</li>
          <li><strong>Paso 3 (Aplicar la Solución):</strong> Si el peligro es que entren con clave simple, la solución es exigir clave de 10 dígitos y verificación por celular.</li>
          <li><strong>Paso 4 (Firmar el Informe PIA Quantus):</strong> El sistema Quantus emite el PDF de 2 páginas con el análisis firmado.</li>
        </ol>`
      },
      c4: {
        title: "4. Aceptación Expresa sin Pre-marcado",
        req: "En los formularios web de la empresa, las casillas que dicen 'Acepto los términos y condiciones' NUNCA pueden venir marcadas con el tick azul por defecto.",
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1 (Abrir la página web del cliente):</strong> Entra a su sitio web e intenta simular una compra o enviar un mensaje de contacto.</li>
          <li><strong>Paso 2 (Revisar los cuadritos de tick):</strong> Fíjate si la casilla de 'Acepto los términos' ya aparece con el tick puesto automáticamente.</li>
          <li><strong>Paso 3 (Instrucción al informático):</strong> Si viene marcada, dile al programador: <em>'Borra la palabra checked del código del formulario HTML'</em>. La casilla DEBE nacer vacía para que la persona le haga clic voluntariamente.</li>
        </ol>`
      },
      c5: {
        title: "5. Respaldo Criptográfico de Permisos (SHA-256)",
        req: "Si un cliente acusa a la empresa diciendo 'Ustedes usaron mi correo sin mi permiso', la empresa debe mostrar la prueba digital exacta del clic.",
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1 (Copiar el Código Quantus):</strong> Copia el script de registro de consentimiento desde el panel Quantus.</li>
          <li><strong>Paso 2 (Pegar en el backend web del cliente):</strong> El programador lo conecta al botón 'Enviar' o 'Pagar' de su formulario.</li>
          <li><strong>Paso 3 (Verificar la prueba):</strong> Cada vez que alguien hace clic, Quantus guarda automáticamente un archivo seguro que registra:
            <ul>
              <li>La dirección IP de internet del cliente.</li>
              <li>La hora y fecha exacta con segundos.</li>
              <li>El código seguro Hash SHA-256 de las palabras que el cliente aceptó.</li>
            </ul>
          </li>
        </ol>`
      },
      c6: {
        title: "6. Portal de Atención Derechos ARCO (SLA 13 días)",
        req: "La empresa debe darle un canal fácil a las personas para pedir que borren sus datos, los corrijan o muestren qué tienen guardado de ellos.",
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1 (Instalar el Widget ARCO):</strong> Copia la línea de código JavaScript de Quantus y pégala en el pie de página del sitio web del cliente.</li>
          <li><strong>Paso 2 (Verificar el Botón Flotante):</strong> Aparecerá un botón azul elegante que dice 'Protección de Datos & Derechos ARCO'.</li>
          <li><strong>Paso 3 (Probar el sistema):</strong> Envía una solicitud de prueba. Al entrar el mensaje, el panel Quantus iniciará la cuenta regresiva de 13 días hábiles y notificará al DPO por correo y WhatsApp.</li>
        </ol>`
      },
      c7: {
        title: "7. Inventario y Etiquetado QR de Archivadores Físicos",
        req: "La Ley 21.719 sanciona la pérdida de carpetas físicas en papel que contengan fichas de clientes, contratos o RUTs.",
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1 (Ir a la bodega u oficina de archivos):</strong> Abre los muebles y estantes donde guardan carpetas y archivadores de palanca en papel.</li>
          <li><strong>Paso 2 (Rotular los archivadores):</strong> Ordénalos por año y tipo (Ej: 'Contratos Clientes 2024').</li>
          <li><strong>Paso 3 (Generar las Etiquetas QR Quantus):</strong> En el panel de Quantus ingresas la carpeta y la plataforma imprime una etiqueta con Código QR.</li>
          <li><strong>Paso 4 (Pegar en el lomo):</strong> Pega la etiqueta autoadhesiva en el lomo del archivador físico. Al escanear el QR con un celular, mostrará qué papeles contiene y cuándo vence.</li>
        </ol>`
      },
      c8: {
        title: "8. Protocolo de Destrucción Física Registrada",
        req: "Queda estrictamente prohibido botar hojas con RUTs o datos de clientes a la papelera común o a la basura de la calle.",
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1 (Comprar o arrendar trituradora):</strong> La empresa debe usar una máquina trituradora de papel de corte cruzado (que deje el papel en confeti no legible, Nivel DIN P-4).</li>
          <li><strong>Paso 2 (Revisar la alerta de vencimiento Quantus):</strong> Cuando Quantus avisa que un archivador físico cumplió sus 6 años, la secretaria junta los papeles vencidos.</li>
          <li><strong>Paso 3 (Triturar y firmar el Acta):</strong> Trituran los papeles en la máquina y en el panel Quantus presionan el botón 'Firmar Acta Digital de Trituración'.</li>
        </ol>`
      },
      c9: {
        title: "9. Control de Acceso Físico a Bodegas y Ficheros",
        req: "Evitar que cualquier persona, visitas o aseadores no autorizados puedan abrir los muebles donde hay fichas o datos de clientes.",
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1 (Revisar las puertas y muebles):</strong> Inspecciona la sala de archivos o la oficina donde están las carpetas.</li>
          <li><strong>Paso 2 (Instalar llave o chapa con clave):</strong> Coloca una chapa con llave o cerradura con clave numérica en la puerta y mantenla cerrada.</li>
          <li><strong>Paso 3 (Llevar la libreta de llaves):</strong> Solo la persona autorizada (DPO o Secretaria principal) tiene la llave del mueble de archivos.</li>
        </ol>`
      },
      c10: {
        title: "10. Cifrado de Datos en Tránsito y Reposo (HTTPS/AES-256)",
        req: "Exigencia de la Ley de Ciberseguridad para garantizar que si un pirata informático intercepta la red, no pueda leer los datos.",
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1 (Verificar el Candadito HTTPS):</strong> Entra a la web de la empresa y revisa que la dirección empiece con <code>https://</code> y tenga el candado verde/gris de seguridad.</li>
          <li><strong>Paso 2 (Hablar con el informático):</strong> Pregúntale: <em>'¿La base de datos en el servidor está cifrada con AES-256?'</em>. Si la respuesta es no, el informático debe activar el cifrado de disco o la clave de base de datos.</li>
        </ol>`
      },
      c11: {
        title: "11. Protocolo de Notificación de Brechas (3 horas)",
        req: "Si la empresa sufre la pérdida de un computador, un virus o un hackeo, la ley exige avisar a la autoridad en menos de 3 horas.",
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1 (Imprimir el Manual de Pánico Quantus):</strong> Imprime la hoja de procedimiento de emergencia de Quantus y pégala en la oficina de TI.</li>
          <li><strong>Paso 2 (Probar el Botón de Notificación):</strong> En caso de hackeo real, el encargado presiona el botón 'Reportar Incidente' en Quantus para enviar la alerta oficial a la Agencia de Ciberseguridad en minutos.</li>
        </ol>`
      },
      c12: {
        title: "12. Control de Accesos por Roles (RBAC)",
        req: "Cada empleado debe ver ÚNICAMENTE los datos necesarios para su trabajo. Un vendedor no debe ver las liquidaciones de sueldo ni datos bancarios.",
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1 (Revisar los usuarios del sistema):</strong> Entra al panel de administración del software o ERP del cliente.</li>
          <li><strong>Paso 2 (Crear Perfiles Restringidos):</strong> Crea perfiles: 'Ventas' (solo ve productos y cliente asignado), 'Cobranza' (solo ve facturas), 'Administrador' (acceso completo).</li>
          <li><strong>Paso 3 (Desactivar ex-empleados):</strong> Borra o desactiva las cuentas de correo y claves de los trabajadores que renunciaron o fueron despedidos.</li>
        </ol>`
      },
      c13: {
        title: "13. Motor de Purga Inmediata tras Cancelación",
        req: "Si una persona pide no recibir más publicidad o cancela su suscripción, se le debe sacar INMEDIATAMENTE de las listas de difusión.",
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1 (Conectar el botón de cancelación):</strong> Dile al informático que conecte el botón 'Darme de Baja' con la API de Quantus.</li>
          <li><strong>Paso 2 (Verificar el bloqueo de WhatsApp):</strong> Al hacer clic en cancelar, el sistema borra de forma automática el número del cliente del robot de WhatsApp y listas masivas.</li>
        </ol>`
      },
      c14: {
        title: "14. Bóveda de Bloqueo Legal Exclusivo (6 años SII)",
        req: "Las boletas, facturas y contratos de clientes cancelados NO se pueden borrar al tiro si el SII obliga a guardarlas 6 años, pero tampoco se pueden usar para venderles nada.",
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1 (Mover a la Carpeta de Custodia):</strong> Las facturas y contratos de ex-clientes se mueven a una carpeta segura llamada 'Bóveda de Bloqueo Tributario'.</li>
          <li><strong>Paso 2 (Bloquear el acceso comercial):</strong> Se le quita el acceso al área de ventas para que nadie pueda llamarlos ni enviarles publicidad. Solo el contador puede leerlas si el SII lo exige.</li>
        </ol>`
      },
      c15: {
        title: "15. Destrucción Definitiva Automática a los 6 Años",
        req: "Una vez cumplido el plazo máximo tributario de 6 años (2.190 días), la información del cliente DEBE borrarse de forma permanente e irreversible.",
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1 (Activar el script de borrado Quantus):</strong> La plataforma ejecuta periódicamente el programa <code>boveda_purger_cron.py</code>.</li>
          <li><strong>Paso 2 (Verificar la destrucción):</strong> El sistema mide la fecha del expediente. Si pasaron los 6 años, destruye los archivos digitales del servidor e imprime el Registro de Purga Definitiva.</li>
        </ol>`
      }
    };'''

pos = content.find('const guiasTecnicas = {')
pos_end = content.find('let currentCorrelativo = 1;')

if pos != -1 and pos_end != -1:
    content = content[:pos] + new_guides + '\n\n    ' + content[pos_end:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("GUÍAS ULTRA DETALLADAS PASO A PASO INTEGRADAS CON ÉXITO")
else:
    print("No se encontró el bloque exacto guiasTecnicas en HTML")
