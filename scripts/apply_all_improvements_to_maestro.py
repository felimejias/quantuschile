path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/maestro_compliance_audit.html'

html_full_updated = '''<!DOCTYPE html>
<html lang="es-CL">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Centro Maestro — Auditoría de Cumplimiento Ley 21.719 | Quantus Private</title>
  <link rel="icon" type="image/png" href="{{ url_for('static', filename='quantus-logo-clean.png') }}">
  <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
  <style>
    :root {
      --bg-dark: #090d16;
      --card-bg: #1e293b;
      --accent-blue: #38bdf8;
      --accent-green: #10b981;
      --accent-red: #ef4444;
      --accent-orange: #f59e0b;
    }
    body { background: var(--bg-dark); color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; padding: 0; margin: 0; -webkit-tap-highlight-color: transparent; }
    .header-bar { background: rgba(15,23,42,0.95); border-bottom: 1px solid rgba(56,189,248,0.2); padding: 12px 20px; position: sticky; top: 0; z-index: 1000; backdrop-filter: blur(10px); display: flex; justify-content: space-between; align-items: center; }
    .container { max-width: 1000px; margin: 0 auto; padding: 16px; }
    
    .company-card { background: var(--card-bg); border: 1px solid rgba(56,189,248,0.3); border-radius: 16px; padding: 20px; margin-bottom: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
    .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; margin-top: 12px; }
    .form-group label { display: block; font-size: 11px; font-weight: 800; color: #94a3b8; text-transform: uppercase; margin-bottom: 4px; letter-spacing: 0.5px; }
    .form-group input { width: 100%; padding: 12px; background: #0f172a; border: 1px solid #334155; color: #fff; border-radius: 10px; font-size: 14px; box-sizing: border-box; }
    
    .progress-bar-container { background: #0f172a; border: 1px solid #334155; border-radius: 12px; padding: 16px; margin: 20px 0; display: flex; align-items: center; justify-content: space-between; gap: 16px; sticky; top: 60px; z-index: 900; }
    .progress-track { flex: 1; height: 14px; background: #334155; border-radius: 999px; overflow: hidden; }
    .progress-fill { height: 100%; width: 0%; background: linear-gradient(90deg, #38bdf8, #10b981); transition: width 0.3s ease; }
    
    .module-section { background: #0f172a; border: 1px solid #334155; border-radius: 14px; margin-bottom: 20px; overflow: hidden; }
    .module-header { background: #1e293b; padding: 14px 20px; font-weight: 800; font-size: 15px; color: #38bdf8; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; }
    .check-item { padding: 14px 20px; border-bottom: 1px solid rgba(255,255,255,0.05); display: flex; align-items: flex-start; gap: 14px; cursor: pointer; transition: background 0.15s; }
    .check-item:last-child { border-bottom: none; }
    .check-item:hover { background: rgba(56,189,248,0.05); }
    .check-item input[type="checkbox"] { width: 22px; height: 22px; accent-color: #10b981; margin-top: 2px; cursor: pointer; flex-shrink: 0; }
    .item-content { flex: 1; }
    .item-title { font-size: 14px; font-weight: 700; color: #f1f5f9; margin-bottom: 2px; }
    .item-desc { font-size: 12px; color: #94a3b8; line-height: 1.4; }
    
    .badge-prio { font-size: 10px; font-weight: 900; padding: 4px 8px; border-radius: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
    .prio-alta { background: rgba(239,68,68,0.2); color: #fca5a5; border: 1px solid rgba(239,68,68,0.4); }
    .prio-media { background: rgba(245,158,11,0.2); color: #fcd34d; border: 1px solid rgba(245,158,11,0.4); }
    .prio-baja { background: rgba(16,185,129,0.2); color: #6ee7b7; border: 1px solid rgba(16,185,129,0.4); }
    
    .action-bar { display: flex; gap: 12px; margin-top: 24px; padding-bottom: 40px; flex-wrap: wrap; }
    .btn-action { flex: 1; min-width: 160px; padding: 14px; border-radius: 12px; font-weight: 800; font-size: 13px; text-align: center; border: none; cursor: pointer; text-transform: uppercase; letter-spacing: 0.5px; }
    .btn-save { background: #10b981; color: #0f172a; }
    .btn-cert { background: linear-gradient(90deg, #f59e0b, #eab308); color: #0f172a; font-weight: 900; }
    .btn-next { background: #38bdf8; color: #0f172a; }
    .btn-delete { background: rgba(239,68,68,0.2); color: #fca5a5; border: 1px solid rgba(239,68,68,0.4); }

    .custom-modal-overlay { display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(6, 16, 31, 0.88); backdrop-filter: blur(8px); z-index: 999999; align-items: center; justify-content: center; padding: 16px; box-sizing: border-box; }
    .custom-modal-card { background: #0f172a; border: 1px solid #38bdf8; padding: 24px; border-radius: 16px; max-width: 650px; width: 100%; box-shadow: 0 20px 40px rgba(0,0,0,0.8); max-height: 90vh; overflow-y: auto; }
  </style>
</head>
<body>

  <header class="header-bar">
    <div style="display:flex; align-items:center; gap:10px;">
      <img src="{{ url_for('static', filename='quantus-logo-clean.png') }}" alt="Quantus" style="height:28px;">
      <span style="font-weight:900; color:#fff; font-size:16px;">QUANTUS <span style="color:#38bdf8;">AUDIT PRIVATE</span></span>
    </div>
    <span style="background:rgba(245,158,11,0.2); color:#fcd34d; padding:4px 10px; border-radius:999px; font-size:11px; font-weight:800;">🔒 PANEL PRIVADO MAESTRO</span>
  </header>

  <main class="container">

    <div class="company-card">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
        <h2 style="margin:0; font-size:18px; color:#fff;">📋 Ficha de Auditoría de Cumplimiento Ley 21.719 & Conexas</h2>
        <span id="correlativo-display" style="background:#38bdf8; color:#0f172a; padding:4px 12px; border-radius:8px; font-weight:900; font-size:13px;">CORRELATIVO #1</span>
      </div>

      <div class="form-grid">
        <div class="form-group">
          <label>N° Registro Correlativo Interno</label>
          <input type="text" id="audit_correlativo" readonly style="background:#1e293b; color:#38bdf8; font-weight:800;">
        </div>
        <div class="form-group">
          <label>Nombre de la Empresa / Razón Social *</label>
          <input type="text" id="emp_nombre" placeholder="Ej: Clínica Santa María / Colegio Saint George" oninput="autoGuardarDatos()">
        </div>
        <div class="form-group">
          <label>RUT Empresa *</label>
          <input type="text" id="emp_rut" placeholder="Ej: 78.478.612-9" oninput="autoGuardarDatos()">
        </div>
        <div class="form-group">
          <label>Nombre del Responsable / DPO *</label>
          <input type="text" id="emp_responsable" placeholder="Ej: Carlos Silva (Gerente Legal)" oninput="autoGuardarDatos()">
        </div>
        <div class="form-group">
          <label>Correo Electrónico *</label>
          <input type="email" id="emp_email" placeholder="ejemplo@empresa.cl" oninput="autoGuardarDatos()">
        </div>
        <div class="form-group">
          <label>Teléfono / WhatsApp *</label>
          <input type="tel" id="emp_phone" placeholder="+56 9 1234 5678" oninput="autoGuardarDatos()">
        </div>
        <div class="form-group" style="grid-column: 1 / -1;">
          <label>Dirección Legal Completa *</label>
          <input type="text" id="emp_direccion" placeholder="Ej: Av. Andrés Bello 2457, Providencia, Santiago" oninput="autoGuardarDatos()">
        </div>
      </div>
    </div>

    <div class="progress-bar-container">
      <div>
        <div style="font-size:11px; color:#94a3b8; font-weight:800; text-transform:uppercase;">Nivel de Cumplimiento Registrado</div>
        <div id="porcentaje-num" style="font-size:24px; font-weight:900; color:#10b981;">0% COMPLETADO</div>
      </div>
      <div class="progress-track">
        <div id="progress-fill" class="progress-fill"></div>
      </div>
    </div>

    <div id="checklist-modules-container"></div>

    <div class="action-bar">
      <button type="button" class="btn-action btn-save" onclick="guardarAuditoriaActual()">💾 Guardar Auditoría</button>
      <button type="button" class="btn-action btn-cert" onclick="descargarCertificadoOficial()">🏆 Emitir Certificado PDF</button>
      <button type="button" class="btn-action btn-next" onclick="siguienteCorrelativo()">➡️ Crear Siguiente (#+1)</button>
      <button type="button" class="btn-action btn-delete" onclick="borrarAuditoriaActual()">🗑️ Borrar Ficha</button>
    </div>

  </main>

  <!-- Modal Explicativo Guía Técnica + Herramientas -->
  <div id="modal-item-guide" class="custom-modal-overlay">
    <div class="custom-modal-card">
      <button type="button" onclick="cerrarModalGuia()" style="float:right; background:none; border:none; color:#94a3b8; font-size:24px; cursor:pointer;">&times;</button>
      <span style="background:rgba(56,189,248,0.2); color:#38bdf8; padding:4px 10px; border-radius:999px; font-size:11px; font-weight:800;">GUÍA DE EJECUCIÓN Y REMEDIACIÓN TÉCNICA</span>
      <h3 id="modal-guide-title" style="font-size:18px; color:#fff; margin-top:10px; margin-bottom:12px;"></h3>
      
      <div style="background:#1e293b; border-left:4px solid #38bdf8; padding:14px; border-radius:8px; margin-bottom:16px;">
        <h4 style="margin:0 0 6px 0; color:#38bdf8; font-size:13px; text-transform:uppercase;">⚖️ Requisito Exigido por Ley N° 21.719 & Conexas:</h4>
        <p id="modal-guide-req" style="margin:0; font-size:13px; color:#cbd5e1; line-height:1.5;"></p>
      </div>

      <!-- Formulario Dinámico RAT (Solo activo en Punto 1) -->
      <div id="interactive-rat-section" style="display:none; margin-bottom:16px; background:#1e293b; border:1px solid #38bdf8; border-radius:12px; padding:16px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
          <h4 style="margin:0; color:#38bdf8; font-size:14px;">📝 Generador Directo RAT (Opción Fácil)</h4>
          <a href="/static/Plantilla_Oficial_RAT_Ley21719_Quantus.csv" download style="background:#10b981; color:#0f172a; padding:6px 12px; border-radius:8px; font-weight:800; font-size:11px; text-decoration:none;">📥 Descargar Excel RAT</a>
        </div>
        
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:10px;">
          <input type="text" id="rat_nombre_lista" placeholder="Nombre de la Lista (Ej: Excel Clientes)" style="padding:8px; background:#0f172a; border:1px solid #475569; color:#fff; border-radius:6px; font-size:12px;">
          <select id="rat_soporte" style="padding:8px; background:#0f172a; border:1px solid #475569; color:#fff; border-radius:6px; font-size:12px;">
            <option value="Digital (Excel / Software / Web)">Digital (Excel / Software / Web)</option>
            <option value="Físico (Papel en Archivador)">Físico (Papel en Archivador)</option>
          </select>
          <input type="text" id="rat_datos" placeholder="Datos que guarda (Ej: RUT, Salud, Nombres)" style="padding:8px; background:#0f172a; border:1px solid #475569; color:#fff; border-radius:6px; font-size:12px;">
          <input type="text" id="rat_finalidad" placeholder="Para qué los usan (Ej: Fichas clínicas)" style="padding:8px; background:#0f172a; border:1px solid #475569; color:#fff; border-radius:6px; font-size:12px;">
        </div>

        <button type="button" onclick="agregarFilaRAT()" style="width:100%; padding:8px; background:#38bdf8; color:#0f172a; font-weight:800; border:none; border-radius:6px; cursor:pointer; font-size:12px;">+ Agregar Registro al RAT de esta Empresa</button>
        
        <div id="rat-records-list" style="margin-top:12px; font-size:11px; color:#cbd5e1; max-height:120px; overflow-y:auto;"></div>
      </div>

      <div style="background:#1e293b; border-left:4px solid #10b981; padding:14px; border-radius:8px;">
        <h4 style="margin:0 0 6px 0; color:#10b981; font-size:13px; text-transform:uppercase;">🛠️ Trabajo Técnico / Pasos para Auditar en la Empresa:</h4>
        <div id="modal-guide-work" style="font-size:13px; color:#cbd5e1; line-height:1.5;"></div>
      </div>

      <button type="button" onclick="cerrarModalGuia()" style="width:100%; margin-top:20px; padding:12px; background:#38bdf8; color:#0f172a; font-weight:900; border:none; border-radius:10px; cursor:pointer;">Entendido — Volver al Checklist</button>
    </div>
  </div>

  <script>
    // Inventario Exhaustivo de 18 Controles de Rigor (Incluye Módulo 6: Datos Sensibles, Salud y Menores)
    const checklistData = [
      {
        modulo: "MÓDULO 1: GOBERNANZA Y REGISTRO DE TRATAMIENTO (RAT)",
        items: [
          { id: "c1", prio: "alta", title: "1. Registro de Actividades de Tratamiento (RAT)", desc: "Mapeo documentado de todas las bases de datos de clientes, empleados y proveedores." },
          { id: "c2", prio: "alta", title: "2. Designación de Responsable de Datos / DPO", desc: "Nombramiento formal del encargado interno o externo de protección de datos." },
          { id: "c3", prio: "media", title: "3. Evaluación de Impacto en Protección de Datos (PIA)", desc: "Matriz de riesgos para nuevos proyectos o sistemas que manejen datos masivos." }
        ]
      },
      {
        modulo: "MÓDULO 2: CONSENTIMIENTO Y PORTAL WEB",
        items: [
          { id: "c4", prio: "alta", title: "4. Aceptación Expresa sin Pre-marcado", desc: "Casillas de verificación de política de privacidad desmarcadas por defecto en todos los formularios." },
          { id: "c5", prio: "alta", title: "5. Respaldo Criptográfico de Permisos (SHA-256)", desc: "Guardado de IP, fecha, hora y versión exacta de términos aceptados por cada cliente." },
          { id: "c6", prio: "alta", title: "6. Portal de Atención Derechos ARCO (SLA 10 Días Hábiles)", desc: "Formulario web exclusivo para tramitar solicitudes de borrado o acceso en máximo 10 días hábiles (Art. 12°)." }
        ]
      },
      {
        modulo: "MÓDULO 3: DOCUMENTACIÓN FÍSICA Y ARCHIVADORES EN PAPEL",
        items: [
          { id: "c7", prio: "alta", title: "7. Inventario y Etiquetado QR de Archivadores Físicos", desc: "Identificación de carpetas físicas en papel con código QR y fecha de expiración." },
          { id: "c8", prio: "media", title: "8. Protocolo de Destrucción Física Registrada", desc: "Trituración certificada de documentos en papel cumplidos los plazos legales (6 años SII)." },
          { id: "c9", prio: "baja", title: "9. Control de Acceso Físico a Bodegas y Ficheros", desc: "Llaves o tarjeta de acceso restringido a salas de archivo en papel." }
        ]
      },
      {
        modulo: "MÓDULO 4: CIBERSEGURIDAD Y CONEXIDAD NORMATIVA",
        items: [
          { id: "c10", prio: "alta", title: "10. Cifrado de Datos en Tránsito y Reposo (HTTPS/AES-256)", desc: "Protección de bases de datos y comunicaciones (Cumplimiento Ley 21.663 de Ciberseguridad)." },
          { id: "c11", prio: "alta", title: "11. Protocolo de Notificación de Brechas (3 horas)", desc: "Plan de respuesta ante hackeo o filtración para avisar a la ANCI y a la Agencia de Datos." },
          { id: "c12", prio: "media", title: "12. Control de Accesos por Roles (RBAC)", desc: "Permisos diferenciados por empleado para evitar filtraciones internas (Ley 21.459)." }
        ]
      },
      {
        modulo: "MÓDULO 5: PURGA Y RETENCIÓN DE DATOS (CICLO DE VIDA)",
        items: [
          { id: "c13", prio: "alta", title: "13. Motor de Purga Inmediata tras Cancelación", desc: "Desactivación instantánea de listas de WhatsApp y marketing al pedir la baja el cliente." },
          { id: "c14", prio: "alta", title: "14. Bóveda de Bloqueo Legal Exclusivo (6 años SII)", desc: "Aislamiento de facturas y contratos sin uso comercial durante el plazo de prescripción." },
          { id: "c15", prio: "media", title: "15. Destrucción Definitiva Automática a los 6 Años", desc: "Borrado físico e irreversible de respaldos una vez vencido el plazo máximo legal." }
        ]
      },
      {
        modulo: "MÓDULO 6: DATOS SENSIBLES, SALUD Y MENORES DE EDAD (NUEVO)",
        items: [
          { id: "c16", prio: "alta", title: "16. Consentimiento Escrito para Datos Sensibles (Art. 2° lit. g)", desc: "Consentimiento formal para fichas clínicas, datos de salud, huellas biométricas o aflicción religiosa." },
          { id: "c17", prio: "alta", title: "17. Protección de Datos de Niños y Apoderados (Art. 2° lit. h)", desc: "Prohibición de uso comercial y autorización expresa de padres o apoderados en colegios e instituciones." },
          { id: "c18", prio: "alta", title: "18. Declaración de Transferencia Internacional de Nubes (Art. 26°)", desc: "Registro formal si la empresa usa servidores extranjeros como Google, AWS, Mailchimp o WhatsApp." }
        ]
      }
    ];

    const guiasTecnicas = {
      c1: {
        title: "1. Registro de Actividades de Tratamiento (RAT)",
        req: "La Ley 21.719 exige tener un inventario formal declarando cada lista o sistema donde guarda RUTs, correos, nombres o teléfonos.",
        toolHtml: `<div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8;">
          <span style="font-size:12px; color:#38bdf8; font-weight:800;">🛠️ Herramienta Rápida:</span>
          <a href="/static/Plantilla_Oficial_RAT_Ley21719_Quantus.csv" download style="background:#10b981; color:#0f172a; padding:6px 12px; border-radius:8px; font-weight:800; font-size:11px; text-decoration:none;">📥 Descargar Plantilla Excel RAT</a>
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Pregunta en Ventas, Marketing y Contabilidad dónde guardan listas de clientes.</li>
          <li><strong>Paso 2:</strong> Anota las listas encontradas (Excels, carpetas de papel, sistemas web).</li>
          <li><strong>Paso 3:</strong> Descarga el Excel verde de arriba o usa el formulario rápido y llena los datos.</li>
          <li><strong>Paso 4:</strong> Sube el archivo listo al panel de la empresa.</li>
        </ol>`
      },
      c2: {
        title: "2. Designación de Responsable de Datos / DPO",
        req: "La empresa debe nombrar por escrito a una persona física (con nombre y RUT) encargada de responder ante reclamos.",
        toolHtml: `<div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8;">
          <span style="font-size:12px; color:#38bdf8; font-weight:800;">🛠️ Herramienta Rápida:</span>
          <a href="/static/Plantilla_Carta_Nombramiento_DPO_Ley21719.txt" download style="background:#10b981; color:#0f172a; padding:6px 12px; border-radius:8px; font-weight:800; font-size:11px; text-decoration:none;">📥 Descargar Carta de Nombramiento DPO</a>
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Elige al encargado interno o contrata DPO Externo Quantus.</li>
          <li><strong>Paso 2:</strong> Descarga la Carta Modelo, rellena el Nombre/RUT del DPO y hazla firmar por el representante legal.</li>
          <li><strong>Paso 3:</strong> Publica el correo <code>privacidad@empresa.cl</code> en la web.</li>
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
          <li><strong>Paso 2:</strong> Descarga la Matriz PIA de arriba e identifica qué pasaría si se pierde el computador.</li>
          <li><strong>Paso 3:</strong> Define la solución (ej: Clave de 10 dígitos + Antivirus) y guarda la matriz firmada.</li>
        </ol>`
      },
      c4: {
        title: "4. Aceptación Expresa sin Pre-marcado",
        req: "Las casillas que dicen 'Acepto los términos' NUNCA pueden venir marcadas por defecto.",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">
          💡 <strong>Código HTML listo:</strong> <code style="color:#10b981;">&lt;input type="checkbox" id="consent" required&gt;</code>
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Entra al sitio web del cliente y simula enviar un formulario.</li>
          <li><strong>Paso 2:</strong> Si la casilla ya viene marcada, dile al informático que borre la palabra <em>checked</em> del código.</li>
        </ol>`
      },
      c5: {
        title: "5. Respaldo Criptográfico de Permisos (SHA-256)",
        req: "La empresa debe PROBAR empíricamente la aceptación de términos por cada cliente ante reclamos.",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">
          ⚙️ <strong>Integración Quantus Audit:</strong> Registro automático de IP, ISO-8601 Timestamp y SHA-256 Hash.
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Copia el script de consentimiento Quantus desde tu panel.</li>
          <li><strong>Paso 2:</strong> Conéctalo al botón de envío web del cliente.</li>
        </ol>`
      },
      c6: {
        title: "6. Portal ARCO (SLA 10 Días Hábiles - Art. 12°)",
        req: "El Artículo 12° exige responder solicitudes de borrado o acceso en máximo 10 DÍAS HÁBILES.",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">
          🌐 <strong>Widget SLA 10 Días:</strong> <code style="color:#10b981;">&lt;script src="https://www.quantuschile.cl/static/quantus-arco-widget.js"&gt;&lt;/script&gt;</code>
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Pega el script de 1 línea en la web del cliente.</li>
          <li><strong>Paso 2:</strong> Al entrar una solicitud, Quantus activa el temporizador exacto de 10 días hábiles.</li>
        </ol>`
      },
      c7: {
        title: "7. Inventario y Etiquetado QR de Archivadores Físicos",
        req: "Sanción por pérdida de carpetas físicas en papel que contengan fichas de clientes.",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">
          🏷️ <strong>Generador QR:</strong> Ingresas el archivador y genera la etiqueta autoadhesiva.
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Ordena carpetas de papel por año.</li>
          <li><strong>Paso 2:</strong> Imprime la etiqueta QR Quantus y pégala en el lomo del archivador.</li>
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
          <li><strong>Paso 1:</strong> Usar trituradora corte cruzado DIN 66399 P-4.</li>
          <li><strong>Paso 2:</strong> Triturar papeles cumplidos 6 años SII y firmar el Acta de arriba.</li>
        </ol>`
      },
      c9: {
        title: "9. Control de Acceso Físico a Bodegas y Ficheros",
        req: "Evitar acceso de visitas a muebles con datos de clientes.",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">
          🔐 <strong>Medida Operativa:</strong> Chapa con llave o clave numérica en muebles de archivo.
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Colocar seguro con clave en muebles de archivo y mantener la llave en manos del DPO.</li>
        </ol>`
      },
      c10: {
        title: "10. Cifrado de Datos (HTTPS / AES-256)",
        req: "Protección de comunicaciones y bases de datos (Ley 21.663).",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">
          🔒 <strong>Verificación SSL:</strong> Candado de seguridad en la URL HTTPS.
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Forzar HTTPS en el sitio web y habilitar cifrado de disco AES-256.</li>
        </ol>`
      },
      c11: {
        title: "11. Protocolo de Notificación de Brechas (3 horas)",
        req: "Avisar a las autoridades en menos de 3 horas si sufren hackeo.",
        toolHtml: `<div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8;">
          <span style="font-size:12px; color:#38bdf8; font-weight:800;">🛠️ Herramienta Rápida:</span>
          <a href="/static/Plantilla_Protocolo_Notificacion_Brechas_Ciberseguridad.txt" download style="background:#10b981; color:#0f172a; padding:6px 12px; border-radius:8px; font-weight:800; font-size:11px; text-decoration:none;">📥 Descargar Protocolo de Crisis 3 Horas</a>
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Descargar e imprimir el Protocolo de Crisis de arriba.</li>
        </ol>`
      },
      c12: {
        title: "12. Control de Accesos por Roles (RBAC)",
        req: "Permisos diferenciados por empleado.",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">
          👤 <strong>Separación de Perfiles:</strong> Vendedores vs Contabilidad.
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Desactivar accesos de ex-empleados despedidos.</li>
        </ol>`
      },
      c13: {
        title: "13. Motor de Purga Inmediata tras Cancelación",
        req: "Borrar al cliente de listas de marketing al darse de baja.",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">
          ⚡ <strong>Endpoint API:</strong> <code>POST /api/cancelar_suscripcion_y_borrar_datos</code>
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Conectar el botón de cancelación a la API Quantus.</li>
        </ol>`
      },
      c14: {
        title: "14. Bóveda de Bloqueo Legal Exclusivo (6 años SII)",
        req: "Aislar facturas por 6 años sin uso comercial.",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">
          📦 <strong>Carpeta aislada:</strong> <code>/data/boveda_legal_bloqueada/</code>
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Mover facturas canceladas a la Bóveda de Custodia.</li>
        </ol>`
      },
      c15: {
        title: "15. Destrucción Definitiva Automática a los 6 Años",
        req: "Borrado físico e irreversible al vencer plazo legal.",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">
          ⚙️ <strong>Servidor Cron:</strong> <code>boveda_purger_cron.py</code> a los 2.190 días.
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Activar script cron de purga automática.</li>
        </ol>`
      },
      c16: {
        title: "16. Consentimiento Escrito para Datos Sensibles (Art. 2° lit. g)",
        req: "Exigencia de consentimiento explícito firmado para fichas médicas, salud o datos biométricos.",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">
          🏥 <strong>Módulo Salud & Clínicas:</strong> Cláusula especial de consentimiento para tratamientos médicos o datos sensibles.
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Si la empresa es Clínica o Laboratorio, hacer firmar el anexo impreso de autorización de ficha de salud.</li>
          <li><strong>Paso 2:</strong> Cifrar con clave de 24 bits las fichas de pacientes.</li>
        </ol>`
      },
      c17: {
        title: "17. Protección de Datos de Niños y Apoderados (Art. 2° lit. h)",
        req: "Prohibición de uso comercial de datos de menores; autorización expresa de padres.",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">
          🏫 <strong>Módulo Educación & Colegios:</strong> Formulario de autorización de apoderados para tratamiento escolar.
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> En matrícula, hacer firmar al apoderado la autorización explícita para uso de datos escolares.</li>
          <li><strong>Paso 2:</strong> Prohibir estrictamente el envío de ofertas comerciales a los alumnos.</li>
        </ol>`
      },
      c18: {
        title: "18. Declaración de Transferencia Internacional de Nubes (Art. 26°)",
        req: "Registro obligatorio si la empresa envía datos a servidores fuera de Chile (AWS, Google, Mailchimp, WhatsApp).",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">
          ☁️ <strong>Declaración de Nube Extranjera:</strong> Cláusula de traspaso internacional de datos a centros autorizados (EE.UU. / UE).
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Incluir en la política web: <em>'Sus datos podrán ser procesados en infraestructura segura de Google Cloud / AWS en EE.UU.'</em></li>
        </ol>`
      }
    };

    let currentCorrelativo = 1;
    let ratItems = [];
    let auditStore = JSON.parse(localStorage.getItem('quantus_audits_db') || '{}');

    function initChecklist() {
      const keys = Object.keys(auditStore).map(k => parseInt(k)).filter(n => !isNaN(n));
      if (keys.length > 0) {
        currentCorrelativo = Math.max(...keys);
      }
      cargarCorrelativo(currentCorrelativo);
    }

    function renderModules(checkedStates = {}) {
      const container = document.getElementById('checklist-modules-container');
      container.innerHTML = '';

      checklistData.forEach(group => {
        const modDiv = document.createElement('div');
        modDiv.className = 'module-section';
        
        let itemsHtml = '';
        group.items.forEach(item => {
          const isChecked = checkedStates[item.id] ? 'checked' : '';
          itemsHtml += `
            <div class="check-item" onclick="toggleCheck('${item.id}')">
              <input type="checkbox" id="${item.id}" ${isChecked} onclick="event.stopPropagation(); calcularProgreso();">
              <div class="item-content">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                  <div class="item-title">${item.title}</div>
                  <div style="display:flex; align-items:center; gap:6px;">
                    <span class="badge-prio prio-${item.prio}">${item.prio}</span>
                    <button type="button" onclick="event.stopPropagation(); abrirGuiaTecnica('${item.id}')" style="background:rgba(56,189,248,0.15); border:1px solid #38bdf8; color:#38bdf8; padding:4px 10px; border-radius:6px; font-size:11px; font-weight:800; cursor:pointer;">🔍 ¿Cómo Auditar?</button>
                  </div>
                </div>
                <div class="item-desc">${item.desc}</div>
              </div>
            </div>
          `;
        });

        modDiv.innerHTML = `
          <div class="module-header">${group.modulo}</div>
          <div>${itemsHtml}</div>
        `;
        container.appendChild(modDiv);
      });

      calcularProgreso();
    }

    function toggleCheck(id) {
      const chk = document.getElementById(id);
      if (chk) {
        chk.checked = !chk.checked;
        calcularProgreso();
      }
    }

    function calcularProgreso() {
      let total = 0;
      let checked = 0;

      checklistData.forEach(g => {
        g.items.forEach(item => {
          total++;
          const chk = document.getElementById(item.id);
          if (chk && chk.checked) checked++;
        });
      });

      const pct = Math.round((checked / total) * 100);
      document.getElementById('porcentaje-num').innerText = pct + '% COMPLETADO';
      document.getElementById('progress-fill').style.width = pct + '%';
      
      autoGuardarDatos();
    }

    function abrirGuiaTecnica(id) {
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
    }

    function cerrarModalGuia() {
      document.getElementById('modal-item-guide').style.display = 'none';
    }

    function agregarFilaRAT() {
      const nombre = document.getElementById('rat_nombre_lista').value;
      const soporte = document.getElementById('rat_soporte').value;
      const datos = document.getElementById('rat_datos').value;
      const finalidad = document.getElementById('rat_finalidad').value;

      if (!nombre) { alert('Ingresa el nombre de la lista'); return; }

      ratItems.push({ nombre, soporte, datos, finalidad });
      document.getElementById('rat_nombre_lista').value = '';
      document.getElementById('rat_datos').value = '';
      document.getElementById('rat_finalidad').value = '';
      renderRatRecords();
    }

    function renderRatRecords() {
      const listDiv = document.getElementById('rat-records-list');
      if (ratItems.length === 0) {
        listDiv.innerHTML = '<em style="color:#64748b;">No hay registros de listas agregados todavía.</em>';
        return;
      }
      let html = '<ul style="margin:0; padding-left:16px;">';
      ratItems.forEach((r, idx) => {
        html += `<li><strong>${r.nombre}</strong> (${r.soporte}) - Datos: ${r.datos} | Uso: ${r.finalidad}</li>`;
      });
      html += '</ul>';
      listDiv.innerHTML = html;
    }

    function descargarCertificadoOficial() {
      const payload = {
        empresa: document.getElementById('emp_nombre').value || 'Empresa Cliente',
        rut: document.getElementById('emp_rut').value || 'N/A',
        responsable: document.getElementById('emp_responsable').value || 'N/A',
        pct: document.getElementById('porcentaje-num').innerText,
        correlativo: currentCorrelativo
      };

      fetch('/api/generar_certificado_cumplimiento_pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          const win = window.open('', '_blank');
          win.document.write(data.certificate_html);
          win.document.close();
        } else {
          alert('Error al emitir certificado: ' + data.message);
        }
      });
    }

    function autoGuardarDatos() {
      const checkedStates = {};
      checklistData.forEach(g => {
        g.items.forEach(item => {
          const chk = document.getElementById(item.id);
          if (chk) checkedStates[item.id] = chk.checked;
        });
      });

      auditStore[currentCorrelativo] = {
        correlativo: currentCorrelativo,
        empresa: document.getElementById('emp_nombre').value,
        rut: document.getElementById('emp_rut').value,
        responsable: document.getElementById('emp_responsable').value,
        email: document.getElementById('emp_email').value,
        phone: document.getElementById('emp_phone').value,
        direccion: document.getElementById('emp_direccion').value,
        checks: checkedStates,
        pct: document.getElementById('porcentaje-num').innerText,
        fecha: new Date().toLocaleString()
      };

      localStorage.setItem('quantus_audits_db', JSON.stringify(auditStore));
    }

    function cargarCorrelativo(num) {
      currentCorrelativo = num;
      document.getElementById('audit_correlativo').value = `#${currentCorrelativo}`;
      document.getElementById('correlativo-display').innerText = `CORRELATIVO #${currentCorrelativo}`;

      const data = auditStore[currentCorrelativo] || {};
      document.getElementById('emp_nombre').value = data.empresa || '';
      document.getElementById('emp_rut').value = data.rut || '';
      document.getElementById('emp_responsable').value = data.responsable || '';
      document.getElementById('emp_email').value = data.email || '';
      document.getElementById('emp_phone').value = data.phone || '';
      document.getElementById('emp_direccion').value = data.direccion || '';

      renderModules(data.checks || {});
    }

    function guardarAuditoriaActual() {
      autoGuardarDatos();
      alert(`✅ Auditoría #${currentCorrelativo} guardada con éxito en la base de datos privada maestro.`);
    }

    function siguienteCorrelativo() {
      autoGuardarDatos();
      currentCorrelativo++;
      cargarCorrelativo(currentCorrelativo);
    }

    function borrarAuditoriaActual() {
      if (confirm(`⚠️ ¿Estás seguro de borrar la ficha de auditoría #${currentCorrelativo}?`)) {
        delete auditStore[currentCorrelativo];
        localStorage.setItem('quantus_audits_db', JSON.stringify(auditStore));
        cargarCorrelativo(currentCorrelativo);
      }
    }

    window.onload = initChecklist;
  </script>
</body>
</html>
'''

with open(path, 'w', encoding='utf-8') as f:
    f.write(html_full_updated)

print("MAESTRO AUDIT ACTUALIZADO CON TODAS LAS CORRECCIONES LEGALES Y BOTÓN DE CERTIFICADO PDF")
