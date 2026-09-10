path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/index.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar variables CSS en root para cambiar el tema claro a la paleta azul noche corporativa sin deslumbrar el ojo
content = content.replace('--surface: #ffffff;', '--surface: #0f172a;')
content = content.replace('--soft: #f5f8fc;', '--soft: #1e293b;')
content = content.replace('--ink: #111827;', '--ink: #f8fafc;')
content = content.replace('--muted: #64748b;', '--muted: #94a3b8;')
content = content.replace('--line: #d8e1ec;', '--line: rgba(56, 189, 248, 0.2);')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("PALETA CORPORATIVA AZUL NOCHE (#0F172A) APLICADA A INDEX.HTML CON ÉXITO")
