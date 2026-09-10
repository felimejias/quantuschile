path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/index.html'

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Limpieza quirúrgica de duplicados en index.html
cleaned_lines = []
in_duplicate = False

for line in lines:
    if '<style id="quantus-clean-dark-theme">' in line:
        in_duplicate = True
        continue
    if in_duplicate and '</style>' in line:
        in_duplicate = False
        continue
    if not in_duplicate:
        cleaned_lines.append(line)

content = "".join(cleaned_lines)

# Estandarización limpia del bloque style de index.html
style_clean = """  <style>
    :root {
      --ink: #f8fafc;
      --muted: #94a3b8;
      --line: rgba(56, 189, 248, 0.25);
      --surface: #0f172a;
      --soft: #1e293b;
      --cyan: #0ea5e9;
      --emerald: #10b981;
      --violet: #7c3aed;
      --amber: #f59e0b;
      --rose: #e11d48;
      --navy: #07111f;
    }
    * { box-sizing: border-box; }
    body {
      background-color: #0f172a !important;
      color: #f8fafc !important;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
      margin: 0;
      padding: 0;
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
    h3 {
      font-size: 16px !important;
      font-weight: 700 !important;
      color: #f1f5f9 !important;
    }
    p, li, span {
      font-size: 14px !important;
      line-height: 1.55 !important;
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
  </style>"""

pos_s = content.find('<style>')
pos_e = content.find('</style>') + 8

if pos_s != -1 and pos_e != -1:
    content = content[:pos_s] + style_clean + content[pos_e:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("INDEX.HTML DEPURADO Y NORMALIZADO CON TOTAL PROLIDAD")
