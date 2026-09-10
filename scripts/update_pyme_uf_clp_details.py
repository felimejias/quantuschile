path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/maestro_compliance_audit.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Actualización del texto explicativo del Punto 22 para dejar ultra claro la definición de PyME (Ley N° 20.416)
old_desc = '"22. Registro de Período de Gracia PyME (Art. Transitorio)", desc: "Identificación de PyMEs elegibles para el año de acompañamiento sin multas de la Agencia (diciembre 2026 a 2027)."'
new_desc = '"22. Registro de Período de Gracia PyME (Art. Transitorio)", desc: "Identificación de PyMEs (ventas anuales inferiores a 25.000 UF / ~$960 Millones CLP) elegibles para el año de acompañamiento sin multas de dinero (diciembre 2026 a 2027)."'

old_guide = 'req: "Período de acompañamiento pedagógico de 1 año sin multas económicas para PyMEs.", toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">\n          🛡️ <strong>Estatus PyME:</strong> Registro de ventas anuales inferiores a 25.000 UF para amparo pedagógico.\n        </div>`, work: "<ol style=\\"margin:0; padding-left:18px;\\">\n          <li><strong>Paso 1:</strong> Adjuntar carpeta tributaria para certificar estatus PyME y acogerse al año de gracias.</li>\n        </ol>"'

new_guide = 'req: "La Ley N° 21.719 otorga un Período de Gracia Pedagógico de 1 AÑO SIN MULTAS DE DINERO (diciembre 2026 a diciembre 2027) exclusivo para PyMEs.", toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:12px; border-radius:8px; border:1px solid #10b981; font-size:12px; color:#10b981;">\n          📊 <strong>Definición Legal de PyME (Ley N° 20.416):</strong><br>\n          Se considera PyME a toda empresa con ingresos anuales por ventas inferiores a <strong>25.000 UF (Aproximadamente $960 Millones de Pesos Chilenos - $960.000.000 CLP)</strong> en el último año calendario.\n        </div>`, work: "<ol style=\\"margin:0; padding-left:18px;\\">\n          <li><strong>Paso 1 (Revisar Formulario 29 / Carpeta Tributaria):</strong> Verifica en el Formulario 29 del SII que las ventas netas anuales de la empresa no superen las 25.000 UF (~$960.000.000 CLP).</li>\n          <li><strong>Paso 2 (Emitir Certificado de Acompañamiento PyME):</strong> Si cumple, Quantus emite el documento oficial para presentar ante la Agencia indicando que la empresa se acoge al período de gracia de 1 año con amonestación pedagógica sin multas de dinero.</li>\n        </ol>"'

if old_desc in content:
    content = content.replace(old_desc, new_desc)

if 'req: "Período de acompañamiento pedagógico de 1 año' in content:
    pos_start = content.find('c22: {')
    pos_end = content.find('};\n\n    let currentCorrelativo = 1;')
    if pos_start != -1 and pos_end != -1:
        c22_full = '''c22: {
        title: "22. Registro de Período de Gracia PyME (Art. Transitorio)",
        req: "La Ley N° 21.719 otorga un Período de Gracia Pedagógico de 1 AÑO SIN MULTAS DE DINERO (diciembre 2026 a diciembre 2027) exclusivo para PyMEs.",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:12px; border-radius:8px; border:1px solid #10b981; font-size:12px; color:#cbd5e1; line-height:1.5;">
          📊 <strong style="color:#10b981;">Definición Legal de PyME (Ley N° 20.416):</strong><br>
          Se considera PyME a toda empresa con ingresos anuales por ventas inferiores a <strong>25.000 UF (Aproximadamente $960 Millones de Pesos Chilenos - $960.000.000 CLP)</strong> en el último año calendario.
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1 (Revisar F29 / Carpeta Tributaria):</strong> Verifica en la carpeta tributaria del SII que las ventas netas anuales de la empresa no superen las 25.000 UF (~$960.000.000 CLP).</li>
          <li><strong>Paso 2 (Emitir Certificado PyME Quantus):</strong> Si cumple, Quantus emite el documento oficial declarando el estatus de PyME para acogerse al acompañamiento de 1 año sin multas de dinero de la Agencia.</li>
        </ol>`
      }'''
        content = content[:pos_start] + c22_full + '\n    ' + content[pos_end:]

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("DEFINICIÓN DE PYME CON VENTAS EN UF Y PESOS CHILENOS EXACTOS APLICADA EN MAESTRO AUDIT")
