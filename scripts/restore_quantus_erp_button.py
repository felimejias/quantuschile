import os
import glob

template_dir = "/Users/felipe/proyectos/quantuschile.cl/do/templates"
html_files = glob.glob(os.path.join(template_dir, "*.html"))

count = 0
for file_path in html_files:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Restaurar el texto exacto del botón que redirige al ERP de Quantus
    if 'class="cta-button btn-secondary">Quantus Chile</a>' in content or 'class="cta-button btn-secondary">Quantus System</a>' in content:
        content = content.replace('class="cta-button btn-secondary">Quantus Chile</a>', 'class="cta-button btn-secondary">Quantus ERP</a>')
        content = content.replace('class="cta-button btn-secondary">Quantus System</a>', 'class="cta-button btn-secondary">Quantus ERP</a>')
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        count += 1

print(f"BOTÓN RESTAURADO CORRECTAMENTE COMO 'Quantus ERP' EN {count} ARCHIVOS HTML")
