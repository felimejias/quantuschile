path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/index.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar directamente las fuentes gigantes y fondos claros en el bloque <style> original de index.html
old_root = """    :root {
      --ink: #f8fafc;
      --muted: #94a3b8;
      --line: rgba(56, 189, 248, 0.2);
      --surface: #0f172a;
      --soft: #1e293b;
      --cyan: #0ea5e9;
      --emerald: #10b981;
      --violet: #7c3aed;
      --amber: #f59e0b;
      --rose: #e11d48;
      --navy: #07111f;
    }"""

new_root = """    :root {
      --ink: #f8fafc;
      --muted: #94a3b8;
      --line: rgba(56, 189, 248, 0.2);
      --surface: #0f172a;
      --soft: #1e293b;
      --cyan: #0ea5e9;
      --emerald: #10b981;
      --violet: #7c3aed;
      --amber: #f59e0b;
      --rose: #e11d48;
      --navy: #07111f;
    }
    body {
      background-color: #0f172a !important;
      color: #f8fafc !important;
    }
    h1 {
      font-size: 32px !important;
      line-height: 1.25 !important;
      font-weight: 900 !important;
    }
    h2 {
      font-size: 22px !important;
      line-height: 1.3 !important;
    }"""

if old_root in content:
    content = content.replace(old_root, new_root)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("ESTILO NATIVO EN INDEX.HTML CORREGIDO DE FORMA PROLIJA")
else:
    print("No se encontró old_root")
