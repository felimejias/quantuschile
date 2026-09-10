path = '/Users/felipe/proyectos/quantuschile.cl/do/templates/checklist_ley21719.html'

html_public_checklist = '''<!DOCTYPE html>
<html lang="es-CL">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Test Diagnóstico Ley N° 21.719 | Quantus Compliance Engine</title>
  <link rel="icon" type="image/png" href="{{ url_for('static', filename='quantus-logo-clean.png') }}">
  <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
  <style>
    :root {
      --bg-dark: #090d16;
      --card-bg: #1e293b;
      --accent-blue: #38bdf8;
      --accent-green: #10b981;
      --accent-red: #ef4444;
      --accent-orange: #f59e0b;
    }
    body { background: var(--bg-dark); color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; padding: 0; margin: 0; }
    .header-bar { background: rgba(15,23,42,0.95); border-bottom: 1px solid rgba(56,189,248,0.2); padding: 14px 24px; position: sticky; top: 0; z-index: 1000; backdrop-filter: blur(10px); display: flex; justify-content: space-between; align-items: center; }
    .container { max-width: 900px; margin: 0 auto; padding: 24px 16px; }
    
    .hero-box { text-align: center; background: radial-gradient(circle at top, rgba(56,189,248,0.15), transparent 70%); border: 1px solid rgba(56,189,248,0.3); border-radius: 20px; padding: 32px 20px; margin-bottom: 28px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
    .hero-title { font-size: 26px; font-weight: 900; color: #fff; margin-bottom: 8px; }
    .hero-sub { font-size: 14px; color: #94a3b8; line-height: 1.6; max-width: 700px; margin: 0 auto 16px auto; }
    
    .btn-pdf-oficial { display: inline-flex; align-items: center; gap: 8px; background: linear-gradient(90deg, #ef4444, #dc2626); color: #fff; text-decoration: none; padding: 10px 20px; border-radius: 12px; font-weight: 900; font-size: 13px; border: 1px solid rgba(255,255,255,0.2); box-shadow: 0 4px 15px rgba(239,68,68,0.4); transition: transform 0.2s; }
    .btn-pdf-oficial:hover { transform: translateY(-2px); }

    .question-card { background: var(--card-bg); border: 1px solid #334155; border-radius: 16px; padding: 20px; margin-bottom: 16px; transition: border-color 0.2s; }
    .question-card.active { border-color: #38bdf8; }
    .q-num { font-size: 11px; font-weight: 800; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
    .q-text { font-size: 15px; font-weight: 700; color: #f8fafc; margin-bottom: 14px; line-height: 1.4; }
    
    .opt-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .btn-opt { background: #0f172a; border: 1px solid #334155; color: #cbd5e1; padding: 12px; border-radius: 10px; font-size: 13px; font-weight: 700; cursor: pointer; text-align: center; transition: all 0.2s; }
    .btn-opt:hover { background: #1e293b; border-color: #38bdf8; color: #fff; }
    .btn-opt.selected-yes { background: rgba(16,185,129,0.2); border-color: #10b981; color: #6ee7b7; }
    .btn-opt.selected-no { background: rgba(239,68,68,0.2); border-color: #ef4444; color: #fca5a5; }

    .result-box { display: none; background: #0f172a; border: 1px solid #38bdf8; border-radius: 20px; padding: 28px 20px; text-align: center; margin-top: 28px; box-shadow: 0 15px 35px rgba(0,0,0,0.7); }
    .score-badge { font-size: 32px; font-weight: 900; color: #ef4444; margin-bottom: 8px; }
  </style>
</head>
<body>

  <header class="header-bar">
    <div style="display:flex; align-items:center; gap:10px;">
      <img src="{{ url_for('static', filename='quantus-logo-clean.png') }}" alt="Quantus" style="height:28px;">
      <span style="font-weight:900; color:#fff; font-size:16px;">QUANTUS <span style="color:#38bdf8;">COMPLIANCE ENGINE</span></span>
    </div>
    
    <a href="/static/ley21719_oficial.pdf" download class="btn-pdf-oficial">
      📄 DESCARGAR LEY N° 21.719 EN PDF OFICIAL BCN (56 PÁGS)
    </a>
  </header>

  <main class="container">

    <div class="hero-box">
      <div class="hero-title">¿Está tu Empresa Lista para la Ley N° 21.719?</div>
      <div class="hero-sub">
        La nueva Ley de Protección de Datos Personales entra en vigencia el <strong>1 de Diciembre de 2026</strong> impositivo multas de hasta <strong>20.000 UTM ($1.300+ millones CLP)</strong>. Responde este test diagnóstico de 8 preguntas clave para evaluar tu nivel de riesgo.
      </div>
      
      <div style="margin-top:12px;">
        <a href="/static/ley21719_oficial.pdf" download class="btn-pdf-oficial" style="background:#0f172a; border:1px solid #38bdf8; color:#38bdf8;">
          📖 Descargar Texto Completo de la Ley N° 21.719 en PDF (Diario Oficial / BCN)
        </a>
      </div>
    </div>

    <div id="quiz-questions-container"></div>

    <div id="result-box" class="result-box">
      <div id="score-badge" class="score-badge">RIESGO CRÍTICO (80%)</div>
      <h3 style="color:#fff; font-size:20px; margin:0 0 10px 0;">Diagnóstico de Cumplimiento Finalizado</h3>
      <p id="result-desc" style="color:#94a3b8; font-size:14px; max-width:600px; margin:0 auto 20px auto; line-height:1.5;"></p>
      
      <div style="display:flex; justify-content:center; gap:12px; flex-wrap:wrap;">
        <a href="/static/ley21719_oficial.pdf" download class="btn-pdf-oficial">📄 Descargar Ley N° 21.719 en PDF</a>
        <a href="https://wa.me/56912345678?text=Hola%20Quantus,%20hice%20el%20test%20diagnóstico%20de%20la%20Ley%2021.719%20y%20necesito%20asesoría%20de%20cumplimiento." target="_blank" style="background:#10b981; color:#0f172a; padding:12px 24px; border-radius:12px; font-weight:900; font-size:13px; text-decoration:none;">💬 Solicitar Auditoría con Quantus</a>
      </div>
    </div>

  </main>

  <script>
    const questions = [
      { id: 1, text: "1. ¿Cuentas con un Registro de Actividades de Tratamiento (RAT) de las bases de datos de tus clientes y empleados?", yesText: "Sí, documentado", noText: "No / No estoy seguro" },
      { id: 2, text: "2. ¿Dispones de un portal o formulario en tu web para responder solicitudes de borrado o acceso (Derechos ARCO) en máximo 10 días hábiles?", yesText: "Sí, automatizado", noText: "No / Solo correo general" },
      { id: 3, text: "3. ¿Tienes la evidencia criptográfica (IP, fecha y Hash SHA-256) de los permisos que te dieron tus clientes actuales?", yesText: "Sí, respaldado", noText: "No, casillas antiguas" },
      { id: 4, text: "4. ¿Los formularios de tu web tienen las casillas de términos desmarcadas por defecto para requerir aceptación explícita?", yesText: "Sí, desmarcadas", noText: "No, vienen marcadas" },
      { id: 5, text: "5. En caso de archivadores en papel, ¿tienes inventario con QR y protocolo de trituración física a los 6 años?", yesText: "Sí, etiquetados y con chapa", noText: "No, están sin seguro" },
      { id: 6, text: "6. Si tratas datos sensibles de Salud o de Menores de Edad (Colegios/Clínicas), ¿tienes la firma explícita del apoderado o tutor legal (Art. 14° y 32°)?", yesText: "Sí, firmado por escrito", noText: "No, sin permiso explícito" },
      { id: 7, text: "7. ¿Cuentas con un Protocolo de Notificación de Brechas para avisar al gobierno en menos de 3 horas si sufres un hackeo?", yesText: "Sí, protocolo activo", noText: "No / No existe manual" },
      { id: 8, text: "8. Si tienes cámaras de seguridad, ¿tienes instalados los carteles informativos visibles de videovigilancia exigidos por ley?", yesText: "Sí, letreros instalados", noText: "No, sin señalética" }
    ];

    const answers = {};

    function renderQuestions() {
      const container = document.getElementById('quiz-questions-container');
      container.innerHTML = '';

      questions.forEach(q => {
        const qDiv = document.createElement('div');
        qDiv.className = 'question-card';
        qDiv.id = `q-box-${q.id}`;
        
        qDiv.innerHTML = `
          <div class="q-num">PREGUNTA ${q.id} DE ${questions.length}</div>
          <div class="q-text">${q.text}</div>
          <div class="opt-grid">
            <button type="button" class="btn-opt" id="btn-yes-${q.id}" onclick="selectAnswer(${q.id}, true)">${q.yesText}</button>
            <button type="button" class="btn-opt" id="btn-no-${q.id}" onclick="selectAnswer(${q.id}, false)">${q.noText}</button>
          </div>
        `;
        container.appendChild(qDiv);
      });
    }

    function selectAnswer(qId, isYes) {
      answers[qId] = isYes;
      
      const btnYes = document.getElementById(`btn-yes-${qId}`);
      const btnNo = document.getElementById(`btn-no-${qId}`);
      const box = document.getElementById(`q-box-${qId}`);

      box.classList.add('active');

      if (isYes) {
        btnYes.className = 'btn-opt selected-yes';
        btnNo.className = 'btn-opt';
      } else {
        btnNo.className = 'btn-opt selected-no';
        btnYes.className = 'btn-opt';
      }

      if (Object.keys(answers).length === questions.length) {
        calcularResultado();
      }
    }

    function calcularResultado() {
      let noCount = 0;
      Object.values(answers).forEach(val => {
        if (!val) noCount++;
      });

      const riskPct = Math.round((noCount / questions.length) * 100);
      const resBox = document.getElementById('result-box');
      const scoreBadge = document.getElementById('score-badge');
      const resDesc = document.getElementById('result-desc');

      resBox.style.display = 'block';
      scoreBadge.innerText = `RIESGO DE MULTAS: ${riskPct}%`;

      if (riskPct > 50) {
        scoreBadge.style.color = '#ef4444';
        resDesc.innerText = `Tu empresa presenta un ALTO RIESGO DE INFRACCIÓN bajo la Ley N° 21.719. Incumples ${noCount} de los 8 controles básicos obligatorios, exponiéndote a multas de hasta 20.000 UTM ($1.300+ millones CLP) y querellas por vulneración de privacidad a partir del 1 de Diciembre de 2026.`;
      } else {
        scoreBadge.style.color = '#f59e0b';
        resDesc.innerText = `Tu empresa cuenta con avances, pero mantiene brechas de cumplimiento activas. Te recomendamos descargar el texto oficial de la Ley N° 21.719 en PDF y agendar una auditoría técnica de remediación con Quantus.`;
      }

      resBox.scrollIntoView({ behavior: 'smooth' });
    }

    window.onload = renderQuestions;
  </script>
</body>
</html>
'''

with open(path, 'w', encoding='utf-8') as f:
    f.write(html_public_checklist)

print("PÁGINA PÚBLICA DE CHECKLIST ACTUALIZADA CON BOTÓN DE DESCARGA PDF DE LA LEY N° 21.719 (56 PÁGS BCN) Y 8 PREGUNTAS CLAVE")
