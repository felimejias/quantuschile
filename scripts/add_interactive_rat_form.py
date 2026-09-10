path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/maestro_compliance_audit.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Código del Formulario Dinámico RAT + Botón de Descarga Excel dentro del modal
interactive_rat_html = '''
    <!-- Formulario Dinámico RAT Interactivo y Descarga Excel -->
    <div id="interactive-rat-section" style="display:none; margin-top:16px; background:#1e293b; border:1px solid #38bdf8; border-radius:12px; padding:16px;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
        <h4 style="margin:0; color:#38bdf8; font-size:14px;">📝 Generador Directo de Formulario RAT (Opción Fácil)</h4>
        <a href="/static/Plantilla_Oficial_RAT_Ley21719_Quantus.csv" download style="background:#10b981; color:#0f172a; padding:6px 12px; border-radius:8px; font-weight:800; font-size:11px; text-decoration:none;">📥 Descargar Plantilla Excel RAT</a>
      </div>
      <p style="color:#94a3b8; font-size:12px; margin-bottom:12px;">Agrega aquí las listas o archivadores encontrados en la empresa para generar su inventario RAT al instante:</p>
      
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:10px;">
        <input type="text" id="rat_nombre_lista" placeholder="Nombre de la Lista (Ej: Excel Clientes 2026)" style="padding:8px; background:#0f172a; border:1px solid #475569; color:#fff; border-radius:6px; font-size:12px;">
        <select id="rat_soporte" style="padding:8px; background:#0f172a; border:1px solid #475569; color:#fff; border-radius:6px; font-size:12px;">
          <option value="Digital (Excel / Software / Web)">Digital (Excel / Software / Web)</option>
          <option value="Físico (Papel en Archivador)">Físico (Papel en Archivador)</option>
        </select>
        <input type="text" id="rat_datos" placeholder="Datos que guarda (Ej: Nombres, RUT, Teléfono)" style="padding:8px; background:#0f172a; border:1px solid #475569; color:#fff; border-radius:6px; font-size:12px;">
        <input type="text" id="rat_finalidad" placeholder="Para qué los usan (Ej: Para cobrar boletas)" style="padding:8px; background:#0f172a; border:1px solid #475569; color:#fff; border-radius:6px; font-size:12px;">
      </div>

      <button type="button" onclick="agregarFilaRAT()" style="width:100%; padding:8px; background:#38bdf8; color:#0f172a; font-weight:800; border:none; border-radius:6px; cursor:pointer; font-size:12px;">+ Agregar Registro al RAT de esta Empresa</button>
      
      <div id="rat-records-list" style="margin-top:12px; font-size:11px; color:#cbd5e1; max-height:120px; overflow-y:auto;"></div>
    </div>
'''

if 'interactive-rat-section' not in content:
    content = content.replace('<div id="modal-guide-work"', interactive_rat_html + '\n        <div id="modal-guide-work"')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print("FORMULARIO DINÁMICO RAT Y BOTÓN EXCEL INTEGRADO")
