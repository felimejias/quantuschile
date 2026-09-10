import os
import glob

template_dir = "/Users/felipe/proyectos/quantuschile.cl/do/templates"

# CSS Estándar Ultra Premium para la Barra de Navegación y Botones de Retorno
standard_header_css = """
  /* Estilo Estándar Premium Quantus - Navegación y Botón Volver */
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
    gap: 8px !important;
    background: #1e293b !important;
    color: #38bdf8 !important;
    border: 1px solid rgba(56, 189, 248, 0.4) !important;
    padding: 8px 16px !important;
    border-radius: 10px !important;
    font-weight: 800 !important;
    font-size: 12px !important;
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
"""

html_files = [
    "checklist_ley21719.html",
    "maestro_compliance_audit.html",
    "ley_21719_guia.html",
    "licitaciones.html",
    "vigilancia_do.html",
    "prospeccion_do.html",
    "remates_inmuebles.html",
    "do_admin.html"
]

print("Iniciando estandarización de botones y barras de navegación...")
