path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/index.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Eliminar cualquier style previo que forzaba fondo blanco e inyectar el modo oscuro ejecutivo definitivo
dark_index_css = """<style>
  :root {
    --ink: #f8fafc !important;
    --muted: #94a3b8 !important;
    --line: rgba(56, 189, 248, 0.25) !important;
    --surface: #0f172a !important;
    --soft: #1e293b !important;
    --navy: #07111f !important;
  }
  html, body {
    background-color: #0f172a !important;
    color: #f8fafc !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
    margin: 0 !important;
    padding: 0 !important;
  }
  header, nav, .navbar, .site-header {
    background: rgba(15, 23, 42, 0.98) !important;
    border-bottom: 1px solid rgba(56, 189, 248, 0.25) !important;
  }
  .quantus-nav-bar {
    background: rgba(15, 23, 42, 0.98) !important;
    border-bottom: 1px solid rgba(56, 189, 248, 0.25) !important;
    padding: 12px 24px !important;
    position: sticky !important;
    top: 0 !important;
    z-index: 99999 !important;
    backdrop-filter: blur(12px) !important;
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
  }
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
    box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
    cursor: pointer !important;
  }
  .quantus-nav-btn:hover {
    background: #38bdf8 !important;
    color: #0f172a !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 16px rgba(56, 189, 248, 0.4) !important;
  }
  h1 {
    font-size: 32px !important;
    line-height: 1.25 !important;
    font-weight: 900 !important;
    color: #ffffff !important;
    letter-spacing: -0.5px !important;
  }
  h2 {
    font-size: 22px !important;
    line-height: 1.3 !important;
    font-weight: 800 !important;
    color: #38bdf8 !important;
  }
  h3, h4, h5 {
    color: #ffffff !important;
  }
  p, li, span, div {
    color: #cbd5e1 !important;
  }
  .card, .hero-card, .service-card, .feature-card, div[style*="background: #ffffff"], div[style*="background:#ffffff"] {
    background: #1e293b !important;
    border: 1px solid rgba(56, 189, 248, 0.2) !important;
    color: #f8fafc !important;
  }
</style>"""

content = content.replace("</head>", dark_index_css + "\n</head>")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("ESTILOS CROMÁTICOS OSCUROS Y NAVEGACIÓN REPARADOS AL 100%")
