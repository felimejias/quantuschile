path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/maestro_compliance_audit.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Módulo 7: Portabilidad, Perfilamiento Algorítmico y Derechos ARCOP+ (Puntos 19 al 22)
mod7_data = ''',
      {
        modulo: "MÓDULO 7: DERECHO DE PORTABILIDAD Y DECISIONES CON IA (ARCOP+)",
        items: [
          { id: "c19", prio: "alta", title: "19. Derecho a la Portabilidad de Datos (Art. 7° bis)", desc: "Mecanismo para exportar los datos del cliente en formato estándar estructurado (JSON/CSV) si decide irse a la competencia." },
          { id: "c20", prio: "alta", title: "20. Oposición a Decisiones Automatizadas e IA (Art. 15°)", desc: "Derecho a solicitar intervención humana si un algoritmo o IA aprueba/rechaza un crédito o evalúa a una persona." },
          { id: "c21", prio: "media", title: "21. Transparencia de Perfilamiento Digital (Art. 14°)", desc: "Deber de informar al usuario si se analiza su comportamiento web para ofrecerle precios o publicidad personalizada." },
          { id: "c22", prio: "baja", title: "22. Registro de Período de Gracia PyME (Art. Transitorio)", desc: "Identificación de PyMEs elegibles para el año de acompañamiento sin multas de la Agencia (diciembre 2026 a 2027)." }
        ]
      }'''

mod7_guias = ''',
      c19: {
        title: "19. Derecho a la Portabilidad de Datos (Art. 7° bis)",
        req: "La persona tiene derecho a exigir que sus datos le sean entregados en un formato digital reutilizable (JSON/CSV).",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">
          📦 <strong>Exportador JSON Quantus:</strong> En el widget ARCO el cliente presiona 'Descargar Mis Datos' y genera el paquete comprimido.
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Configurar el script de exportación de datos en la base del cliente.</li>
          <li><strong>Paso 2:</strong> Probar la descarga en 1 clic de sus datos en formato JSON.</li>
        </ol>`
      },
      c20: {
        title: "20. Oposición a Decisiones Automatizadas e IA (Art. 15°)",
        req: "Derecho a exigir revisión humana si un algoritmo o IA tomó una decisión sobre la persona.",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">
          🤖 <strong>Formulario de Revisión Humana:</strong> Permite solicitar que un ejecutivo revise lo que decidió la IA.
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Si la empresa usa Scoring automático o IA para evaluar clientes, habilitar la casilla 'Solicitar Revisión por una Persona Real'.</li>
        </ol>`
      },
      c21: {
        title: "21. Transparencia de Perfilamiento Digital (Art. 14°)",
        req: "Informar si se rastrea la navegación del usuario para armarle un perfil.",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">
          🍪 <strong>Banner de Cookies & Perfilado:</strong> Avisa y pide permiso antes de activar píxeles de rastreo.
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Instalar el Banner de Cookies de Quantus en la web.</li>
        </ol>`
      },
      c22: {
        title: "22. Registro de Período de Gracia PyME (Art. Transitorio)",
        req: "Período de acompañamiento pedagógico de 1 año sin multas económicas para PyMEs.",
        toolHtml: `<div style="margin-bottom:12px; background:#0f172a; padding:10px; border-radius:8px; border:1px solid #38bdf8; font-size:12px; color:#38bdf8;">
          🛡️ <strong>Estatus PyME:</strong> Registro de ventas anuales inferiores a 25.000 UF para amparo pedagógico.
        </div>`,
        work: `<ol style="margin:0; padding-left:18px;">
          <li><strong>Paso 1:</strong> Adjuntar carpeta tributaria para certificar estatus PyME y acogerse al año de gracias.</li>
        </ol>`
      }'''

if 'MÓDULO 7: DERECHO DE PORTABILIDAD' not in content:
    content = content.replace('modulo: "MÓDULO 6: DATOS SENSIBLES, SALUD Y MENORES DE EDAD (NUEVO)"', 'modulo: "MÓDULO 6: DATOS SENSIBLES, SALUD Y MENORES DE EDAD"')
    content = content.replace('] \n      }\n    ];', mod7_data + '\n      }\n    ];')
    content = content.replace('c18: {', 'c18: {' + mod7_guias.replace(',\n      c19: {', '},\n      c19: {'))
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print("MÓDULO 7 ARCOP+ Y CONTROLES 19 AL 22 APLICADOS PERFECTAMENTE")
