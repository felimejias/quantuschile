path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/maestro_compliance_audit.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Actualizar script JS para mostrar el formulario dinámico RAT cuando sea la opción 1
js_func = '''
    let ratItems = [];

    function abrirGuiaTecnica(id) {
      const g = guiasTecnicas[id];
      if (g) {
        document.getElementById('modal-guide-title').innerText = g.title;
        document.getElementById('modal-guide-req').innerText = g.req;
        document.getElementById('modal-guide-work').innerHTML = g.work;
        
        const ratSec = document.getElementById('interactive-rat-section');
        if (id === 'c1') {
          ratSec.style.display = 'block';
          renderRatRecords();
        } else {
          ratSec.style.display = 'none';
        }

        document.getElementById('modal-item-guide').style.display = 'flex';
      }
    }

    function agregarFilaRAT() {
      const nombre = document.getElementById('rat_nombre_lista').value;
      const soporte = document.getElementById('rat_soporte').value;
      const datos = document.getElementById('rat_datos').value;
      const finalidad = document.getElementById('rat_finalidad').value;

      if (!nombre) { alert('Ingresa el nombre de la lista'); return; }

      ratItems.push({ nombre, soporte, datos, finalidad });
      document.getElementById('rat_nombre_lista').value = '';
      document.getElementById('rat_datos').value = '';
      document.getElementById('rat_finalidad').value = '';
      renderRatRecords();
    }

    function renderRatRecords() {
      const listDiv = document.getElementById('rat-records-list');
      if (ratItems.length === 0) {
        listDiv.innerHTML = '<em style="color:#64748b;">No hay registros de listas agregados todavía.</em>';
        return;
      }
      let html = '<ul style="margin:0; padding-left:16px;">';
      ratItems.forEach((r, idx) => {
        html += `<li><strong>${r.nombre}</strong> (${r.soporte}) - Datos: ${r.datos} | Uso: ${r.finalidad}</li>`;
      });
      html += '</ul>';
      listDiv.innerHTML = html;
    }
'''

if 'function agregarFilaRAT()' not in content:
    pos = content.find('function abrirGuiaTecnica(id) {')
    pos_end = content.find('function cerrarModalGuia() {')
    content = content[:pos] + js_func + '\n\n    ' + content[pos_end:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print("JS DE FORMULARIO DINÁMICO RAT Y RENDERING CORRECTO")
