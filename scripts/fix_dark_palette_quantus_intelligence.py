path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/quantus_intelligence.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Cambiar la paleta root de blanca a azul noche corporativo (#0F172A)
content = content.replace('--surface: #ffffff;', '--surface: #0f172a;')
content = content.replace('--soft: #f5f8fc;', '--soft: #1e293b;')
content = content.replace('--ink: #111827;', '--ink: #f8fafc;')
content = content.replace('--muted: #64748b;', '--muted: #94a3b8;')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("PALETA CROMÁTICA DE QUANTUS_INTELLIGENCE.HTML CAMBIADA A MODO OSCURO AZUL NOCHE (#0F172A)")
