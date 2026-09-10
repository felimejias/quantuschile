import urllib.request
import json
import time

# Obtener lista de páginas desde Chrome DevTools Protocol local
try:
    req = urllib.request.urlopen("http://127.0.0.1:9222/json")
    pages = json.loads(req.read().decode('utf-8'))
    print("PÁGINAS ABIERTAS EN CHROME:", len(pages))
    for p in pages:
        print(" -", p.get('title'), "->", p.get('url'))
except Exception as e:
    print("Error consultando CDP:", e)
