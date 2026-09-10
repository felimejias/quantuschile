path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/maestro_compliance_audit.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Código JS actualizado con recursos de descarga y herramientas rápidas para los 15 puntos
js_all_tools = '''    const guiasTecnicas = {
      c1: {
        title: "1. Registro de Actividades de Tratamiento (RAT)",
        req: "La Ley 21.719 exige tener un inventario formal declarando cada lista o sistema donde guarda RUTs, correos, nombres o teléfonos.",
        toolHtml: `<div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8;">
          <span style="font-size:12px; color:#38bdf8; font-weight:800;">🛠️ Herramienta Rápida:</span>
          <a href="/static/Plantilla_Oficial_RAT_Ley21719_Quantus.csv" download style="background:#10b981; color:#0f172a; padding:6px 12px; border-radius:8px; font-weight:800; font-size:11px; text-decoration:none;">📥 Descargar Plantilla Excel RAT</a>
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1 (Entrevista Inicial):</strong> Pregunta en Ventas, Marketing y Contabilidad dónde guardan listas de clientes.</li>
          <li><strong>Paso 2 (Listar fuentes):</strong> Anota las listas encontradas (Excels, carpetas de papel, sistemas web).</li>
          <li><strong>Paso 3 (Completar la plantilla):</strong> Descarga el Excel verde de arriba o usa el formulario rápido y llena los 5 datos.</li>
          <li><strong>Paso 4 (Cargar en Quantus):</strong> Sube el archivo listo al panel de la empresa.</li>
        </ol>`
      },
      c2: {
        title: "2. Designación de Responsable de Datos / DPO",
        req: "La empresa debe nombrar por escrito a una persona física (con nombre y RUT) encargada de responder ante reclamos y auditorías.",
        toolHtml: `<div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8;">
          <span style="font-size:12px; color:#38bdf8; font-weight:800;">🛠️ Herramienta Rápida:</span>
          <a href="/static/Plantilla_Carta_Nombramiento_DPO_Ley21719.txt" download style="background:#10b981; color:#0f172a; padding:6px 12px; border-radius:8px; font-weight:800; font-size:11px; text-decoration:none;">📥 Descargar Carta de Nombramiento DPO</a>
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Elige al encargado interno o contrata el servicio de DPO Externo Quantus.</li>
          <li><strong>Paso 2:</strong> Descarga la Carta Modelo de arriba, rellena el Nombre/RUT del DPO y hazla firmar por el representante legal.</li>
          <li><strong>Paso 3:</strong> Publica el correo <code>privacidad@empresa.cl</code> en el pie de página de su sitio web.</li>
        </ol>`
      },
      c3: {
        title: "3. Evaluación de Impacto en Protección de Datos (PIA)",
        req: "Estudio preventivo de riesgos obligatorio antes de instalar software nuevo o manejar datos delicados.",
        toolHtml: `<div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8;">
          <span style="font-size:12px; color:#38bdf8; font-weight:800;">🛠️ Herramienta Rápida:</span>
          <a href="/static/Plantilla_Matriz_PIA_Evaluacion_Riesgos_Ley21719.csv" download style="background:#10b981; color:#0f172a; padding:6px 12px; border-radius:8px; font-weight:800; font-size:11px; text-decoration:none;">📥 Descargar Matriz PIA en Excel</a>
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Pregunta si procesan datos delicados (salud, cuentas bancarias, datos de niños).</li>
          <li><strong>Paso 2:</strong> Descarga la Matriz PIA de arriba e identifica qué pasaría si se pierde ese computador.</li>
          <li><strong>Paso 3:</strong> Define la solución (ej: Clave de 10 dígitos + Antivirus) y guarda la matriz firmada.</li>
        </ol>`
      },
      c4: {
        title: "4. Aceptación Expresa sin Pre-marcado",
        req: "Las casillas que dicen 'Acepto los términos' NUNCA pueden venir marcadas con el tick azul por defecto.",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">
          💡 <strong>Código HTML que debes dar al programador:</strong><br>
          <code style="color:#10b981;">&lt;input type="checkbox" id="consent" required&gt;</code> (Sin la palabra <em>checked</em>)
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Entra al sitio web de la empresa y simula enviar un formulario.</li>
          <li><strong>Paso 2:</strong> Si la casilla de términos ya viene marcada con el tick azul, dile al informático que borre la palabra <em>checked</em> del código.</li>
          <li><strong>Paso 3:</strong> Confirma que la casilla nazca vacía para que el usuario le haga clic de forma voluntaria.</li>
        </ol>`
      },
      c5: {
        title: "5. Respaldo Criptográfico de Permisos (SHA-256)",
        req: "La empresa debe PROBAR empíricamente la aceptación de términos por cada cliente ante reclamos.",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">
          ⚙️ <strong>Integración Quantus Audit:</strong> El motor guarda automáticamente IP, Timestamp ISO-8601 y Hash SHA-256 en <code>/data/clientes/</code>.
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Copia el script de consentimiento Quantus desde tu panel.</li>
          <li><strong>Paso 2:</strong> Conéctalo al botón 'Enviar' o 'Pagar' de la web de la empresa.</li>
          <li><strong>Paso 3:</strong> Cada clic generará el comprobante JSON inalterable respaldado en la nube.</li>
        </ol>`
      },
      c6: {
        title: "6. Portal de Atención Derechos ARCO (SLA 13 días)",
        req: "Canal obligatorio en la web para responder solicitudes de borrado o acceso en máximo 13 días hábiles.",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">
          🌐 <strong>Widget de 1 Línea:</strong><br>
          <code style="color:#10b981;">&lt;script src="https://www.quantuschile.cl/static/quantus-arco-widget.js"&gt;&lt;/script&gt;</code>
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Pega el script de 1 línea en el pie de página de la web del cliente.</li>
          <li><strong>Paso 2:</strong> Aparecerá el botón flotante 'Protección de Datos & Derechos ARCO'.</li>
          <li><strong>Paso 3:</strong> Al entrar una solicitud, Quantus activa la cuenta regresiva de 13 días hábiles y notifica al DPO.</li>
        </ol>`
      },
      c7: {
        title: "7. Inventario y Etiquetado QR de Archivadores Físicos",
        req: "La Ley 21.719 sanciona la pérdida de carpetas físicas en papel que contengan fichas de clientes o RUTs.",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">
          🏷️ <strong>Generador de QR Quantus:</strong> En el panel de la empresa ingresas el nombre de la carpeta y genera el sticker listo para imprimir.
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Revisa las carpetas en papel y ordénalas por año (Ej: 'Contratos 2026').</li>
          <li><strong>Paso 2:</strong> Genera la etiqueta autoadhesiva con QR en Quantus e imprímela.</li>
          <li><strong>Paso 3:</strong> Pégala en el lomo del archivador. Al escanearla con el celular, mostrará qué papeles contiene y cuándo vence.</li>
        </ol>`
      },
      c8: {
        title: "8. Protocolo de Destrucción Física Registrada",
        req: "Destrucción certificada de documentos en papel sin botarlos a la basura común.",
        toolHtml: `<div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8;">
          <span style="font-size:12px; color:#38bdf8; font-weight:800;">🛠️ Herramienta Rápida:</span>
          <a href="/static/Plantilla_Acta_Destruccion_Fisica_Papel_Ley21719.txt" download style="background:#10b981; color:#0f172a; padding:6px 12px; border-radius:8px; font-weight:800; font-size:11px; text-decoration:none;">📥 Descargar Acta Digital de Trituración</a>
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Utilizar trituradora de papel corte cruzado DIN 66399 P-4 (deja el papel en confeti no legible).</li>
          <li><strong>Paso 2:</strong> Cuando Quantus avise que el archivador cumplió sus 6 años, tritura los papeles.</li>
          <li><strong>Paso 3:</strong> Descarga el Acta de arriba, fírmala y sube la copia al panel Quantus.</li>
        </ol>`
      },
      c9: {
        title: "9. Control de Acceso Físico a Bodegas y Ficheros",
        req: "Evitar que personas no autorizadas o visitas puedan abrir muebles con datos de clientes.",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">
          🔐 <strong>Medida Operativa:</strong> Instalación de chapa con llave o cerradura con clave numérica en muebles y puertas de archivo.
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Coloca chapa con llave o clave en la puerta de la sala de archivos o en los muebles metálicos.</li>
          <li><strong>Paso 2:</strong> Asigna la llave únicamente al DPO o Secretaria principal y mantén la puerta cerrada con seguro.</li>
        </ol>`
      },
      c10: {
        title: "10. Cifrado de Datos (HTTPS / AES-256)",
        req: "Exigencia de Ciberseguridad para proteger las comunicaciones y la base de datos.",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">
          🔒 <strong>Verificador SSL:</strong> Revisa que la dirección empiece con <code>https://</code> y tenga el candado de seguridad.
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Confirma que la web tenga certificado SSL activado (HTTPS).</li>
          <li><strong>Paso 2:</strong> Pide al informático habilitar el cifrado de disco o base de datos en reposo AES-256.</li>
        </ol>`
      },
      c11: {
        title: "11. Protocolo de Notificación de Brechas (3 horas)",
        req: "Avisar a las autoridades en menos de 3 horas si sufren un hackeo o filtración de datos.",
        toolHtml: `<div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8;">
          <span style="font-size:12px; color:#38bdf8; font-weight:800;">🛠️ Herramienta Rápida:</span>
          <a href="/static/Plantilla_Protocolo_Notificacion_Brechas_Ciberseguridad.txt" download style="background:#10b981; color:#0f172a; padding:6px 12px; border-radius:8px; font-weight:800; font-size:11px; text-decoration:none;">📥 Descargar Protocolo de Crisis 3 Horas</a>
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Descarga el Protocolo de Crisis de arriba e imprímelo en la oficina de TI.</li>
          <li><strong>Paso 2:</strong> En caso de hackeo real, sigue los 5 pasos y usa el botón de pánico Quantus para notificar a la ANCI en minutos.</li>
        </ol>`
      },
      c12: {
        title: "12. Control de Accesos por Roles (RBAC)",
        req: "Cada empleado debe ver ÚNICAMENTE los datos necesarios para su trabajo.",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">
          👤 <strong>Configuración de Perfiles:</strong> Vendedores (solo clientes asignados), Contabilidad (solo facturas), Admin (completo).
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Configura los perfiles de usuario en el software o ERP de la empresa.</li>
          <li><strong>Paso 2:</strong> Desactiva inmediatamente los accesos y correos de trabajadores que hayan renunciado.</li>
        </ol>`
      },
      c13: {
        title: "13. Motor de Purga Inmediata tras Cancelación",
        req: "Borrar de inmediato al cliente de listas de marketing al darse de baja.",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">
          ⚡ <strong>Endpoint Quantus API:</strong> <code>POST /api/cancelar_suscripcion_y_borrar_datos</code>
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Conecta el botón 'Darme de Baja' de la web a la API de Quantus.</li>
          <li><strong>Paso 2:</strong> Al presionar el botón, el bot de WhatsApp y las listas de correo sacan al cliente al instante.</li>
        </ol>`
      },
      c14: {
        title: "14. Bóveda de Bloqueo Legal Exclusivo (6 años SII)",
        req: "Aislar facturas/contratos por 6 años sin usarlos para enviar publicidad.",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">
          📦 <strong>Directorio de Bloqueo:</strong> <code>/data/boveda_legal_bloqueada/</code> en estado solo lectura.
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Mueve los respaldos de facturas de ex-clientes a la Bóveda de Bloqueo Quantus.</li>
          <li><strong>Paso 2:</strong> Quita el acceso al equipo comercial para que nadie pueda llamarlos ni enviarles ofertas.</li>
        </ol>`
      },
      c15: {
        title: "15. Destrucción Definitiva Automática a los 6 Años",
        req: "Borrado físico e irreversible de respaldos al vencer el plazo máximo legal.",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">
          ⚙️ <strong>Servidor Cron Quantus:</strong> Ejecuta <code>boveda_purger_cron.py</code> tras cumplirse los 2.190 días.
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Activa el script de purga en el servidor.</li>
          <li><strong>Paso 2:</strong> Cumplidos los 6 años, el sistema elimina permanentemente los archivos y emite el Log de Destrucción.</li>
        </ol>`
      }
    };'''

# Reemplazar la función abrirGuiaTecnica para inyectar toolHtml
js_modal_inject = '''    function abrirGuiaTecnica(id) {
      const g = guiasTecnicas[id];
      if (g) {
        document.getElementById('modal-guide-title').innerText = g.title;
        document.getElementById('modal-guide-req').innerText = g.req;
        
        let fullWorkHtml = (g.toolHtml || '') + g.work;
        document.getElementById('modal-guide-work').innerHTML = fullWorkHtml;
        
        const ratSec = document.getElementById('interactive-rat-section');
        if (id === 'c1') {
          ratSec.style.display = 'block';
          renderRatRecords();
        } else {
          ratSec.style.display = 'none';
        }

        document.getElementById('modal-item-guide').style.display = 'flex';
      }
    }'''

pos = content.find('const guiasTecnicas = {')
pos_end = content.find('let currentCorrelativo = 1;')

if pos != -1 and pos_end != -1:
    content = content[:pos] + js_all_tools + '\n\n' + js_modal_inject + '\n\n    ' + content[pos_end:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("RECURSOS Y PLANTILLAS DESCARGABLES INTEGRADAS PARA LOS 15 PUNTOS CON ÉXITO")
else:
    print("No se encontró el bloque en HTML")
