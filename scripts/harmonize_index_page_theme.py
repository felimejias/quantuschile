path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/index.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# CSS Estándar Noche Corporativa Premium para index.html sin fatiga visual lumínica
dark_home_css = """
  <style>
    :root {
      --bg-dark: #0f172a;
      --card-bg: #1e293b;
      --accent-blue: #38bdf8;
      --accent-green: #10b981;
      --accent-red: #ef4444;
      --accent-orange: #f59e0b;
    }
    body {
      background-color: #0f172a !important;
      color: #f8fafc !important;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
    }
    header, .navbar, .header-bar {
      background: rgba(15, 23, 42, 0.95) !important;
      border-bottom: 1px solid rgba(56, 189, 248, 0.25) !important;
      backdrop-filter: blur(12px) !important;
    }
    .hero-section, .hero, .banner {
      background: radial-gradient(circle at top, rgba(56,189,248,0.15), transparent 70%) !important;
      color: #ffffff !important;
    }
    .card, .feature-box, .service-card {
      background: #1e293b !important;
      border: 1px solid rgba(56, 189, 248, 0.2) !important;
      color: #f8fafc !important;
      box-shadow: 0 10px 25px rgba(0,0,0,0.5) !important;
    }
    h1, h2, h3, h4, h5, h6 {
      color: #ffffff !important;
    }
    p, span, li {
      color: #cbd5e1 !important;
    }
    .quantus-nav-bar {
      background: rgba(15, 23, 42, 0.95) !important;
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
    .quantus-nav-btn-pdf {
      background: linear-gradient(90deg, #ef4444, #dc2626) !important;
      color: #ffffff !important;
      border: 1px solid rgba(255,255,255,0.3) !important;
    }
    .quantus-nav-btn-pdf:hover {
      background: #f87171 !important;
      color: #ffffff !important;
    }
  </style>
"""

content = content.replace('</head>', dark_home_css + '\n</head>')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("PÁGINA DE INICIO (INDEX.HTML) HARMONIZADA A LA PALETA AZUL NOCHE CORPORATIVA (#0F172A)")
