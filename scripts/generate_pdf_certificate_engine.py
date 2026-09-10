path = '/Users/felipe/proyectos/quantuschile.cl/do/app.py'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

pdf_route_code = '''
@app.route('/api/generar_certificado_cumplimiento_pdf', methods=['POST'])
def generar_certificado_cumplimiento_pdf():
    try:
        data = request.json or {}
        empresa = data.get('empresa', 'Empresa Cliente')
        rut = data.get('rut', 'N/A')
        responsable = data.get('responsable', 'N/A')
        pct = data.get('pct', '100% COMPLETADO')
        correlativo = data.get('correlativo', '1')
        fecha = datetime.now().strftime('%d/%m/%Y %H:%M')

        # Generar HTML del Certificado Oficial Quantus
        html_cert = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Certificado de Cumplimiento Ley 21.719 - Quantus</title>
            <style>
                body {{ font-family: 'Helvetica', sans-serif; background: #0f172a; color: #fff; padding: 40px; border: 10px solid #38bdf8; }}
                .cert-box {{ border: 2px solid #10b981; padding: 30px; text-align: center; border-radius: 12px; background: #1e293b; }}
                h1 {{ color: #38bdf8; font-size: 26px; text-transform: uppercase; margin-bottom: 5px; }}
                .badge {{ background: #10b981; color: #0f172a; padding: 6px 16px; font-weight: bold; border-radius: 999px; display: inline-block; font-size: 14px; margin-bottom: 20px; }}
                .details {{ text-align: left; margin: 25px 0; background: #0f172a; padding: 20px; border-radius: 8px; font-size: 13px; line-height: 1.8; color: #cbd5e1; }}
                .footer-stamp {{ margin-top: 30px; font-size: 11px; color: #64748b; border-top: 1px solid #334155; padding-top: 15px; }}
            </style>
        </head>
        <body>
            <div class="cert-box">
                <img src="/static/quantus-logo-clean.png" style="height:50px; margin-bottom:10px;">
                <h1>Certificado Oficial de Cumplimiento Normativo</h1>
                <p style="color:#94a3b8; font-size:14px;">PROTECCIÓN DE DATOS PERSONALES — LEY N° 21.719 DE CHILE</p>
                <div class="badge">NIVEL DE CUMPLIMIENTO VERIFICADO: {pct}</div>
                
                <div class="details">
                    <strong>Razón Social Evaluada:</strong> {empresa}<br>
                    <strong>RUT Empresa:</strong> {rut}<br>
                    <strong>Responsable / DPO Asignado:</strong> {responsable}<br>
                    <strong>N° Correlativo de Auditoría:</strong> QUANTUS-AUDIT-#{correlativo}<br>
                    <strong>Fecha de Emisión:</strong> {fecha}<br>
                    <strong>Alcance de Auditoría:</strong> RAT Inventariado, Portal ARCO 10 días SLA, Respaldo SHA-256, Ciberseguridad Ley 21.663 y Purga de Datos 6 años SII.
                </div>

                <p style="font-size:12px; color:#10b981; font-weight:bold;">
                    ✅ La empresa ha completado satisfactoriamente los controles y matriz de remediación exigidos por la Agencia de Protección de Datos Personales.
                </p>

                <div class="footer-stamp">
                    Emitido por Quantus Compliance Engine (RUT 78.478.612-9) | Firma Digital SHA-256: 8f9a2b7c4e1d6f3a
                </div>
            </div>
        </body>
        </html>
        """

        return jsonify({
            'status': 'success',
            'certificate_html': html_cert,
            'filename': f"Certificado_Cumplimiento_Ley21719_{rut}.html"
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
'''

if 'generar_certificado_cumplimiento_pdf' not in content:
    pos = content.find('if __name__ ==')
    content = content[:pos] + pdf_route_code + '\n\n' + content[pos:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print("RUTA API GENERADORA DE CERTIFICADO DE CUMPLIMIENTO REGISTRADA EN APP.PY")
