path = '/Users/felipe/proyectos/quantuschile.cl/do/app.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

pos = content.find("def checklist_ley21719")
if pos != -1:
    pos_end = content.find("if __name__ ==")
    head = content[:pos]
    tail = content[pos_end:]
    
    clean_route = '''def checklist_ley21719():
    return render_template('checklist_ley21719.html')

@app.route('/api/cancelar_suscripcion_y_borrar_datos', methods=['POST'])
@csrf.exempt
def api_cancelar_suscripcion_y_borrar_datos():
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), "01_diario_oficial"))
    from data_lifecycle_engine import ejecutar_cancelacion_y_purga_ley21719
    
    data = request.get_json(silent=True) or request.form or {}
    rut_o_email = (data.get('rut') or data.get('email') or '').strip()
    motivo = (data.get('motivo') or 'Solicitud por Derecho ARCO de Supresión').strip()
    
    if not rut_o_email:
        return jsonify({'status': 'error', 'message': 'Debes ingresar tu RUT o Email para procesar la cancelación.'}), 400
        
    resultado = ejecutar_cancelacion_y_purga_ley21719(rut_o_email, motivo)
    return jsonify(resultado), 200

'''
    with open(path, 'w', encoding='utf-8') as f:
        f.write(head + clean_route + tail)

print("ROUTE CLEANED AND RE-WRITTEN PRECISELY")
