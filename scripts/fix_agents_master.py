path = '/Users/felipe/proyectos/quantuschile.cl/do/AGENTS.md'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

pos = content.find('## 🏢 6. DATOS CORPORATIVOS OFICIALES')
if pos != -1:
    new_sec = '''## 🏢 6. DATOS CORPORATIVOS OFICIALES Y DOCUMENTOS LEGALES (QUANTUS CHILE SpA)
- **Razón Social**: Quantus Chile SpA
- **RUT Empresa**: `78.478.612-9` (Fuente: `app.py` L2099 / L2122)
- **Giro Comercial**: Desarrollo de Software, Portales Web, Procesamiento de Datos, Hospedaje y Consultoría Informática.
- **Domicilio Societario**: Rancagua, Región del Libertador General Bernardo O'Higgins, Chile.
- **Emails Oficiales**: `contacto@quantuschile.cl` | ARCO Ley 21.719: `privacidad@quantuschile.cl`.
- **Archivo JSON Consolidado**: `/data/datos_corporativos_quantus.json`.
'''
    content = content[:pos] + new_sec
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print("AGENTS.md MAESTRO REPARADO CON DATOS REALES 78.478.612-9")
