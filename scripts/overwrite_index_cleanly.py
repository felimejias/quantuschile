path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/index.html'

html_code = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Quantus Chile | Inteligencia Legal, Comercial y Operacional</title>
  <link rel="icon" type="image/png" href="/static/quantus-logo-clean.png">

  <style>
    :root {
      --ink: #f8fafc;
      --muted: #94a3b8;
      --line: rgba(56, 189, 248, 0.25);
      --surface: #0f172a;
      --soft: #1e293b;
      --cyan: #38bdf8;
      --emerald: #10b981;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      color: #f8fafc;
      background-color: #0f172a !important;
      min-height: 100vh;
      overflow-x: hidden;
    }
    a { text-decoration: none; color: inherit; }

    /* Barra de Navegación Estándar Premium */
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
    .quantus-btn-erp {
      background: rgba(16,185,129,0.2) !important;
      border-color: #10b981 !important;
      color: #6ee7b7 !important;
    }
    .quantus-btn-erp:hover {
      background: #10b981 !important;
      color: #0f172a !important;
    }
    .quantus-btn-admin {
      background: rgba(245,158,11,0.2) !important;
      border-color: #f59e0b !important;
      color: #fcd34d !important;
    }

    .hero-section {
      padding: 60px 24px;
      max-width: 1100px;
      margin: 0 auto;
      text-align: center;
    }
    .hero-eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(56,189,248,0.15);
      color: #38bdf8;
      padding: 6px 16px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 20px;
      border: 1px solid rgba(56,189,248,0.3);
    }
    .hero-title {
      font-size: 34px !important;
      line-height: 1.25 !important;
      font-weight: 900 !important;
      color: #ffffff !important;
      margin-bottom: 16px;
    }
    .hero-sub {
      font-size: 16px !important;
      color: #94a3b8 !important;
      line-height: 1.6 !important;
      max-width: 780px;
      margin: 0 auto 32px auto;
    }
    .grid-services {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 20px;
      max-width: 1100px;
      margin: 0 auto 60px auto;
      padding: 0 24px;
    }
    .card-service {
      background: #1e293b !important;
      border: 1px solid rgba(56,189,248,0.2) !important;
      border-radius: 16px;
      padding: 24px;
      text-align: left;
      box-shadow: 0 10px 25px rgba(0,0,0,0.4);
      transition: transform 0.2s;
    }
    .card-service:hover { transform: translateY(-4px); border-color: #38bdf8 !important; }
    .card-icon { font-size: 28px; margin-bottom: 12px; }
    .card-title { font-size: 18px !important; font-weight: 800 !important; color: #ffffff !important; margin-bottom: 8px; }
    .card-desc { font-size: 13px !important; color: #94a3b8 !important; line-height: 1.5 !important; margin-bottom: 16px; }
  </style>
</head>
<body>

  <header class="quantus-nav-bar">
    <div style="display:flex; align-items:center; gap:12px;">
      <a href="/" style="display:flex; align-items:center; gap:8px;">
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
      <a href="https://www.quantuschile.cl" class="quantus-nav-btn quantus-btn-erp">🖥️ QUANTUS ERP</a>
      <a href="/maestro" class="quantus-nav-btn quantus-btn-admin">🔒 ADMINISTRACIÓN</a>
    </div>
  </header>

  <section class="hero-section">
    <div class="hero-eyebrow">🌐 ECOSISTEMA DE INTELIGENCIA LEGAL Y OPERACIONAL</div>
    <h1 class="hero-title">Monitoreo de Fuentes Oficiales, Radares Comerciales y Cumplimiento Normativo en Chile</h1>
    <p class="hero-sub">
      Quantus Chile SpA conecta la información del Diario Oficial, Mercado Público (Licitaciones), INAPI, Remates Judiciales y Auditorías de Cumplimiento Ley N° 21.719 en una sola plataforma integrada.
    </p>
  </section>

  <div class="grid-services">
    <div class="card-service">
      <div class="card-icon">⚖️</div>
      <div class="card-title">Cumplimiento Ley N° 21.719</div>
      <div class="card-desc">Auditoría técnica de 24 controles, evaluación de riesgos PIA, plantillas RAT en Excel y portal de derechos ARCOP+.</div>
      <a href="/checklist-ley-21719" class="quantus-nav-btn" style="width:100%; justify-content:center;">Realizar Test Diagnóstico</a>
    </div>

    <div class="card-service">
      <div class="card-icon">📰</div>
      <div class="card-title">Vigilancia del Diario Oficial</div>
      <div class="card-desc">Alertas preventivas de publicaciones legales, citaciones, constituciones de empresas y avisos a acreedores.</div>
      <a href="/do/prospeccion" class="quantus-nav-btn" style="width:100%; justify-content:center;">Ver Radar Diario Oficial</a>
    </div>

    <div class="card-service">
      <div class="card-icon">🏛️</div>
      <div class="card-title">Licitaciones Mercado Público</div>
      <div class="card-desc">Monitoreo 24/7 de oportunidades de compras estatales con análisis de bases e IA explicativa.</div>
      <a href="/licitaciones" class="quantus-nav-btn" style="width:100%; justify-content:center;">Explorar Licitaciones</a>
    </div>

    <div class="card-service">
      <div class="card-icon">🏷️</div>
      <div class="card-title">Registro de Marcas INAPI</div>
      <div class="card-desc">Buscador de marcas en Chile, cálculo de tasas oficiales y custodia contra oposiciones.</div>
      <a href="/inapi" class="quantus-nav-btn" style="width:100%; justify-content:center;">Buscar Marcas</a>
    </div>

    <div class="card-service">
      <div class="card-icon">🖥️</div>
      <div class="card-title">Quantus ERP (BodegaPro)</div>
      <div class="card-desc">Sistema autoritativo de punto de venta (POS), inventario, compras, shopper y control multi-tenant.</div>
      <a href="https://www.quantuschile.cl" class="quantus-nav-btn quantus-btn-erp" style="width:100%; justify-content:center;">Acceder al ERP</a>
    </div>

    <div class="card-service">
      <div class="card-icon">🔒</div>
      <div class="card-title">Panel Maestro Privado</div>
      <div class="card-desc">Centro de control para auditores y administradores Quantus con emisión de Certificados de Cumplimiento.</div>
      <a href="/maestro" class="quantus-nav-btn quantus-btn-admin" style="width:100%; justify-content:center;">Entrar a Administración</a>
    </div>
  </div>

  <footer style="text-align:center; padding:30px 20px; color:#64748b; font-size:13px; border-top:1px solid rgba(56, 189, 248, 0.15);">
    <p>&copy; 2026 Quantus Chile SpA — RUT 78.478.612-9 · Todos los derechos reservados.</p>
  </footer>

</body>
</html>"""

with open(path, 'w', encoding='utf-8') as f:
    f.write(html_code)

print("ARCHIVO INDEX.HTML SOBREESCRITO CON ÉXITO Y CON LA BARRA DE NAVEGACIÓN Y EL BOTÓN QUANTUS ERP CORREGIDOS")
