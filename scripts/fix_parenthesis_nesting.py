path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/checklist_ley21719.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Corrección de paréntesis: incluir la frase completa con sus paréntesis DENTRO de la etiqueta tooltip-term para que no queden sueltos fuera del link
new_questions_js = '''    const questions = [
      {
        id: 1,
        text: '1. ¿Cuentas con un <span class="tooltip-term">RAT (Registro de Actividades de Tratamiento)<span class="tooltip-text"><span class="tooltip-title">📜 ¿Qué es el RAT?</span>Es un documento u orden oficial exigido por ley donde anotas todas las listas, planillas Excel o cuadernos donde guardas nombres, RUTs o teléfonos de clientes.</span></span> de las bases de datos de tus clientes y empleados?',
        yesText: "Sí, documentado",
        noText: "No / No estoy seguro"
      },
      {
        id: 2,
        text: '2. ¿Dispones de un portal o formulario en tu web para responder solicitudes de borrado o acceso (<span class="tooltip-term">Derechos ARCO<span class="tooltip-text"><span class="tooltip-title">🛡️ ¿Qué son los Derechos ARCO?</span>Son las siglas de Acceso, Rectificación, Cancelación y Oposición. Es el derecho legal del cliente a pedir que borren su número o le muestren qué datos tienen de él.</span></span>) en menos de 10 días hábiles?',
        yesText: "Sí, automatizado",
        noText: "No / Solo correo general"
      },
      {
        id: 3,
        text: '3. ¿Tienes la evidencia criptográfica (IP, fecha y <span class="tooltip-term">Hash SHA-256<span class="tooltip-text"><span class="tooltip-title">🔐 ¿Qué es el HASH SHA-256?</span>Es como una huella digital matemática e inalterable. Transforma la firma del cliente en un código de seguridad que demuestra ante un juez la fecha y hora exacta en que dio permiso.</span></span>) de los permisos que te dieron tus clientes actuales?',
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
        text: '5. En caso de archivadores en papel, ¿tienes inventario etiquetado y protocolo de <span class="tooltip-term">Trituración Física (DIN P-4)<span class="tooltip-text"><span class="tooltip-title">✂️ Trituración DIN P-4</span>Proceso de romper documentos viejos en trozos minúsculos para que nadie pueda leerlos en la basura al vencer los 6 años tributarios.</span></span> a los 6 años?',
        yesText: "Sí, etiquetados y con seguro",
        noText: "No, están sin seguro"
      },
      {
        id: 6,
        text: '6. Si tratas <span class="tooltip-term">Datos Sensibles o de Menores (Art. 14° y 32°)<span class="tooltip-text"><span class="tooltip-title">🏥 Datos Sensibles y Menores</span>Son datos de salud, fichas médicas, huellas o fotos de niños menores de 14 años. La ley exige el consentimiento escrito del apoderado o representante legal.</span></span> de Salud o Colegios, ¿tienes la firma del apoderado?',
        yesText: "Sí, firmado por escrito",
        noText: "No, sin permiso explícito"
      },
      {
        id: 7,
        text: '7. ¿Cuentas con un <span class="tooltip-term">Protocolo de Brechas (3 Horas)<span class="tooltip-text"><span class="tooltip-title">🚨 Protocolo de Brechas (3 Horas)</span>Plan de emergencia obligatoria bajo la Ley 21.663 para avisar al gobierno en menos de 3 horas si un hacker roba o filtra un computador con datos.</span></span> para avisar al gobierno en menos de 3 horas si sufres un hackeo?',
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

start_q = content.find('const questions = [')
end_q = content.find('const answers = {};')

if start_q != -1 and end_q != -1:
    content = content[:start_q] + new_questions_js + '\n\n    ' + content[end_q:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("PARENTESIS CORREGIDOS Y UNIFICADOS DENTRO DE LOS TOOLTIPS")
else:
    print("No se encontró questions")
