path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/maestro_compliance_audit.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Diccionario con descripciones ultra simples "para niños de 10 años" con ejemplos de la vida diaria
kid_explanations = '''    const guiasTecnicas = {
      c1: {
        title: "1. Registro de Actividades de Tratamiento (RAT)",
        req: "La Ley 21.719 exige tener un mapa o lista de todas las partes donde la empresa guarda nombres, RUTs o teléfonos.",
        toolHtml: `<div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8;">
          <span style="font-size:12px; color:#38bdf8; font-weight:800;">🛠️ Herramienta Rápida:</span>
          <a href="/static/Plantilla_Oficial_RAT_Ley21719_Quantus.csv" download style="background:#10b981; color:#0f172a; padding:6px 12px; border-radius:8px; font-weight:800; font-size:11px; text-decoration:none;">📥 Descargar Excel RAT</a>
        </div>`,
        work: `<strong>Explicación ultra fácil (Ejemplo):</strong><br>
        Imagina que tienes una libreta secreta con los números de todos tus amigos. La ley te pide anotarle una etiqueta que diga: <em>'Tengo esta lista para invitarlos a mi cumpleaños y solo la guardo yo'</em>.<br><br>
        <strong>Pasos para auditar en la empresa:</strong><br>
        1. Pregúntale a la secretaria o vendedor: <em>'¿Dónde guardan la lista de clientes?'</em> (Excels, cuadernos, archivadores en la bodega).<br>
        2. Descarga el Excel verde de arriba o usa el formulario rápido y anota cada lista encontrada.`
      },
      c2: {
        title: "2. Designación de Responsable de Datos / DPO",
        req: "Elegir por escrito a un encargado con nombre y apellido que responda si un cliente reclama o la fiscalía pregunta.",
        toolHtml: `<div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8;">
          <span style="font-size:12px; color:#38bdf8; font-weight:800;">🛠️ Herramienta Rápida:</span>
          <a href="/static/Plantilla_Carta_Nombramiento_DPO_Ley21719.txt" download style="background:#10b981; color:#0f172a; padding:6px 12px; border-radius:8px; font-weight:800; font-size:11px; text-decoration:none;">📥 Descargar Carta de Nombramiento DPO</a>
        </div>`,
        work: `<strong>Explicación ultra fácil (Ejemplo):</strong><br>
        Es como nombrar al 'Capitán del Equipo'. Si alguien rompe una ventana con la pelota, la ley quiere saber quién es el Capitán que va a dar la cara y ordenar las cosas.<br><br>
        <strong>Pasos para auditar en la empresa:</strong><br>
        1. Descarga la Carta Modelo de arriba, escribe el nombre del Gerente o Encargado y hazlo firmar.<br>
        2. Pon el correo <code>privacidad@empresa.cl</code> abajo en su página web.`
      },
      c3: {
        title: "3. Evaluación de Impacto en Protección de Datos (PIA)",
        req: "Un estudio de peligros obligatorios antes de usar programas nuevos o manejar datos delicados.",
        toolHtml: `<div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8;">
          <span style="font-size:12px; color:#38bdf8; font-weight:800;">🛠️ Herramienta Rápida:</span>
          <a href="/static/Plantilla_Matriz_PIA_Evaluacion_Riesgos_Ley21719.csv" download style="background:#10b981; color:#0f172a; padding:6px 12px; border-radius:8px; font-weight:800; font-size:11px; text-decoration:none;">📥 Descargar Matriz PIA en Excel</a>
        </div>`,
        work: `<strong>Explicación ultra fácil (Ejemplo):</strong><br>
        Es como revisar si la bicicleta tiene frenos antes de tirarte por una bajada. Te preguntas: <em>'¿Qué pasa si me caigo y cómo me protejo con casco?'</em>.<br><br>
        <strong>Pasos para auditar en la empresa:</strong><br>
        1. Descarga la Matriz de arriba y revisa qué pasaría si se pierde un computador con datos.<br>
        2. Ponle clave difícil de 10 números al computador para protegerlo.`
      },
      c4: {
        title: "4. Aceptación Expresa sin Pre-marcado",
        req: "Las casillas de 'Acepto los términos' NUNCA pueden nacer con el tick azul marcado automáticamente.",
        work: `<strong>Explicación ultra fácil (Ejemplo):</strong><br>
        Imagina que vas a comprar un helado de vainilla y el vendedor ya te puso chispas de chocolate sin preguntarte y te las cobra. La ley dice que tú debes elegir poner la chispa con tu propia mano.<br><br>
        <strong>Pasos para auditar en la empresa:</strong><br>
        1. Entra a su página web. Si la casilla de términos ya viene con el tick puesto, dile al informático que borre la palabra <em>checked</em> del código HTML para que nazca vacía.`
      },
      c5: {
        title: "5. Respaldo Criptográfico de Permisos (SHA-256)",
        req: "Guardar un comprobante digital inalterable de la fecha e IP exacta en que cada cliente dio permiso.",
        work: `<strong>Explicación ultra fácil (Ejemplo):</strong><br>
        Es como sacarle una foto con fecha y hora al recibo de una compra para que nadie pueda mentir diciendo que nunca pagó.<br><br>
        <strong>Pasos para auditar en la empresa:</strong><br>
        1. Conecta el script Quantus al botón de envío web. Cada clic guardará una foto digital con fecha, hora e IP inalterables.`
      },
      c6: {
        title: "6. Portal ARCO (SLA 10 Días Hábiles - Art. 12°)",
        req: "Tener un botón web obligatorio para responder si alguien pide borrar sus datos en máximo 10 días hábiles.",
        work: `<strong>Explicación ultra fácil (Ejemplo):</strong><br>
        Es como un buzón de reclamos rápido. Si un cliente dice <em>'Borren mi número de su lista'</em>, la empresa tiene 10 días para decirle <em>'Listo, ya te borramos'</em>.<br><br>
        <strong>Pasos para auditar en la empresa:</strong><br>
        1. Pega la línea de código del Widget Quantus en la web del cliente. Aparecerá el botón azul 'Protección de Datos & Derechos ARCO'.`
      },
      c7: {
        title: "7. Inventario y Etiquetado QR de Archivadores Físicos",
        req: "La ley exige rotular y cuidar las carpetas de papel que contengan fichas de clientes o contratos.",
        work: `<strong>Explicación ultra fácil (Ejemplo):</strong><br>
        Es como ponerle una etiqueta con tu nombre y curso a tus cuadernos del colegio para que no se pierdan en el recreo.<br><br>
        <strong>Pasos para auditar en la empresa:</strong><br>
        1. Ve a la bodega o estantes de papel.<br>
        2. Imprime el sticker QR de Quantus y pégalo en el lomo del archivador físico. Al escanearlo con el celular mostrará qué papeles guarda y cuándo vence.`
      },
      c8: {
        title: "8. Protocolo de Destrucción Física Registrada",
        req: "Prohibido botar papeles con datos de clientes a la basura común. Deben triturarse en confeti.",
        toolHtml: `<div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8;">
          <span style="font-size:12px; color:#38bdf8; font-weight:800;">🛠️ Herramienta Rápida:</span>
          <a href="/static/Plantilla_Acta_Destruccion_Fisica_Papel_Ley21719.txt" download style="background:#10b981; color:#0f172a; padding:6px 12px; border-radius:8px; font-weight:800; font-size:11px; text-decoration:none;">📥 Descargar Acta Trituración</a>
        </div>`,
        work: `<strong>Explicación ultra fácil (Ejemplo):</strong><br>
        Si tiras un dibujo con tu nombre a la basura de la calle, cualquiera puede recogerlo. Tienes que romperlo en pedacitos chiquititos antes de botarlo.<br><br>
        <strong>Pasos para auditar en la empresa:</strong><br>
        1. Pasar las hojas viejas vencidas de 6 años por una máquina trituradora de papel.<br>
        2. Descargar el Acta verde de arriba y hacerla firmar.`
      },
      c9: {
        title: "9. Control de Acceso Físico a Bodegas y Ficheros",
        req: "Poner chapa con llave en los armarios de archivos para que las visitas no los puedan abrir.",
        work: `<strong>Explicación ultra fácil (Ejemplo):</strong><br>
        Es como cerrarle la puerta con llave a tu pieza cuando vienen visitas a tu casa para que no desordenen tus juguetes.<br><br>
        <strong>Pasos para auditar en la empresa:</strong><br>
        1. Ponle candado o chapa con clave al mueble donde guardan los contratos de clientes y entrega la llave solo a la secretaria.`
      },
      c10: {
        title: "10. Cifrado de Datos (HTTPS / AES-256)",
        req: "Proteger la página web con el candado HTTPS y cifrar las bases de datos con clave secreta.",
        work: `<strong>Explicación ultra fácil (Ejemplo):</strong><br>
        Es como enviar una carta guardada adentro de un cofre metálico con candado en vez de mandar una tarjeta postal transparente que todos pueden leer.<br><br>
        <strong>Pasos para auditar en la empresa:</strong><br>
        1. Revisa que su web empiece con <code>https://</code> y tenga el candado gris de seguridad.`
      },
      c11: {
        title: "11. Protocolo de Notificación de Brechas (3 horas)",
        req: "Si roban un computador o sufre un hackeo, la ley exige avisar al gobierno en menos de 3 horas.",
        toolHtml: `<div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8;">
          <span style="font-size:12px; color:#38bdf8; font-weight:800;">🛠️ Herramienta Rápida:</span>
          <a href="/static/Plantilla_Protocolo_Notificacion_Brechas_Ciberseguridad.txt" download style="background:#10b981; color:#0f172a; padding:6px 12px; border-radius:8px; font-weight:800; font-size:11px; text-decoration:none;">📥 Descargar Protocolo Crisis 3 Horas</a>
        </div>`,
        work: `<strong>Explicación ultra fácil (Ejemplo):</strong><br>
        Si se te pierde la llave de tu casa, le avisas de inmediato a tus papás para cambiar la chapa antes de que alguien entre.<br><br>
        <strong>Pasos para auditar en la empresa:</strong><br>
        1. Descarga el manual de pánico verde de arriba y pégalo en la pared de la oficina de computación.`
      },
      c12: {
        title: "12. Control de Accesos por Roles (RBAC)",
        req: "Cada empleado debe ver solo lo que necesita para su trabajo y borrar las claves de ex-empleados.",
        work: `<strong>Explicación ultra fácil (Ejemplo):</strong><br>
        El profesor tiene la llave de la sala de profesores, pero los alumnos no. Cada persona tiene permiso solo para su espacio.<br><br>
        <strong>Pasos para auditar en la empresa:</strong><br>
        1. Revisa que los vendedores no puedan ver los sueldos ni las cuentas del banco de la empresa.<br>
        2. Borra las claves de los trabajadores que fueron despedidos.`
      },
      c13: {
        title: "13. Motor de Purga Inmediata tras Cancelación",
        req: "Si un cliente dice 'no me manden más publicidad', hay que sacarlo al instante del sistema.",
        work: `<strong>Explicación ultra fácil (Ejemplo):</strong><br>
        Si le dices a un amigo <em>'ya no quiero jugar más'</em>, tu amigo debe dejar de llamarte a jugar ese día.<br><br>
        <strong>Pasos para auditar en la empresa:</strong><br>
        1. Conecta el botón de desuscripción a la API Quantus para que el bot de WhatsApp deje de mandar ofertas en el segundo exacto.`
      },
      c14: {
        title: "14. Bóveda de Bloqueo Legal Exclusivo (6 años SII)",
        req: "Guardar las boletas y facturas 6 años por exigencia del SII, pero sin usarlas para vender nada.",
        work: `<strong>Explicación ultra fácil (Ejemplo):</strong><br>
        Es como guardar las pruebas de tus exámenes del año pasado en un cajón cerrado: están ahí por si el profesor pregunta, pero no las usas para hacer tareas nuevas.<br><br>
        <strong>Pasos para auditar en la empresa:</strong><br>
        1. Mueve las facturas viejas a la carpeta <code>/boveda_legal_bloqueada/</code> y quítale el acceso al equipo de ventas.`
      },
      c15: {
        title: "15. Destrucción Definitiva Automática a los 6 Años",
        req: "Borrado permanente e irreversible de archivos digitales cumplidos los 6 años tributarios.",
        work: `<strong>Explicación ultra fácil (Ejemplo):</strong><br>
        Es como usar una goma de borrar mágica que desintegra el papel de forma que nadie en el mundo pueda volver a leerlo.<br><br>
        <strong>Pasos para auditar en la empresa:</strong><br>
        1. Activa el programa automático <code>boveda_purger_cron.py</code> que mide las fechas y borra los archivos viejos.`
      },
      c16: {
        title: "16. Consentimiento Escrito para Datos Sensibles (Art. 32°)",
        req: "Permiso firmado en papel o digital explícito para fichas médicas, fotos de salud o huellas.",
        work: `<strong>Explicación ultra fácil (Ejemplo):</strong><br>
        Si vas al doctor, le das permiso firmado para que revise tu cuerpo y anote qué remedio necesitas.<br><br>
        <strong>Pasos para auditar en la empresa:</strong><br>
        1. Si es clínica o laboratorio, haz firmar el anexo impreso de salud antes de tomar exámenes o fichas.`
      },
      c17: {
        title: "17. Protección de Datos de Niños y Apoderados (Art. 34°)",
        req: "Prohibición absoluta de usar datos de niños para venderles cosas y permiso de los papás.",
        work: `<strong>Explicación ultra fácil (Ejemplo):</strong><br>
        En el colegio, para ir a una excursión o usar tu foto, la profesora tiene que pedirle la firma en una libreta a tu papá o mamá.<br><br>
        <strong>Pasos para auditar en la empresa:</strong><br>
        1. En colegios y jardines, haz firmar en la matrícula la autorización de los apoderados.`
      },
      c18: {
        title: "18. Declaración de Nubes Extranjeras (AWS/Google - Art. 26°)",
        req: "Avisar si la empresa guarda los datos en servidores ubicados fuera de Chile.",
        work: `<strong>Explicación ultra fácil (Ejemplo):</strong><br>
        Si dejas tu mochila encargada en la casa de tu vecino, tienes que avisarle a tus papás en qué casa está guardada.<br><br>
        <strong>Pasos para auditar en la empresa:</strong><br>
        1. Escribe en su política web: <em>'Tus datos están guardados en servidores seguros de Google/AWS en Estados Unidos'</em>.`
      },
      c19: {
        title: "19. Portabilidad de Datos en JSON (Art. 7° bis)",
        req: "Permitir al cliente descargar toda su información en un archivo digital para llevárselo.",
        work: `<strong>Explicación ultra fácil (Ejemplo):</strong><br>
        Es como cuando te cambias de colegio y pides tu carpeta de notas en una bolsa para entregársela al director del colegio nuevo.<br><br>
        <strong>Pasos para auditar en la empresa:</strong><br>
        1. Activa el botón 'Descargar Mis Datos en JSON' en la web para que el usuario descargue su archivo comprimido.`
      },
      c20: {
        title: "20. Oposición a Decisiones por Algoritmos/IA (Art. 15°)",
        req: "Derecho a exigir que una persona humana revise si un robot o IA rechazó una solicitud.",
        work: `<strong>Explicación ultra fácil (Ejemplo):</strong><br>
        Si un juego de computador te dice <em>'Perdiste'</em> por error, tú pides que un árbitro humano venga a mirar la jugada para corregir el resultado.<br><br>
        <strong>Pasos para auditar en la empresa:</strong><br>
        1. Si usan robots o IA para evaluar clientes, pon un botón que diga: <em>'Solicitar que un Ejecutivo Humano revise mi caso'</em>.`
      },
      c21: {
        title: "21. Transparencia de Perfilamiento Digital (Art. 14°)",
        req: "Informar al usuario si se le rastrea la navegación web para enviarle publicidad.",
        work: `<strong>Explicación ultra fácil (Ejemplo):</strong><br>
        Es como avisar con un letrero que hay un detective mirando qué juguetes te gustan en la tienda.<br><br>
        <strong>Pasos para auditar en la empresa:</strong><br>
        1. Activa el Banner de Cookies de Quantus que pide permiso antes de rastrear la web.`
      },
      c22: {
        title: "22. Registro de Período de Gracia PyME (Art. Transitorio)",
        req: "Las PyMEs que venden menos de $960 Millones CLP tienen 1 año de acompañamiento sin multas de dinero.",
        work: `<strong>Explicación ultra fácil (Ejemplo):</strong><br>
        Es como cuando juegas un juego nuevo y la primera partida es 'de prueba' sin perder puntos para que aprendas las reglas.<br><br>
        <strong>Pasos para auditar en la empresa:</strong><br>
        1. Revisa el F29 del SII. Si vende menos de $960.000.000 CLP al año, emite el Certificado PyME Quantus.`
      },
      c23: {
        title: "23. Protección de Datos de Trabajadores y Anexo RRHH",
        req: "Proteger las liquidaciones de sueldo y hacer firmar anexo laboral a los empleados.",
        toolHtml: `<div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8;">
          <span style="font-size:12px; color:#38bdf8; font-weight:800;">🛠️ Herramienta Rápida:</span>
          <a href="/static/Plantilla_Anexo_Contrato_Trabajo_Proteccion_Datos_Ley21719.txt" download style="background:#10b981; color:#0f172a; padding:6px 12px; border-radius:8px; font-weight:800; font-size:11px; text-decoration:none;">📥 Descargar Anexo Trabajo RRHH</a>
        </div>`,
        work: `<strong>Explicación ultra fácil (Ejemplo):</strong><br>
        Los sueldos y fichas médicas de los trabajadores son secretos. No se pueden dejar tirados encima del escritorio del jefe.<br><br>
        <strong>Pasos para auditar en la empresa:</strong><br>
        1. Descarga el Anexo de Trabajo de arriba y hazlo firmar a todos los empleados de la empresa.`
      },
      c24: {
        title: "24. Carteles Informativos de Cámaras y Videovigilancia",
        req: "Obligación de instalar carteles informativos avisando que las cámaras graban rostros a clientes y trabajadores.",
        toolHtml: `<div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8;">
          <span style="font-size:12px; color:#38bdf8; font-weight:800;">🛠️ Herramienta Rápida:</span>
          <a href="/static/Plantilla_Cartel_Oficial_Videovigilancia_Camaras.txt" download style="background:#10b981; color:#0f172a; padding:6px 12px; border-radius:8px; font-weight:800; font-size:11px; text-decoration:none;">📥 Descargar Cartel Oficial Cámaras</a>
        </div>`,
        work: `<strong>Explicación ultra fácil (Ejemplo):</strong><br>
        Si pones un ojo mágico o cámara en tu puerta, tienes que poner un cartel brillante que diga: <em>'Atención, te estamos sonriendo y grabando por seguridad'</em>.<br><br>
        <strong>Pasos para auditar en la empresa:</strong><br>
        1. Descarga el cartel de arriba, imprímelo y pégalo en la puerta de entrada de los locales u oficinas.`
      }
    };'''

pos = content.find('const guiasTecnicas = {')
pos_end = content.find('let currentCorrelativo = 1;')

if pos != -1 and pos_end != -1:
    content = content[:pos] + kid_explanations + '\n\n    ' + content[pos_end:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("REESCRITURA COMPLETA CON EXPLICACIONES Y EJEMPLOS PARA NIÑOS DE 10 AÑOS INTEGRADA EN MAESTRO")
else:
    print("No se encontró el bloque en HTML")
