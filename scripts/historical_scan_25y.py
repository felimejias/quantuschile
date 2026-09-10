import requests
import json
import sqlite3
import os
import re

print("=== AUDITORÍA Y BÚSQUEDA HISTÓRICA PROFUNDA (25 AÑOS - DIARIO OFICIAL) ===")

target_rut_formatted = "14.011.762-5"
target_rut_clean = "14011762-5"
target_rut_digits = "140117625"

names = [
    "Felipe Esteban Mejías González",
    "Felipe Esteban Mejias Gonzalez",
    "Felipe Mejías González",
    "Felipe Mejias Gonzalez",
]

# 1. Check Local & Production SQLite DB
db_files = [
    "/Users/felipe/proyectos/quantuschile.cl/do/data/do_historico.db",
    "/Users/felipe/proyectos/quantuschile.cl/do/data/do_intelligence.sqlite3",
]

local_matches = []

for db_path in db_files:
    if not os.path.exists(db_path):
        continue
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    
    if "publicaciones" in tables:
        # Search publicaciones
        cur = conn.cursor()
        for n in [target_rut_formatted, target_rut_clean, target_rut_digits] + names:
            n_norm = n.upper().replace("Í", "I").replace("Á", "A").replace("É", "E").replace("Ó", "O").replace("Ú", "U")
            rows = cur.execute("SELECT * FROM publicaciones WHERE texto_norm LIKE ?", (f"%{n_norm}%",)).fetchall()
            for r in rows:
                local_matches.append(dict(r))
                
    if "do_ai_reports" in tables:
        cur = conn.cursor()
        for n in [target_rut_formatted, target_rut_clean, target_rut_digits] + names:
            rows = cur.execute("SELECT * FROM do_ai_reports WHERE client_rut LIKE ? OR source_excerpt LIKE ?", (f"%{n}%", f"%{n}%")).fetchall()
            for r in rows:
                local_matches.append(dict(r))
    conn.close()

print(f"Coincidencias en base de datos local: {len(local_matches)}")

# 2. Query DuckDuckGo Lite & HTML search with all variants
search_terms = [
    f'"{target_rut_formatted}"',
    f'"{target_rut_clean}"',
    f'"{names[1]}"',
    f'"{names[3]}"',
    f'site:diariooficial.interior.gob.cl "{target_rut_clean}"',
    f'site:diariooficial.interior.gob.cl "{names[1]}"',
]

web_matches = []

for q in search_terms:
    try:
        r = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": q},
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
            timeout=10
        )
        if "No results." in r.text or "not found" in r.text.lower():
            print(f" -> Busqueda [{q}]: 0 resultados.")
        else:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, "html.parser")
            res_items = soup.select(".result")
            print(f" -> Busqueda [{q}]: {len(res_items)} resultados parciales.")
            for item in res_items:
                title = item.select_one(".result__title")
                snippet = item.select_one(".result__snippet")
                link = item.select_one(".result__url")
                t_text = title.get_text().strip() if title else ""
                s_text = snippet.get_text().strip() if snippet else ""
                l_text = link.get_text().strip() if link else ""
                web_matches.append({"term": q, "title": t_text, "snippet": s_text, "link": l_text})
    except Exception as e:
        print(f"Error buscando {q}: {e}")

print("\n=== RESUMEN DE COINCIDENCIAS HISTÓRICAS ENCONTRADAS ===")
print("Matches locales:", len(local_matches))
print("Matches web externamente indexados:", len(web_matches))

for m in web_matches:
    print(f"\n[Término: {m['term']}]")
    print(f" Título: {m['title']}")
    print(f" Enlace: {m['link']}")
    print(f" Extracto: {m['snippet']}")
