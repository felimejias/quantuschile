path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/maestro_compliance_audit.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Actualizar renderModules para incluir el botón de Guía "🔍 ¿Cómo Auditar?"
old_render = '''let itemsHtml = '';
        group.items.forEach(item => {
          const isChecked = checkedStates[item.id] ? 'checked' : '';
          itemsHtml += `
            <div class="check-item" onclick="toggleCheck('${item.id}')">
              <input type="checkbox" id="${item.id}" ${isChecked} onclick="event.stopPropagation(); calcularProgreso();">
              <div class="item-content">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                  <div class="item-title">${item.title}</div>
                  <span class="badge-prio prio-${item.prio}">${item.prio}</span>
                </div>
                <div class="item-desc">${item.desc}</div>
              </div>
            </div>
          `;
        });'''

new_render = '''let itemsHtml = '';
        group.items.forEach(item => {
          const isChecked = checkedStates[item.id] ? 'checked' : '';
          itemsHtml += `
            <div class="check-item" onclick="toggleCheck('${item.id}')">
              <input type="checkbox" id="${item.id}" ${isChecked} onclick="event.stopPropagation(); calcularProgreso();">
              <div class="item-content">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                  <div class="item-title">${item.title}</div>
                  <div>
                    <span class="badge-prio prio-${item.prio}">${item.prio}</span>
                    <button type="button" onclick="event.stopPropagation(); abrirGuiaTecnica('${item.id}')" style="background:rgba(56,189,248,0.15); border:1px solid #38bdf8; color:#38bdf8; padding:3px 8px; border-radius:6px; font-size:10px; font-weight:800; margin-left:6px; cursor:pointer;">🔍 ¿Cómo Auditar?</button>
                  </div>
                </div>
                <div class="item-desc">${item.desc}</div>
              </div>
            </div>
          `;
        });'''

if 'abrirGuiaTecnica' not in content:
    content = content.replace(old_render, new_render)
    
    # Agregar diccionario de guías técnicas en JS
    js_guides = '''
    const guiasTecnicas = {
      c1: { title: "1. Registro de Actividades de Tratamiento (RAT)", req: "La Ley 21.719 obliga a declarar el inventario de todas las bases de datos de clientes, empleados y proveedores.", work: "<strong>Pasos:</strong><br>1. Entrevistar al área de TI/Ventas.<br>2. Identificar Excels, ERPs, CRMs y Fichas físicas.<br>3. Redactar el RAT indicando Finalidad, Base Legal y Medidas de Seguridad.<br>4. Cargar la planilla en el panel Quantus." },
      c2: { title: "2. Designación de Responsable de Datos / DPO", req: "Debe existir un DPO nominado que responda ante denuncias y ante la Agencia de Protección de Datos.", work: "<strong>Pasos:</strong><br>1. Firmar el anexo de contrato designando al DPO interno o contrato externo Quantus.<br>2. Publicar el correo dpo@empresa.cl en la web." },
      c3: { title: "3. Evaluación de Impacto (PIA)", req: "Análisis preventivo de riesgos ante nuevos desarrollos o manejo de datos sensibles.", work: "<strong>Pasos:</strong><br>1. Aplicar la matriz de riesgos Quantus.<br>2. Determinar si manejan salud, menores o datos financieros.<br>3. Establecer controles de mitigación." },
      c4: { title: "4. Aceptación Expresa sin Pre-marcado", req: "Las casillas de consentimiento deben nacer desmarcadas por libertad de elección.", work: "<strong>Pasos:</strong><br>1. Revisar los formularios HTML del cliente.<br>2. Eliminar el atributo 'checked' de los checkboxes.<br>3. Vincular el enlace visible a la política de privacidad." },
      c5: { title: "5. Respaldo Criptográfico de Permisos (SHA-256)", req: "La empresa debe PROBAR empíricamente la aceptación de términos por cada cliente.", work: "<strong>Pasos:</strong><br>1. Instalar el script de consentimiento Quantus.<br>2. Registrar en la base de datos la IP, Fecha, Hora y Hash SHA-256 de la política aceptada." },
      c6: { title: "6. Portal de Atención Derechos ARCO (SLA 13 días)", req: "Canal obligatorio para responder solicitudes de borrado o acceso en máximo 13 días hábiles.", work: "<strong>Pasos:</strong><br>1. Pegar el widget quantus-arco-widget.js en el sitio web del cliente.<br>2. Probar el envío de un ticket de prueba y verificar el reloj de control de 13 días." },
      c7: { title: "7. Inventario y Etiquetado QR de Archivadores Físicos", req: "La Ley 21.719 aplica a ficheros físicos organizados en papel.", work: "<strong>Pasos:</strong><br>1. Clasificar archivadores físicos por año y tipo.<br>2. Imprimir etiquetas QR Quantus con fecha de vencimiento.<br>3. Pegar el QR en los lomos de los archivadores." },
      c8: { title: "8. Protocolo de Destrucción Física Registrada", req: "Destrucción de documentos en papel sin botarlos a la basura común.", work: "<strong>Pasos:</strong><br>1. Implementar trituradora de papel corte cruzado DIN 66399 P-4.<br>2. Emitir el Acta Digital de Destrucción en Quantus cada vez que se tritura un archivador." },
      c9: { title: "9. Control de Acceso Físico a Bodegas", req: "Evitar que empleados no autorizados accedan a carpetas con datos de clientes.", work: "<strong>Pasos:</strong><br>1. Colocar chapa con llave o control de tarjeta en la sala de archivos físicos.<br>2. Llevar bitácora de quién entra y sale de la bodega." },
      c10: { title: "10. Cifrado de Datos (HTTPS / AES-256)", req: "Cumplimiento de Ley 21.663 de Ciberseguridad para proteger la integridad.", work: "<strong>Pasos:</strong><br>1. Forzar SSL (HTTPS) en la web.<br>2. Habilitar cifrado AES-256 en reposo para bases de datos SQL." },
      c11: { title: "11. Protocolo de Notificación de Brechas (3 horas)", req: "Avisar a las autoridades en menos de 3 horas si sufren un hackeo o filtración.", work: "<strong>Pasos:</strong><br>1. Entregar el Manual de Crisis de Ciberseguridad.<br>2. Probar el botón de pánico de notificación ANCI/Agencia." },
      c12: { title: "12. Control de Accesos por Roles (RBAC)", req: "Evitar que vendedores vean datos financieros o contables (Ley 21.459).", work: "<strong>Pasos:</strong><br>1. Configurar perfiles en su software (Administrador, Ejecutivo, Consulta).<br>2. Desactivar usuarios de exfuncionarios." },
      c13: { title: "13. Motor de Purga Inmediata tras Cancelación", req: "Borrar de inmediato al cliente de listas de marketing al darse de baja.", work: "<strong>Pasos:</strong><br>1. Conectar la API de Quantus al botón de cancelaciones.<br>2. Verificar que el bot de WhatsApp deje de enviarle publicidad al instante." },
      c14: { title: "14. Bóveda de Bloqueo Legal Exclusivo (6 años SII)", req: "Aislar boletas/facturas por 6 años sin usarlas para marketing.", work: "<strong>Pasos:</strong><br>1. Configurar la carpeta de custodia aislada.<br>2. Mover registros cancelados impidiendo su uso comercial." },
      c15: { title: "15. Destrucción Definitiva Automática a los 6 Años", req: "Cumplimiento del plazo máximo de retención y supresión permanente.", work: "<strong>Pasos:</strong><br>1. Programar el script boveda_purger_cron.py.<br>2. Probar el borrado físico e irreversible en el servidor cumplidos los 2.190 días." }
    };

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
'''
    pos = content.find('let currentCorrelativo = 1;')
    content = content[:pos] + js_guides + '\n\n' + content[pos:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print("JS DE GUÍA TÉCNICA DETALLADA INTEGRADO CON ÉXITO")
