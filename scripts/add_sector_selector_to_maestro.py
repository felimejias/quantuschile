path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/maestro_compliance_audit.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Desplegable de rubros e instituciones sujetas a la Ley 21.719
sector_dropdown_html = '''        <div class="form-group" style="grid-column: 1 / -1;">
          <label>Sector / Tipo de Institución Obligada por Ley N° 21.719 *</label>
          <select id="emp_rubro" onchange="autoGuardarDatos()" style="width:100%; padding:12px; background:#0f172a; border:1px solid #38bdf8; color:#38bdf8; font-weight:800; border-radius:10px; font-size:13px;">
            <option value="">-- Selecciona el Rubro o Tipo de Institución Cliente --</option>
            <optgroup label="🏥 SECTOR SALUD Y BIENESTAR (Datos Sensibles - Art. 32°)">
              <option value="Clínicas Privadas y Hospitales">Clínicas Privadas y Hospitales</option>
              <option value="Centros Médicos y Diagnóstico (Rayos/Ecografías)">Centros Médicos y Diagnóstico (Rayos/Ecografías)</option>
              <option value="Laboratorios Clínicos y Sangre">Laboratorios Clínicos y Sangre</option>
              <option value="Centros Odontológicos / Dentales">Centros Odontológicos / Dentales</option>
              <option value="Centros de Salud Mental y Psicología">Centros de Salud Mental y Psicología</option>
              <option value="Farmacias y Cadenas Farmacéuticas">Farmacias y Cadenas Farmacéuticas</option>
              <option value="Isapres / Fonasa / Cajas de Compensación">Isapres / Fonasa / Cajas de Compensación</option>
            </optgroup>
            <optgroup label="🏫 SECTOR EDUCACIÓN (Datos de Menores - Art. 34°)">
              <option value="Colegios Particulares Pagados">Colegios Particulares Pagados</option>
              <option value="Colegios Particulares Subvencionados (Corporaciones/Fundaciones)">Colegios Particulares Subvencionados (Corporaciones/Fundaciones)</option>
              <option value="Jardines Infantiles y Salas Cuna (Junji/Integra/Privados)">Jardines Infantiles y Salas Cuna (Junji/Integra/Privados)</option>
              <option value="Universidades e Institutos Profesionales (IP/CFT)">Universidades e Institutos Profesionales (IP/CFT)</option>
              <option value="Preuniversitarios y OTECs / Academias">Preuniversitarios y OTECs / Academias</option>
            </optgroup>
            <optgroup label="💳 SECTOR FINANCIERO, FINTECH Y COBRANZAS">
              <option value="Bancos e Instituciones Financieras">Bancos e Instituciones Financieras</option>
              <option value="Cooperativas de Ahorro y Crédito">Cooperativas de Ahorro y Crédito</option>
              <option value="Compañías de Seguros">Compañías de Seguros</option>
              <option value="FinTech, Pasarelas de Pago y Tarjetas">FinTech, Pasarelas de Pago y Tarjetas</option>
              <option value="Empresas de Cobranza Judicial y Extrajudicial">Empresas de Cobranza Judicial y Extrajudicial</option>
            </optgroup>
            <optgroup label="🛍️ COMMERCE, RETAIL Y PLATAFORMAS DIGITALES">
              <option value="E-Commerce y Tiendas Online (Shopify/WooCommerce)">E-Commerce y Tiendas Online (Shopify/WooCommerce)</option>
              <option value="Retail, Supermercados y Cadenas">Retail, Supermercados y Cadenas</option>
              <option value="Apps de Delivery y Movilidad">Apps de Delivery y Movilidad</option>
              <option value="Empresas de Courier y Logística">Empresas de Courier y Logística</option>
              <option value="Empresas SaaS, Software y Agencias Marketing">Empresas SaaS, Software y Agencias Marketing</option>
            </optgroup>
            <optgroup label="🏠 INMOBILIARIO, SERVICIOS Y OTROS">
              <option value="Inmobiliarias y Constructoras">Inmobiliarias y Constructoras</option>
              <option value="Corredoras de Propiedades y Arriendos">Corredoras de Propiedades y Arriendos</option>
              <option value="Administración de Condominios y Edificios">Administración de Condominios y Edificios</option>
              <option value="Estudios de Abogados y Consultoras">Estudios de Abogados y Consultoras</option>
              <option value="Contabilidades y Asesorías Tributarias">Contabilidades y Asesorías Tributarias</option>
              <option value="Automotoras y Concesionarias">Automotoras y Concesionarias</option>
              <option value="Empresas de Seguridad Privada y Alarmas">Empresas de Seguridad Privada y Alarmas</option>
            </optgroup>
          </select>
        </div>'''

if 'id="emp_rubro"' not in content:
    content = content.replace('<div class="form-group" style="grid-column: 1 / -1;">\n          <label>Dirección Legal Completa *</label>', sector_dropdown_html + '\n        <div class="form-group" style="grid-column: 1 / -1;">\n          <label>Dirección Legal Completa *</label>')

# Actualizar autoGuardarDatos y cargarCorrelativo para incluir emp_rubro
content = content.replace("direccion: document.getElementById('emp_direccion').value,", "direccion: document.getElementById('emp_direccion').value,\n        rubro: document.getElementById('emp_rubro').value,")
content = content.replace("document.getElementById('emp_direccion').value = data.direccion || '';", "document.getElementById('emp_direccion').value = data.direccion || '';\n      document.getElementById('emp_rubro').value = data.rubro || '';")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("DESPLEGABLE DE SECTORES E INSTITUCIONES OBLIGADAS INTEGRADO EN MAESTRO AUDIT")
