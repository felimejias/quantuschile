path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/maestro_compliance_audit.html'

html_code = '''<!DOCTYPE html>
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
    
    .action-bar { display: flex; gap: 12px; margin-top: 24px; padding-bottom: 40px; }
    .btn-action { flex: 1; padding: 14px; border-radius: 12px; font-weight: 800; font-size: 14px; text-align: center; border: none; cursor: pointer; text-transform: uppercase; letter-spacing: 0.5px; }
    .btn-save { background: #10b981; color: #0f172a; }
    .btn-next { background: #38bdf8; color: #0f172a; }
    .btn-delete { background: rgba(239,68,68,0.2); color: #fca5a5; border: 1px solid rgba(239,68,68,0.4); }

    /* Modal Overlay */
    .custom-modal-overlay { display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(6, 16, 31, 0.88); backdrop-filter: blur(8px); z-index: 999999; align-items: center; justify-content: center; padding: 16px; box-sizing: border-box; }
    .custom-modal-card { background: #0f172a; border: 1px solid #38bdf8; padding: 24px; border-radius: 16px; max-width: 600px; width: 100%; box-shadow: 0 20px 40px rgba(0,0,0,0.8); }
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
        <h2 style="margin:0; font-size:18px; color:#fff;">📋 Ficha de Auditoría de Cumplimiento Ley 21.719</h2>
        <span id="correlativo-display" style="background:#38bdf8; color:#0f172a; padding:4px 12px; border-radius:8px; font-weight:900; font-size:13px;">CORRELATIVO #1</span>
      </div>

      <div class="form-grid">
        <div class="form-group">
          <label>N° Registro Correlativo Interno</label>
          <input type="text" id="audit_correlativo" readonly style="background:#1e293b; color:#38bdf8; font-weight:800;">
        </div>
        <div class="form-group">
          <label>Nombre de la Empresa / Razón Social *</label>
          <input type="text" id="emp_nombre" placeholder="Ej: Clínica Santa María / Banco de Chile" oninput="autoGuardarDatos()">
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
      <button type="button" class="btn-action btn-next" onclick="siguienteCorrelativo()">➡️ Crear Siguiente (#+1)</button>
      <button type="button" class="btn-action btn-delete" onclick="borrarAuditoriaActual()">🗑️ Borrar Ficha</button>
    </div>

  </main>

  <!-- Modal Explicativo Guía Técnica -->
  <div id="modal-item-guide" class="custom-modal-overlay">
    <div class="custom-modal-card">
      <button type="button" onclick="cerrarModalGuia()" style="float:right; background:none; border:none; color:#94a3b8; font-size:24px; cursor:pointer;">&times;</button>
      <span style="background:rgba(56,189,248,0.2); color:#38bdf8; padding:4px 10px; border-radius:999px; font-size:11px; font-weight:800;">GUÍA DE EJECUCIÓN Y REMEDIACIÓN TÉCNICA</span>
      <h3 id="modal-guide-title" style="font-size:18px; color:#fff; margin-top:10px; margin-bottom:12px;"></h3>
      
      <div style="background:#1e293b; border-left:4px solid #38bdf8; padding:14px; border-radius:8px; margin-bottom:16px;">
        <h4 style="margin:0 0 6px 0; color:#38bdf8; font-size:13px; text-transform:uppercase;">⚖️ Requisito Exigido por Ley N° 21.719:</h4>
        <p id="modal-guide-req" style="margin:0; font-size:13px; color:#cbd5e1; line-height:1.5;"></p>
      </div>

      <div style="background:#1e293b; border-left:4px solid #10b981; padding:14px; border-radius:8px;">
        <h4 style="margin:0 0 6px 0; color:#10b981; font-size:13px; text-transform:uppercase;">🛠️ Trabajo Técnico / Auditoría a Realizar en la Empresa:</h4>
        <div id="modal-guide-work" style="font-size:13px; color:#cbd5e1; line-height:1.5;"></div>
      </div>

      <button type="button" onclick="cerrarModalGuia()" style="width:100%; margin-top:20px; padding:12px; background:#38bdf8; color:#0f172a; font-weight:900; border:none; border-radius:10px; cursor:pointer;">Entendido — Volver al Checklist</button>
    </div>
  </div>

  <script>
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
          { id: "c6", prio: "alta", title: "6. Portal de Atención Derechos ARCO (SLA 13 días)", desc: "Formulario web exclusivo para tramitar solicitudes de borrado, acceso, rectificación u oposición." }
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
      }
    ];

    const guiasTecnicas = {
      c1: { title: "1. Registro de Actividades de Tratamiento (RAT)", req: "La Ley 21.719 obliga a declarar el inventario de todas las bases de datos de clientes, empleados y proveedores.", work: "<strong>Pasos de Ejecución:</strong><br>1. Entrevistar al área de TI/Ventas.<br>2. Identificar Excels, ERPs, CRMs y Fichas físicas.<br>3. Redactar el RAT indicando Finalidad, Base Legal y Medidas de Seguridad.<br>4. Cargar la planilla en el panel Quantus." },
      c2: { title: "2. Designación de Responsable de Datos / DPO", req: "Debe existir un DPO nominado que responda ante denuncias y ante la Agencia de Protección de Datos.", work: "<strong>Pasos de Ejecución:</strong><br>1. Firmar el anexo de contrato designando al DPO interno o contrato externo Quantus.<br>2. Publicar el correo dpo@empresa.cl en la web." },
      c3: { title: "3. Evaluación de Impacto (PIA)", req: "Análisis preventivo de riesgos ante nuevos desarrollos o manejo de datos sensibles.", work: "<strong>Pasos de Ejecución:</strong><br>1. Aplicar la matriz de riesgos Quantus.<br>2. Determinar si manejan salud, menores o datos financieros.<br>3. Establecer controles de mitigación." },
      c4: { title: "4. Aceptación Expresa sin Pre-marcado", req: "Las casillas de consentimiento deben nacer desmarcadas por libertad de elección.", work: "<strong>Pasos de Ejecución:</strong><br>1. Revisar los formularios HTML del cliente.<br>2. Eliminar el atributo 'checked' de los checkboxes.<br>3. Vincular el enlace visible a la política de privacidad." },
      c5: { title: "5. Respaldo Criptográfico de Permisos (SHA-256)", req: "La empresa debe PROBAR empíricamente la aceptación de términos por cada cliente.", work: "<strong>Pasos de Ejecución:</strong><br>1. Instalar el script de consentimiento Quantus.<br>2. Registrar en la base de datos la IP, Fecha, Hora y Hash SHA-256 de la política aceptada." },
      c6: { title: "6. Portal de Atención Derechos ARCO (SLA 13 días)", req: "Canal obligatorio para responder solicitudes de borrado o acceso en máximo 13 días hábiles.", work: "<strong>Pasos de Ejecución:</strong><br>1. Pegar el widget quantus-arco-widget.js en el sitio web del cliente.<br>2. Probar el envío de un ticket de prueba y verificar el reloj de control de 13 días." },
      c7: { title: "7. Inventario y Etiquetado QR de Archivadores Físicos", req: "La Ley 21.719 aplica a ficheros físicos organizados en papel.", work: "<strong>Pasos de Ejecución:</strong><br>1. Clasificar archivadores físicos por año y tipo.<br>2. Imprimir etiquetas QR Quantus con fecha de vencimiento.<br>3. Pegar el QR en los lomos de los archivadores." },
      c8: { title: "8. Protocolo de Destrucción Física Registrada", req: "Destrucción de documentos en papel sin botarlos a la basura común.", work: "<strong>Pasos de Ejecución:</strong><br>1. Implementar trituradora de papel corte cruzado DIN 66399 P-4.<br>2. Emitir el Acta Digital de Destrucción en Quantus cada vez que se tritura un archivador." },
      c9: { title: "9. Control de Acceso Físico a Bodegas", req: "Evitar que empleados no autorizados accedan a carpetas con datos de clientes.", work: "<strong>Pasos de Ejecución:</strong><br>1. Colocar chapa con llave o control de tarjeta en la sala de archivos físicos.<br>2. Llevar bitácora de quién entra y sale de la bodega." },
      c10: { title: "10. Cifrado de Datos (HTTPS / AES-256)", req: "Cumplimiento de Ley 21.663 de Ciberseguridad para proteger la integridad.", work: "<strong>Pasos de Ejecución:</strong><br>1. Forzar SSL (HTTPS) en la web.<br>2. Habilitar cifrado AES-256 en reposo para bases de datos SQL." },
      c11: { title: "11. Protocolo de Notificación de Brechas (3 horas)", req: "Avisar a las autoridades en menos de 3 horas si sufren un hackeo o filtración.", work: "<strong>Pasos de Ejecución:</strong><br>1. Entregar el Manual de Crisis de Ciberseguridad.<br>2. Probar el botón de pánico de notificación ANCI/Agencia." },
      c12: { title: "12. Control de Accesos por Roles (RBAC)", req: "Evitar que vendedores vean datos financieros o contables (Ley 21.459).", work: "<strong>Pasos de Ejecución:</strong><br>1. Configurar perfiles en su software (Administrador, Ejecutivo, Consulta).<br>2. Desactivar usuarios de exfuncionarios." },
      c13: { title: "13. Motor de Purga Inmediata tras Cancelación", req: "Borrar de inmediato al cliente de listas de marketing al darse de baja.", work: "<strong>Pasos de Ejecución:</strong><br>1. Conectar la API de Quantus al botón de cancelaciones.<br>2. Verificar que el bot de WhatsApp deje de enviarle publicidad al instante." },
      c14: { title: "14. Bóveda de Bloqueo Legal Exclusivo (6 años SII)", req: "Aislar boletas/facturas por 6 años sin usarlas para marketing.", work: "<strong>Pasos de Ejecución:</strong><br>1. Configurar la carpeta de custodia aislada.<br>2. Mover registros cancelados impidiendo su uso comercial." },
      c15: { title: "15. Destrucción Definitiva Automática a los 6 Años", req: "Cumplimiento del plazo máximo de retención y supresión permanente.", work: "<strong>Pasos de Ejecución:</strong><br>1. Programar el script boveda_purger_cron.py.<br>2. Probar el borrado físico e irreversible en el servidor cumplidos los 2.190 días." }
    };

    let currentCorrelativo = 1;
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
        document.getElementById('modal-guide-work').innerHTML = g.work;
        document.getElementById('modal-item-guide').style.display = 'flex';
      }
    }

    function cerrarModalGuia() {
      document.getElementById('modal-item-guide').style.display = 'none';
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
    f.write(html_code)

print("MAESTRO AUDIT HTML REWRITTEN AND CLEANED PERFECTLY")
