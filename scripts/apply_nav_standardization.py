import os

template_dir = "/Users/felipe/proyectos/quantuschile.cl/do/templates"

# Modificar 1: checklist_ley21719.html
path_chk = os.path.join(template_dir, "checklist_ley21719.html")
with open(path_chk, "r", encoding="utf-8") as f:
    chk_content = f.read()

nav_css = """
  <style>
    /* Estilo Estándar Premium Quantus - Navegación y Botones */
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

new_chk_header = """  <header class="quantus-nav-bar">
    <div style="display:flex; align-items:center; gap:12px;">
      <a href="/" class="quantus-nav-btn">⬅️ VOLVER AL INICIO</a>
      <img src="{{ url_for('static', filename='quantus-logo-clean.png') }}" alt="Quantus" style="height:26px;">
      <span style="font-weight:900; color:#fff; font-size:15px;">QUANTUS <span style="color:#38bdf8;">COMPLIANCE</span></span>
    </div>
    
    <div style="display:flex; align-items:center; gap:10px;">
      <a href="/ley-21719/guia" class="quantus-nav-btn">📖 GUÍA COMPLETA LEY</a>
      <a href="/static/ley21719_oficial.pdf" download class="quantus-nav-btn quantus-nav-btn-pdf">
        📄 PDF LEY N° 21.719 (56 PÁGS BCN)
      </a>
    </div>
  </header>"""

# Inyectar CSS y reemplazar Header en checklist_ley21719.html
chk_content = chk_content.replace('</head>', nav_css + '\n</head>')
pos_h_start = chk_content.find('<header')
pos_h_end = chk_content.find('</header>') + 9
if pos_h_start != -1 and pos_h_end != -1:
    chk_content = chk_content[:pos_h_start] + new_chk_header + chk_content[pos_h_end:]
    with open(path_chk, "w", encoding="utf-8") as f:
        f.write(chk_content)

# Modificar 2: maestro_compliance_audit.html
path_mae = os.path.join(template_dir, "maestro_compliance_audit.html")
with open(path_mae, "r", encoding="utf-8") as f:
    mae_content = f.read()

new_mae_header = """  <header class="quantus-nav-bar">
    <div style="display:flex; align-items:center; gap:12px;">
      <a href="/maestro" class="quantus-nav-btn">⬅️ VOLVER AL MAESTRO</a>
      <img src="{{ url_for('static', filename='quantus-logo-clean.png') }}" alt="Quantus" style="height:26px;">
      <span style="font-weight:900; color:#fff; font-size:15px;">QUANTUS <span style="color:#38bdf8;">AUDIT PRIVATE</span></span>
    </div>
    
    <div style="display:flex; align-items:center; gap:10px;">
      <a href="/checklist-ley-21719" class="quantus-nav-btn">📋 VER TEST PÚBLICO</a>
      <a href="/static/ley21719_oficial.pdf" download class="quantus-nav-btn quantus-nav-btn-pdf">
        📄 PDF LEY N° 21.719 (56 PÁGS BCN)
      </a>
    </div>
  </header>"""

mae_content = mae_content.replace('</head>', nav_css + '\n</head>')
pos_m_start = mae_content.find('<header')
pos_m_end = mae_content.find('</header>') + 9
if pos_m_start != -1 and pos_m_end != -1:
    mae_content = mae_content[:pos_m_start] + new_mae_header + mae_content[pos_m_end:]
    with open(path_mae, "w", encoding="utf-8") as f:
        f.write(mae_content)

# Modificar 3: ley_21719_guia.html
path_guia = os.path.join(template_dir, "ley_21719_guia.html")
if os.path.exists(path_guia):
    with open(path_guia, "r", encoding="utf-8") as f:
        guia_content = f.read()
    
    new_guia_header = """  <header class="quantus-nav-bar">
    <div style="display:flex; align-items:center; gap:12px;">
      <a href="/checklist-ley-21719" class="quantus-nav-btn">⬅️ VOLVER AL TEST DIAGNÓSTICO</a>
      <img src="{{ url_for('static', filename='quantus-logo-clean.png') }}" alt="Quantus" style="height:26px;">
      <span style="font-weight:900; color:#fff; font-size:15px;">QUANTUS <span style="color:#38bdf8;">COMPLIANCE GUÍA</span></span>
    </div>
    
    <a href="/static/ley21719_oficial.pdf" download class="quantus-nav-btn quantus-nav-btn-pdf">
      📄 PDF LEY N° 21.719 (56 PÁGS BCN)
    </a>
  </header>"""

    guia_content = guia_content.replace('</head>', nav_css + '\n</head>')
    pos_g_start = guia_content.find('<header')
    pos_g_end = guia_content.find('</header>') + 9
    if pos_g_start != -1 and pos_g_end != -1:
        guia_content = guia_content[:pos_g_start] + new_guia_header + guia_content[pos_g_end:]
        with open(path_guia, "w", encoding="utf-8") as f:
            f.write(guia_content)

# Modificar 4: licitaciones.html
path_lic = os.path.join(template_dir, "licitaciones.html")
if os.path.exists(path_lic):
    with open(path_lic, "r", encoding="utf-8") as f:
        lic_content = f.read()
    
    new_lic_header = """  <header class="quantus-nav-bar">
    <div style="display:flex; align-items:center; gap:12px;">
      <a href="/" class="quantus-nav-btn">⬅️ VOLVER AL INICIO</a>
      <img src="{{ url_for('static', filename='quantus-logo-clean.png') }}" alt="Quantus" style="height:26px;">
      <span style="font-weight:900; color:#fff; font-size:15px;">QUANTUS <span style="color:#38bdf8;">LICITACIONES</span></span>
    </div>
    
    <div style="display:flex; align-items:center; gap:10px;">
      <a href="/prospeccion-do" class="quantus-nav-btn">📰 DIARIO OFICIAL</a>
      <a href="/checklist-ley-21719" class="quantus-nav-btn">⚖️ LEY 21.719</a>
    </div>
  </header>"""

    lic_content = lic_content.replace('</head>', nav_css + '\n</head>')
    pos_l_start = lic_content.find('<header')
    pos_l_end = lic_content.find('</header>') + 9
    if pos_l_start != -1 and pos_l_end != -1:
        lic_content = lic_content[:pos_l_start] + new_lic_header + lic_content[pos_l_end:]
        with open(path_lic, "w", encoding="utf-8") as f:
            f.write(lic_content)

print("ESTANDARIZACIÓN TOTAL DE NAVEGACIÓN Y BOTONES DE VOLVER FINALIZADA CON ÉXITO")
