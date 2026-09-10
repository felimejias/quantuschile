import os
import glob
import re

template_dir = "/Users/felipe/proyectos/quantuschile.cl/do/templates"

# 1. Reemplazar "Quantus System" por el nombre oficial "Quantus Chile" en todas las plantillas HTML
html_files = glob.glob(os.path.join(template_dir, "*.html"))

count_name = 0
for file_path in html_files:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    if "Quantus System" in content:
        content = content.replace("Quantus System", "Quantus Chile")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        count_name += 1

print(f"1. Nombre 'Quantus System' reemplazado por 'Quantus Chile' en {count_name} archivos HTML.")

# 2. Corregir index.html: aplicar tema azul noche nativo sin parches conflictivos y ajustar títulos gigantes
path_index = os.path.join(template_dir, "index.html")
with open(path_index, "r", encoding="utf-8") as f:
    idx_content = f.read()

# Estandarización de tipografía h1, h2, h3 y fondo en index.html
clean_dark_index_css = """
<style id="quantus-clean-dark-theme">
  :root {
    --ink: #f8fafc !important;
    --muted: #94a3b8 !important;
    --line: rgba(56, 189, 248, 0.25) !important;
    --surface: #0f172a !important;
    --soft: #1e293b !important;
    --navy: #07111f !important;
  }
  body {
    background-color: #0f172a !important;
    color: #f8fafc !important;
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
</style>
"""

# Quitar parches anteriores desordenados en head e inyectar el CSS nativo limpio
if "</head>" in idx_content:
    idx_content = idx_content.replace("</head>", clean_dark_index_css + "\n</head>")
    with open(path_index, "w", encoding="utf-8") as f:
        f.write(idx_content)

print("2. Página de Inicio (index.html) unificada a la paleta corporativa oscura (#0F172A) con tipografías equilibradas.")
