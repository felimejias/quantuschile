path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/index.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazo directo y forzado de la paleta en index.html
content = content.replace('var(--surface)', '#0f172a')
content = content.replace('--surface: #ffffff;', '--surface: #0f172a;\n      --soft: #1e293b;\n      --ink: #f8fafc;\n      --muted: #94a3b8;')
content = content.replace('background: #ffffff;', 'background: #0f172a;')
content = content.replace('background:#ffffff;', 'background:#0f172a;')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("REEMPLAZO CROMÁTICO APROBADO COMPLETADO")
