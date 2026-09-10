path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/maestro_compliance_audit.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

modal_html = '''
    <!-- Modal Explicativo de Ejecución Técnica por Cada Punto -->
    <div id="modal-item-guide" class="modal-overlay" style="display:none;">
      <div class="modal-card" style="max-width:650px; background:#0f172a; border:1px solid #38bdf8; padding:24px; border-radius:16px; color:#f8fafc;">
        <button type="button" class="modal-close-btn" onclick="cerrarModalGuia()" style="float:right; background:none; border:none; color:#94a3b8; font-size:24px; cursor:pointer;">&times;</button>
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
'''

# Reemplazar o insertar antes del script en maestro_compliance_audit.html
if 'modal-item-guide' not in content:
    content = content.replace('<!-- Botonera de Acción -->', modal_html + '\n    <!-- Botonera de Acción -->')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print("MODAL DE GUÍA TÉCNICA INCLUIDO EN EL CHECKLIST MAESTRO")
