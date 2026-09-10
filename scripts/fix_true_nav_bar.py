path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/quantus_intelligence.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar la barra de navegación original en quantus_intelligence.html por los botones estandarizados
old_nav_snippet = """    <nav class="site-nav" aria-label="Navegacion principal">
      <a href="/" class="brand">
        <img src="/static/logo-quantus-official-emblem-small.png" alt="Emblema Quantus Chile SpA">
        <span class="brand-text">Quantus Chile SpA<small>Intelligence Business</small></span>
      </a>
      <div class="nav-links">
        <a href="#radar">Ecosistema</a>
        <a href="/do">Diario Oficial</a>
        <a href="/licitaciones">Licitaciones</a>
        <a href="/inapi">Marcas</a>
        <a href="/remates">Remates</a>
        <a href="/checklist-ley-21719">Checklist Ley 21.719</a>
        <a href="#cumplimiento">Cumplimiento</a>
      </div>
      <a href="/admin" class="admin-link">Administracion</a>
    </nav>"""

new_nav_snippet = """    <nav class="site-nav" aria-label="Navegacion principal" style="display:flex; justify-content:space-between; align-items:center; width:100%; gap:12px;">
      <a href="/" class="brand" style="display:flex; align-items:center; gap:8px;">
        <img src="/static/quantus-logo-clean.png" alt="Quantus Chile SpA" style="height:28px;">
        <span class="brand-text" style="font-weight:900; color:#fff;">QUANTUS <span style="color:#38bdf8;">CHILE SpA</span></span>
      </a>
      <div class="nav-links" style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
        <a href="/do/prospeccion" class="quantus-nav-btn">📰 DIARIO OFICIAL</a>
        <a href="/licitaciones" class="quantus-nav-btn">🏛️ LICITACIONES</a>
        <a href="/inapi" class="quantus-nav-btn">🏷️ MARCAS</a>
        <a href="/remates" class="quantus-nav-btn">🏠 REMATES</a>
        <a href="/checklist-ley-21719" class="quantus-nav-btn">⚖️ LEY 21.719</a>
        <a href="https://www.quantuschile.cl" class="quantus-nav-btn" style="background:rgba(16,185,129,0.2); border-color:#10b981; color:#6ee7b7;">🖥️ QUANTUS ERP</a>
        <a href="/maestro" class="quantus-nav-btn" style="background:rgba(245,158,11,0.2); border-color:#f59e0b; color:#fcd34d;">🔒 ADMINISTRACIÓN</a>
      </div>
    </nav>"""

if old_nav_snippet in content:
    content = content.replace(old_nav_snippet, new_nav_snippet)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("NAVEGACIÓN DE LA PORTADA VERDADERA QUANTUS_INTELLIGENCE.HTML ACTUALIZADA AL 100%")
else:
    print("No se encontró el snippet exacto")
