path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/maestro_compliance_audit.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Corrección definitiva: Colegios, Jardines y Clínicas pasan al GRUPO 1 desde el 1 de Diciembre de 2026 sin excepción por Datos Sensibles y Menores (Art. 32° y 34°)
dropdown_corrected_html = '''        <div class="form-group" style="grid-column: 1 / -1;">
          <label>Sector / Tipo de Institución Obligada por Ley N° 21.719 *</label>
          <select id="emp_rubro" onchange="autoGuardarDatos()" style="width:100%; padding:12px; background:#0f172a; border:1px solid #38bdf8; color:#38bdf8; font-weight:800; border-radius:10px; font-size:13px;">
            <option value="">-- Selecciona el Rubro o Tipo de Institución Cliente --</option>
            
            <optgroup label="🚨 GRUPO 1: APLICACIÓN EXIGIBLE Y MULTAS DESDE 1 DIC 2026 (Datos Sensibles, Niños o Ventas > $960M)">
              <option value="Colegios Particulares y Subvencionados (Rige 1 Dic 2026 - Datos Menores Art. 34°)">Colegios Particulares y Subvencionados (Rige 1 Dic 2026 - Datos Menores Art. 34°)</option>
              <option value="Jardines Infantiles y Salas Cuna (Rige 1 Dic 2026 - Datos Menores Art. 34°)">Jardines Infantiles y Salas Cuna (Rige 1 Dic 2026 - Datos Menores Art. 34°)</option>
              <option value="Clínicas, Centros Médicos y Dentales (Rige 1 Dic 2026 - Datos Salud Art. 32°)">Clínicas, Centros Médicos y Dentales (Rige 1 Dic 2026 - Datos Salud Art. 32°)</option>
              <option value="Bancos, Financieras, AFPs e Isapres (Rige 1 Dic 2026 - Grandes Corporaciones)">Bancos, Financieras, AFPs e Isapres (Rige 1 Dic 2026 - Grandes Corporaciones)</option>
              <option value="Grandes Cadenas de Retail y Supermercados (Rige 1 Dic 2026 - Facturación > $960M)">Grandes Cadenas de Retail y Supermercados (Rige 1 Dic 2026 - Facturación > $960M)</option>
              <option value="Universidades y Grandes Institutos (Rige 1 Dic 2026 - Matrículas Masivas)">Universidades y Grandes Institutos (Rige 1 Dic 2026 - Matrículas Masivas)</option>
              <option value="Inmobiliarias Grandes y Telecomunicaciones (Rige 1 Dic 2026)">Inmobiliarias Grandes y Telecomunicaciones (Rige 1 Dic 2026)</option>
              <option value="Organismos Públicos y Municipalidades (Rige 1 Dic 2026)">Organismos Públicos y Municipalidades (Rige 1 Dic 2026)</option>
            </optgroup>

            <optgroup label="🛡️ GRUPO 2: PERÍODO DE GRACIA PEDAGÓGICO DE 1 AÑO (Solo PyMEs de Datos Generales de Adultos)">
              <option value="Tiendas E-Commerce PyME y Emprendimientos (Año Gracia Pedagógico)">Tiendas E-Commerce PyME y Emprendimientos (Año Gracia Pedagógico)</option>
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
    content = content[:pos_start] + dropdown_corrected_html + '\n        ' + content[pos_end:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("DESPLEGABLE CORREGIDO: COLEGIOS, JARDINES Y CLÍNICAS PASAN AL GRUPO 1 DESDE 1 DIC 2026")
