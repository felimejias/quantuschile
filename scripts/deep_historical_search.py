import requests
import re
import urllib.parse
from bs4 import BeautifulSoup

def search_ddg(query):
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    data = {"q": query}
    results = []
    try:
        r = requests.post(url, data=data, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.select("a.result__url"):
            href = a.get("href", "")
            title_elem = a.find_parent("div", class_="result__body")
            snippet = ""
            title = ""
            if title_elem:
                snip_elem = title_elem.select_one(".result__snippet")
                title_a = title_elem.select_one(".result__title")
                if snip_elem:
                    snippet = snip_elem.get_text().strip()
                if title_a:
                    title = title_a.get_text().strip()
            
            # Clean URL
            m = re.search(r"uddg=([^&]+)", href)
            clean_url = urllib.parse.unquote(m.group(1)) if m else href
            results.append({
                "title": title,
                "url": clean_url,
                "snippet": snippet
            })
    except Exception as e:
        print("Error en búsqueda DDG:", e)
    return results

queries = [
    '"14.011.762-5" site:diariooficial.interior.gob.cl',
    '"14011762-5" site:diariooficial.interior.gob.cl',
    '"Felipe Esteban Mejias Gonzalez" site:diariooficial.interior.gob.cl',
    '"Felipe Mejias Gonzalez" site:diariooficial.interior.gob.cl',
    '"14.011.762-5"',
    '"14011762-5"',
    '"Felipe Esteban Mejias Gonzalez" "Diario Oficial"',
    '"Felipe Mejias Gonzalez" "Diario Oficial"',
]

print("=== INICIANDO BÚSQUEDA HISTÓRICA PROFUNDA (25 AÑOS) ===")
all_results = []
seen_urls = set()

for q in queries:
    print(f"\nConsultando: {q}")
    res = search_ddg(q)
    for r in res:
        if r["url"] not in seen_urls:
            seen_urls.add(r["url"])
            all_results.append(r)
            print(f" -> Encontrado: {r['title']} | {r['url']}")
            print(f"    Snippet: {r['snippet']}")

print(f"\nTotal resultados únicos encontrados: {len(all_results)}")
