import os

template_dir = "/Users/felipe/proyectos/quantuschile.cl/do/templates"

# 1. Ajuste de seguridad en la barra de acciones de maestro_compliance_audit.html
path_mae = os.path.join(template_dir, "maestro_compliance_audit.html")
with open(path_mae, "r", encoding="utf-8") as f:
    mae_content = f.read()

old_action_bar = '''    <div class="action-bar">
      <button type="button" class="btn-action btn-save" onclick="guardarAuditoriaActual()">💾 Guardar Auditoría</button>
      <button type="button" class="btn-action btn-cert" onclick="descargarCertificadoOficial()">🏆 Emitir Certificado PDF</button>
      <button type="button" class="btn-action btn-next" onclick="siguienteCorrelativo()">➡️ Crear Siguiente (#+1)</button>
      <button type="button" class="btn-action btn-delete" onclick="borrarAuditoriaActual()">🗑️ Borrar Ficha</button>
    </div>'''

new_action_bar = '''    <div class="action-bar" style="display:flex; justify-content:space-between; align-items:center; gap:12px; margin-top:24px; padding-bottom:40px; flex-wrap:wrap;">
      <div style="display:flex; gap:10px; flex:1; flex-wrap:wrap;">
        <button type="button" class="btn-action btn-save" onclick="guardarAuditoriaActual()">💾 Guardar Auditoría</button>
        <button type="button" class="btn-action btn-cert" onclick="descargarCertificadoOficial()">🏆 Emitir Certificado PDF</button>
        <button type="button" class="btn-action btn-next" onclick="siguienteCorrelativo()">➡️ Crear Siguiente (#+1)</button>
      </div>
      <div style="margin-left:auto;">
        <button type="button" class="btn-action btn-delete" onclick="borrarAuditoriaActual()" style="background:rgba(239,68,68,0.15); border:1px solid #ef4444; color:#fca5a5;">🗑️ Borrar Ficha</button>
      </div>
    </div>'''

if old_action_bar in mae_content:
    mae_content = mae_content.replace(old_action_bar, new_action_bar)
    with open(path_mae, "w", encoding="utf-8") as f:
        f.write(mae_content)
    print("SEPARACIÓN DE SEGURIDAD EN MAESTRO APLICADA CIENTÍFICAMENTE")

# 2. Despeje de focalización en checklist_ley21719.html
path_chk = os.path.join(template_dir, "checklist_ley21719.html")
with open(path_chk, "r", encoding="utf-8") as f:
    chk_content = f.read()

old_hero_sub = '''      <div style="margin-top:12px;">
        <a href="/static/ley21719_oficial.pdf" download class="btn-pdf-oficial" style="background:#0f172a; border:1px solid #38bdf8; color:#38bdf8;">
          📖 Descargar Texto Completo de la Ley N° 21.719 en PDF (Diario Oficial / BCN)
        </a>
      </div>'''

if old_hero_sub in chk_content:
    chk_content = chk_content.replace(old_hero_sub, '')
    with open(path_chk, "w", encoding="utf-8") as f:
        f.write(chk_content)
    print("DESPEJE VISUAL EN TEST DIAGNÓSTICO APLICADO")
