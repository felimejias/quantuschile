path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/maestro_compliance_audit.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Actualizar el desplegable en maestro_compliance_audit.html separando explícitamente los 2 grupos de fiscalización
new_dropdown_html = '''        <div class="form-group" style="grid-column: 1 / -1;">
          <label>Sector / Tipo de Institución Obligada por Ley N° 21.719 *</label>
          <select id="emp_rubro" onchange="autoGuardarDatos()" style="width:100%; padding:12px; background:#0f172a; border:1px solid #38bdf8; color:#38bdf8; font-weight:800; border-radius:10px; font-size:13px;">
            <option value="">-- Selecciona el Rubro o Tipo de Institución Cliente --</option>
            
            <optgroup label="🚨 GRUPO 1: MULTAS DIRECTAS DESDE EL 1 DE DICIEMBRE 2026 (Grandes Empresas > $960M CLP / Corporaciones)">
              <option value="Bancos, Financieras, AFPs e Isapres (Multas Directas 1 Dic 2026)">Bancos, Financieras, AFPs e Isapres (Multas Directas 1 Dic 2026)</option>
              <option value="Grandes Cadenas de Retail y Supermercados (Multas Directas 1 Dic 2026)">Grandes Cadenas de Retail y Supermercados (Multas Directas 1 Dic 2026)</option>
              <option value="Clínicas Privadas y Grandes Hospitales (Multas Directas 1 Dic 2026)">Clínicas Privadas y Grandes Hospitales (Multas Directas 1 Dic 2026)</option>
              <option value="Universidades y Grandes Institutos (Multas Directas 1 Dic 2026)">Universidades y Grandes Institutos (Multas Directas 1 Dic 2026)</option>
              <option value="Inmobiliarias Grandes y Telecomunicaciones (Multas Directas 1 Dic 2026)">Inmobiliarias Grandes y Telecomunicaciones (Multas Directas 1 Dic 2026)</option>
              <option value="Organismos Públicos y Municipalidades (Multas Directas 1 Dic 2026)">Organismos Públicos y Municipalidades (Multas Directas 1 Dic 2026)</option>
            </optgroup>

            <optgroup label="🛡️ GRUPO 2: PERÍODO DE GRACIA PEDAGÓGICO DE 1 AÑO (PyMEs < 25.000 UF / ~$960M CLP - Dic 2026 a 2027)">
              <option value="Colegios Pequeños / Jardines Infantiles PyME (Año Gracia Pedagógico)">Colegios Pequeños / Jardines Infantiles PyME (Año Gracia Pedagógico)</option>
              <option value="Tiendas E-Commerce PyME y Emprendimientos (Año Gracia Pedagógico)">Tiendas E-Commerce PyME y Emprendimientos (Año Gracia Pedagógico)</option>
              <option value="Centros Médicos Pequeños / Dentales PyME (Año Gracia Pedagógico)">Centros Médicos Pequeños / Dentales PyME (Año Gracia Pedagógico)</option>
              <option value="Corredoras de Propiedades PyME y Condominios (Año Gracia Pedagógico)">Corredoras de Propiedades PyME y Condominios (Año Gracia Pedagógico)</option>
              <option value="Estudios de Abogados y Contadores PyME (Año Gracia Pedagógico)">Estudios de Abogados y Contadores PyME (Año Gracia Pedagógico)</option>
              <option value="Agencias Marketing, OTECs y Servicios PyME (Año Gracia Pedagógico)">Agencias Marketing, OTECs y Servicios PyME (Año Gracia Pedagógico)</option>
              <option value="Gimnasios y Automotoras PyME (Año Gracia Pedagógico)">Gimnasios y Automotoras PyME (Año Gracia Pedagógico)</option>
            </optgroup>
          </select>
        </div>'''

pos_start = content.find('<div class="form-group" style="grid-column: 1 / -1;">\n          <label>Sector / Tipo de Institución Obligada por Ley N° 21.719 *</label>')
pos_end = content.find('<div class="form-group" style="grid-column: 1 / -1;">\n          <label>Dirección Legal Completa *</label>')

if pos_start != -1 and pos_end != -1:
    content = content[:pos_start] + new_dropdown_html + '\n        ' + content[pos_end:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("DESPLEGABLE MAESTRO ACTUALIZADO SEPARANDO GRUPO 1 (MULTAS DIRECTAS) Y GRUPO 2 (GRACIA PYME)")
else:
    print("No se encontró el bloque anterior")
