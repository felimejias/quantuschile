path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/index.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Borrar la vieja barra de navegación clara site-nav-wrap
pos_old_start = content.find('<header class="site-nav-wrap">')
pos_old_end = content.find('</header>', pos_old_start) + 9

if pos_old_start != -1 and pos_old_end != -1:
    content = content[:pos_old_start] + content[pos_old_end:]

# Reemplazar la barra de navegación duplicada por una sola barra de navegación limpia y fija arriba de la página
new_top_header = """  <header class="quantus-nav-bar" style="background: rgba(15, 23, 42, 0.98); border-bottom: 1px solid rgba(56, 189, 248, 0.25); padding: 12px 24px; position: sticky; top: 0; z-index: 99999; backdrop-filter: blur(12px); display: flex; justify-content: space-between; align-items: center;">
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

# Asegurar que esté inmediatamente después del <body>
pos_body = content.find('<body')
pos_body_close = content.find('>', pos_body) + 1

if pos_body != -1:
    # Quitar cualquier header previo
    content_no_headers = []
    in_header = False
    for line in content[pos_body_close:].split('\n'):
        if '<header' in line:
            in_header = True
            continue
        if in_header and '</header>' in line:
            in_header = False
            continue
        if not in_header:
            content_no_headers.append(line)
            
    final_content = content[:pos_body_close] + '\n' + new_top_header + '\n' + '\n'.join(content_no_headers)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    print("LIMPIEZA DE BARRA DUPLICADA EN INDEX.HTML COMPLETADA CON PROLIDAD")
