path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/checklist_ley21719.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# CSS Premium para Tooltips Flotantes estilo Glassmorphism Dark Mode
tooltip_css = '''
    /* Estilo Premium Glassmorphism para Notas Flotantes (Tooltips) */
    .tooltip-term {
      position: relative;
      display: inline-block;
      color: #38bdf8;
      font-weight: 800;
      border-bottom: 1.5px dashed #38bdf8;
      cursor: help;
    }
    .tooltip-term .tooltip-text {
      visibility: hidden;
      width: 260px;
      background: rgba(15, 23, 42, 0.95);
      color: #f1f5f9;
      text-align: left;
      border-radius: 12px;
      padding: 12px 14px;
      position: absolute;
      z-index: 9999;
      bottom: 125%;
      left: 50%;
      transform: translateX(-50%);
      opacity: 0;
      transition: opacity 0.25s ease, transform 0.25s ease;
      font-size: 11px;
      font-weight: 400;
      line-height: 1.5;
      border: 1px solid rgba(56, 189, 248, 0.4);
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.8), 0 0 15px rgba(56, 189, 248, 0.2);
      backdrop-filter: blur(10px);
      pointer-events: none;
    }
    .tooltip-term .tooltip-text::after {
      content: "";
      position: absolute;
      top: 100%;
      left: 50%;
      margin-left: -6px;
      border-width: 6px;
      border-style: solid;
      border-color: #0f172a transparent transparent transparent;
    }
    .tooltip-term:hover .tooltip-text {
      visibility: visible;
      opacity: 1;
      transform: translateX(-50%) translateY(-4px);
    }
    .tooltip-title {
      font-weight: 800;
      color: #38bdf8;
      margin-bottom: 4px;
      display: block;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
'''

content = content.replace('</style>', tooltip_css + '\n  </style>')

# Preguntas actualizadas con acrónimos entre paréntesis y notas flotantes (Tooltips)
new_questions_js = '''    const questions = [
      {
        id: 1,
        text: '1. ¿Cuentas con un <span class="tooltip-term">RAT (Registro de Actividades de Tratamiento)<span class="tooltip-text"><span class="tooltip-title">📜 ¿Qué es el RAT?</span>Es un documento u orden oficial exigido por ley donde anotas todas las listas, planillas Excel o cuadernos donde guardas nombres, RUTs o teléfonos de clientes.</span></span> de las bases de datos de tus clientes y empleados?',
        yesText: "Sí, documentado",
        noText: "No / No estoy seguro"
      },
      {
        id: 2,
        text: '2. ¿Dispones de un portal o formulario en tu web para responder solicitudes de borrado o acceso (<span class="tooltip-term">Derechos ARCO)<span class="tooltip-text"><span class="tooltip-title">🛡️ ¿Qué son los Derechos ARCO?</span>Son las siglas de Acceso, Rectificación, Cancelación y Oposición. Es el derecho legal del cliente a pedir que borren su número o le muestren qué datos tienen de él.</span></span> en menos de 10 días hábiles?',
        yesText: "Sí, automatizado",
        noText: "No / Solo correo general"
      },
      {
        id: 3,
        text: '3. ¿Tienes la evidencia criptográfica (IP, fecha y <span class="tooltip-term">Hash SHA-256)<span class="tooltip-text"><span class="tooltip-title">🔐 ¿Qué es el HASH SHA-256?</span>Es como una huella digital matemática e inalterable. Transforma la firma del cliente en un código de seguridad que demuestra ante un juez la fecha y hora exacta en que dio permiso.</span></span>) de los permisos que te dieron tus clientes actuales?',
        yesText: "Sí, respaldado",
        noText: "No, solo casillas en formularios antiguos"
      },
      {
        id: 4,
        text: '4. ¿Los formularios de tu web tienen la casilla de <span class="tooltip-term">Aceptación Expresa<span class="tooltip-text"><span class="tooltip-title">☑️ Aceptación Expresa</span>Significa que el cliente debe marcar la casilla con su propia mano. Está prohibido por ley que el tick azul venga marcado automáticamente.</span></span> desmarcada por defecto?',
        yesText: "Sí, desmarcada por defecto",
        noText: "No, viene marcada"
      },
      {
        id: 5,
        text: '5. En caso de archivadores en papel, ¿tienes inventario etiquetado y protocolo de <span class="tooltip-term">Trituración Física<span class="tooltip-text"><span class="tooltip-title">✂️ Trituración DIN P-4</span>Proceso de romper documentos viejos en trozos minúsculos para que nadie pueda leerlos en la basura al vencer los 6 años tributarios.</span></span> a los 6 años?',
        yesText: "Sí, etiquetados y con seguro",
        noText: "No, están sin seguro"
      },
      {
        id: 6,
        text: '6. Si tratas <span class="tooltip-term">Datos Sensibles<span class="tooltip-text"><span class="tooltip-title">🏥 Datos Sensibles y Menores</span>Son datos de salud, fichas médicas, huellas o fotos de niños menores de 14 años. La ley exige el consentimiento escrito del apoderado o representante legal.</span></span> de Salud o de Menores (Art. 14° y 32°), ¿tienes la firma del apoderado?',
        yesText: "Sí, firmado por escrito",
        noText: "No, sin permiso explícito"
      },
      {
        id: 7,
        text: '7. ¿Cuentas con un <span class="tooltip-term">Protocolo de Brechas<span class="tooltip-text"><span class="tooltip-title">🚨 Protocolo de Brechas (3 Horas)</span>Plan de emergencia obligatoria bajo la Ley 21.663 para avisar al gobierno en menos de 3 horas si un hacker roba o filtra un computador con datos.</span></span> para avisar al gobierno en menos de 3 horas si sufres un hackeo?',
        yesText: "Sí, protocolo activo",
        noText: "No / No existe manual"
      },
      {
        id: 8,
        text: '8. Si tienes cámaras de seguridad, ¿tienes instalados los carteles informativos visibles de <span class="tooltip-term">Videovigilancia<span class="tooltip-text"><span class="tooltip-title">🎥 Cartel de Videovigilancia</span>Señalética obligatoria en las entradas que avisa a clientes y trabajadores que están siendo grabados por motivos de seguridad.</span></span> exigidos por ley?',
        yesText: "Sí, letreros instalados",
        noText: "No, sin señalética"
      }
    ];'''

pos = content.find('const questions = [')
pos_end = content.find('const answers = {};')

if pos != -1 and pos_end != -1:
    content = content[:pos] + new_questions_js + '\n\n    ' + content[pos_end:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("NOTAS FLOTANTES (TOOLTIPS PREMIUM) INTEGRADAS CON ÉXITO EN EL CHECKLIST PÚBLICO")
else:
    print("No se encontró la constante questions")
