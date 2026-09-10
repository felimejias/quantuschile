path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/index.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar variables CSS en root de index.html para forzar el tema oscuro azul noche
content = content.replace('--surface: #ffffff;', '--surface: #0f172a;')
content = content.replace('--soft: #f5f8fc;', '--soft: #1e293b;')
content = content.replace('--ink: #111827;', '--ink: #f8fafc;')
content = content.replace('--muted: #64748b;', '--muted: #94a3b8;')

# Reemplazar el contenedor blanco de navegación por la barra oscura unificada
old_nav = content[content.find('<header'):content.find('</header>') + 9]

new_nav = """<header class="quantus-nav-bar" style="background: #0f172a; border-bottom: 1px solid rgba(56, 189, 248, 0.25); padding: 12px 24px; position: sticky; top: 0; z-index: 99999; display: flex; justify-content: space-between; align-items: center;">
    <div style="display:flex; align-items:center; gap:12px;">
      <a href="/" style="display:flex; align-items:center; gap:8px; text-decoration:none;">
        <img src="/static/quantus-logo-clean.png" alt="Quantus Chile" style="height:28px;">
        <span style="font-weight:900; color:#fff; font-size:16px;">QUANTUS <span style="color:#38bdf8;">CHILE SpA</span></span>
      </a>
    </div>
    
    <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
      <a href="/do/prospeccion" class="quantus-nav-btn">📰 DIARIO OFICIAL</a>
      <a href="/licitaciones" class="quantus-nav-btn">🏛️ LICITACIONES</a>
      <a href="/inapi" class="quantus-nav-btn">🏷️ MARCAS</a>
      <a href="/remates" class="quantus-nav-btn">🏠 REMATES</a>
      <a href="/checklist-ley-21719" class="quantus-nav-btn">⚖️ LEY 21.719</a>
      <a href="https://www.quantuschile.cl" class="quantus-nav-btn" style="background:rgba(16,185,129,0.2); border-color:#10b981; color:#6ee7b7;">🖥️ QUANTUS ERP</a>
      <a href="/maestro" class="quantus-nav-btn" style="background:rgba(245,158,11,0.2); border-color:#f59e0b; color:#fcd34d;">🔒 ADMINISTRACIÓN</a>
    </div>
  </header>"""

if old_nav:
    content = content.replace(old_nav, new_nav)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("PORTADA CORREGIDA: NAVEGACIÓN UNIFICADA Y FONDO AZUL NOCHE APLICADO AL 100%")
