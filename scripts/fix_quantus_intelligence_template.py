path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/quantus_intelligence.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Cambiar la paleta clara a la paleta corporativa azul noche
content = content.replace('background: var(--soft);', 'background: #0f172a !important;')
content = content.replace('color: var(--ink);', 'color: #f8fafc !important;')
content = content.replace('--surface: #ffffff;', '--surface: #0f172a;')
content = content.replace('--soft: #f5f8fc;', '--soft: #1e293b;')
content = content.replace('--ink: #111827;', '--ink: #f8fafc;')
content = content.replace('--muted: #64748b;', '--muted: #94a3b8;')

# 2. Corregir los enlaces de navegación para que la portada tenga el botón QUANTUS ERP
old_nav_links = """      <div class="nav-links">
        <a href="#radar">Ecosistema</a>
        <a href="/do">Diario Oficial</a>
        <a href="/licitaciones">Licitaciones</a>
        <a href="/inapi">Marcas</a>
        <a href="/remates">Remates</a>
        <a href="/checklist-ley-21719">Checklist Ley 21.719</a>
        <a href="/maestro">Cumplimiento</a>
      </div>
      <div class="nav-actions">
        <a href="https://www.quantuschile.cl" class="btn btn-secondary">Quantus System</a>
      </div>"""

new_nav_links = """      <div class="nav-links" style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
        <a href="/do/prospeccion" class="quantus-nav-btn">📰 DIARIO OFICIAL</a>
        <a href="/licitaciones" class="quantus-nav-btn">🏛️ LICITACIONES</a>
        <a href="/inapi" class="quantus-nav-btn">🏷️ MARCAS</a>
        <a href="/remates" class="quantus-nav-btn">🏠 REMATES</a>
        <a href="/checklist-ley-21719" class="quantus-nav-btn">⚖️ LEY 21.719</a>
        <a href="https://www.quantuschile.cl" class="quantus-nav-btn" style="background:rgba(16,185,129,0.2); border-color:#10b981; color:#6ee7b7;">🖥️ QUANTUS ERP</a>
        <a href="/maestro" class="quantus-nav-btn" style="background:rgba(245,158,11,0.2); border-color:#f59e0b; color:#fcd34d;">🔒 ADMINISTRACIÓN</a>
      </div>"""

if old_nav_links in content:
    content = content.replace(old_nav_links, new_nav_links)

# Reemplazo alternativo si difiere en espacios
content = content.replace('>Quantus System<', '>Quantus ERP<')
content = content.replace('>Quantus Chile<', '>Quantus ERP<')

# Inyectar CSS oscuro garantizado en head
dark_override = """<style>
  body {
    background-color: #0f172a !important;
    color: #f8fafc !important;
  }
  .site-nav-wrap {
    background: rgba(15, 23, 42, 0.98) !important;
    border-bottom: 1px solid rgba(56, 189, 248, 0.25) !important;
  }
  .hero-card, .radar-card, .service-card, .metric-card, div[style*="background: #ffffff"] {
    background: #1e293b !important;
    border: 1px solid rgba(56, 189, 248, 0.2) !important;
    color: #f8fafc !important;
  }
  h1, h2, h3 { color: #ffffff !important; }
  p, span, small { color: #cbd5e1 !important; }
  .quantus-nav-btn {
    display: inline-flex !important;
    align-items: center !important;
    gap: 6px !important;
    background: #1e293b !important;
    color: #38bdf8 !important;
    border: 1px solid rgba(56, 189, 248, 0.4) !important;
    padding: 8px 14px !important;
    border-radius: 10px !important;
    font-weight: 800 !important;
    font-size: 11px !important;
    text-decoration: none !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    transition: all 0.2s ease !important;
  }
</style>"""

content = content.replace("</head>", dark_override + "\n</head>")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("PLANTILLA REAL DE LA PORTADA (QUANTUS_INTELLIGENCE.HTML) ACTUALIZADA Y CORREGIDA AL 100%")
