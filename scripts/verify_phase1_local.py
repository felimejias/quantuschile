import urllib.request
import urllib.parse
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

base_url = "http://127.0.0.1:8084"
routes_to_test = [
    ("/", "Portada Principal www.quantuschile.cl"),
    ("/do", "Radar Diario Oficial (/do)"),
    ("/ley21.719", "Guía Ley 21.719 (/ley21.719)"),
    ("/maestros", "Centro Maestro Redirect (/maestros)"),
    ("/checklist-ley-21719", "Test Diagnóstico Público Ley 21.719")
]

print("=== VERIFICACIÓN EMPÍRICA LOCAL DE FASE 1 (MAC LOCALHOST:8084) ===")
all_ok = True
for route, name in routes_to_test:
    url = base_url + route
    try:
        req = urllib.request.urlopen(url, timeout=5)
        status = req.status
        content_length = len(req.read())
        print(f"✅ [200 OK] {name} -> {route} ({content_length} bytes)")
    except Exception as e:
        print(f"❌ [ERROR] {name} -> {route}: {e}")
        all_ok = False

if all_ok:
    print("\n🎉 TODAS LAS RUTAS DE LA FASE 1 RESPONDEN 100% CORRECTAS EN LOCALHOST:8084")
else:
    print("\n⚠️ SE DETECTARON RUTAS CON ERRORES.")
