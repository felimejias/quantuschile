#!/usr/bin/env python3
"""
Generador de Ficha Comercial Quantus ERP en PDF
Crea un documento comercial de 1 página de altísimo impacto visual con diseño Dark Glassmorphism,
precios, características y capturas de pantalla, listo para enviar a clientes por WhatsApp/Email.
"""

import os
from playwright.sync_api import sync_playwright

OUTPUT_PDF = "/tmp/quantus_ficha_comercial.pdf"
OUTPUT_PNG = "/tmp/quantus_ficha_comercial.png"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800;900&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Inter', sans-serif;
    background: #08101e;
    color: #f8fafc;
    width: 1200px;
    height: 1600px;
    padding: 60px;
    position: relative;
    overflow: hidden;
  }
  .glow-top {
    position: absolute;
    top: -100px;
    right: -100px;
    width: 500px;
    height: 500px;
    background: radial-gradient(circle, rgba(56, 189, 248, 0.25) 0%, transparent 70%);
  }
  .glow-bot {
    position: absolute;
    bottom: -100px;
    left: -100px;
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(139, 92, 246, 0.2) 0%, transparent 70%);
  }
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding-bottom: 30px;
    margin-bottom: 40px;
  }
  .logo-title {
    display: flex;
    align-items: center;
    gap: 18px;
  }
  .logo-badge {
    width: 60px;
    height: 60px;
    border-radius: 18px;
    background: linear-gradient(135deg, #0284c7, #2563eb);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    box-shadow: 0 10px 25px rgba(2, 132, 199, 0.4);
  }
  .brand-name {
    font-size: 32px;
    font-weight: 900;
    letter-spacing: -0.5px;
  }
  .brand-name span { color: #38bdf8; }
  .tagline {
    font-size: 14px;
    color: #94a3b8;
    margin-top: 4px;
  }
  .hero {
    text-align: center;
    margin-bottom: 50px;
  }
  .hero h1 {
    font-size: 42px;
    font-weight: 900;
    line-height: 1.2;
    margin-bottom: 16px;
    background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 50%, #38bdf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .hero p {
    font-size: 18px;
    color: #94a3b8;
    max-width: 800px;
    margin: 0 auto;
    line-height: 1.6;
  }
  .grid-features {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    margin-bottom: 50px;
  }
  .feature-card {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    padding: 24px;
    backdrop-filter: blur(12px);
  }
  .feature-icon {
    font-size: 32px;
    margin-bottom: 12px;
  }
  .feature-title {
    font-size: 18px;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 8px;
  }
  .feature-desc {
    font-size: 13px;
    color: #94a3b8;
    line-height: 1.5;
  }
  .plans-section {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 24px;
    margin-bottom: 40px;
  }
  .plan-card {
    background: rgba(11, 21, 38, 0.9);
    border: 1px solid rgba(56, 189, 248, 0.25);
    border-radius: 24px;
    padding: 30px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4);
  }
  .plan-card.featured {
    border: 2px solid #38bdf8;
    background: linear-gradient(180deg, rgba(14, 30, 56, 0.95) 0%, rgba(8, 16, 30, 0.98) 100%);
    box-shadow: 0 20px 45px rgba(56, 189, 248, 0.25);
    transform: scale(1.03);
  }
  .plan-badge {
    align-self: flex-start;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 800;
    background: rgba(56, 189, 248, 0.2);
    color: #38bdf8;
    margin-bottom: 14px;
  }
  .plan-name {
    font-size: 22px;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 6px;
  }
  .plan-price {
    font-size: 34px;
    font-weight: 900;
    color: #38bdf8;
    margin-bottom: 16px;
  }
  .plan-price span {
    font-size: 14px;
    color: #94a3b8;
    font-weight: 500;
  }
  .plan-list {
    list-style: none;
    margin-bottom: 24px;
  }
  .plan-list li {
    font-size: 13px;
    color: #cbd5e1;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .plan-list li::before {
    content: "✓";
    color: #10b981;
    font-weight: 900;
  }
  .footer {
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    padding-top: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 14px;
    color: #94a3b8;
  }
  .contact-btn {
    background: linear-gradient(135deg, #0284c7, #2563eb);
    color: #ffffff;
    padding: 12px 24px;
    border-radius: 12px;
    font-weight: 700;
    text-decoration: none;
    display: inline-block;
  }
</style>
</head>
<body>
<div class="glow-top"></div>
<div class="glow-bot"></div>

<div class="header">
  <div class="logo-title">
    <div class="logo-badge">⚡</div>
    <div>
      <div class="brand-name">Quantus <span>App</span></div>
      <div class="tagline">ERP Inteligente & Centro de Mando Empresarial</div>
    </div>
  </div>
  <div style="text-align: right;">
    <div style="font-size: 12px; color: #64748b;">DISPONIBILIDAD INMEDIATA</div>
    <div style="font-size: 16px; font-weight: 700; color: #38bdf8;">🌐 quantuschile.cl/app</div>
  </div>
</div>

<div class="hero">
  <h1>Control Total de tu Negocio en tu Bolsillo</h1>
  <p>Punto de venta ultra-rápido, gestión multibodega, órdenes de compra automatizadas y radar financiero en tiempo real para Ferreterías, Minimarkets, Farmacias y Bodegas.</p>
</div>

<div class="grid-features">
  <div class="feature-card">
    <div class="feature-icon">🛡️</div>
    <div class="feature-title">Centro de Mando Dueño</div>
    <div class="feature-desc">Métricas de margen neto, utilidad bruta en vivo, ticket promedio y radar de quiebres de stock desde cualquier teléfono o PC.</div>
  </div>
  <div class="feature-card">
    <div class="feature-icon">⚡</div>
    <div class="feature-title">Continuidad Offline-First</div>
    <div class="feature-desc">¿Se cayó el internet? Tu caja sigue cobrando sin parar. La cola inteligente sincroniza las boletas automáticamente al volver la red.</div>
  </div>
  <div class="feature-card">
    <div class="feature-icon">🤖</div>
    <div class="feature-title">Copiloto Inteligente AI</div>
    <div class="feature-desc">Auditoría automática de mermas, detección de productos estancados y sugerencia predictiva de órdenes de compra.</div>
  </div>
</div>

<div class="plans-section">
  <div class="plan-card">
    <div>
      <div class="plan-badge">INICIAL</div>
      <div class="plan-name">Comercio Básico</div>
      <div class="plan-price">$19.990 <span>/ mes</span></div>
      <ul class="plan-list">
        <li>1 Rubro comercial habilitado</li>
        <li>Caja POS táctil e impresora térmica</li>
        <li>Control de inventario simple</li>
        <li>Boleta y arqueo de turnos</li>
        <li>Soporte técnico por WhatsApp</li>
      </ul>
    </div>
  </div>

  <div class="plan-card featured">
    <div>
      <div class="plan-badge" style="background: rgba(16, 185, 129, 0.25); color: #34d399;">MÁS POPULAR</div>
      <div class="plan-name">Pyme Pro Multi-Caja</div>
      <div class="plan-price">$39.990 <span>/ mes</span></div>
      <ul class="plan-list">
        <li>Hasta 3 Rubros simultáneos</li>
        <li>App Móvil Administrador instalable</li>
        <li>Modo Offline-First garantizado</li>
        <li>Órdenes de Compra y Recepción</li>
        <li>Radar de Quiebres y Stock Crítico</li>
        <li>Historial de clientes y crédito</li>
      </ul>
    </div>
  </div>

  <div class="plan-card">
    <div>
      <div class="plan-badge">EMPRESAS</div>
      <div class="plan-name">Corporativo Enterprise</div>
      <div class="plan-price">$69.990 <span>/ mes</span></div>
      <ul class="plan-list">
        <li>Todos los rubros ilimitados</li>
        <li>Multi-sucursal y multi-bodega</li>
        <li>Copiloto Ejecutivo IA en vivo</li>
        <li>Migración Express desde Excel</li>
        <li>Acceso a API y base de datos</li>
        <li>Ejecutivo de cuenta dedicado 24/7</li>
      </ul>
    </div>
  </div>
</div>

<div class="footer">
  <div>
    <strong>Quantus System Chile SpA</strong> · Rancagua, Chile<br>
    Contacto: contacto@quantuschile.cl · WhatsApp: +56 9 8478 6129
  </div>
  <div class="contact-btn">🚀 Solicitar Demo Gratis</div>
</div>

</body>
</html>
"""

def generate_pdf():
    print("📄 Generando Ficha Comercial Quantus en PDF...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1200, "height": 1600})
        page.set_content(HTML_TEMPLATE)
        page.wait_for_timeout(1000)
        
        # 1. Export PDF
        page.pdf(
            path=OUTPUT_PDF,
            width="1200px",
            height="1600px",
            print_background=True,
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"}
        )
        print(f"✅ PDF guardado exitosamente en: {OUTPUT_PDF}")

        # 2. Export PNG preview
        page.screenshot(path=OUTPUT_PNG, full_page=True)
        print(f"✅ Preview PNG guardado en: {OUTPUT_PNG}")
        
        browser.close()

if __name__ == "__main__":
    generate_pdf()
