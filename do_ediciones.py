import os
import re
import json
import time
import datetime
import unicodedata

import requests
from pypdf import PdfReader

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EDICIONES_DIR = os.path.join(BASE_DIR, "data", "do_ediciones")
ESTADO_FILE = os.path.join(EDICIONES_DIR, "estado.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "application/pdf,text/html;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-CL,es;q=0.9",
}

SECCIONES = {
    "01": "Normas Generales",
    "02": "Normas Particulares",
    "03": "Publicaciones Judiciales",
    "04": "Avisos Destacados",
    "05": "Empresas y Cooperativas",
    "06": "Marcas y Patentes",
    "07": "Boletín Oficial de Minería",
}
NOMBRE_SECCION_A_ROMANO = {
    "Normas Generales": "I",
    "Normas Particulares": "II",
    "Publicaciones Judiciales": "III",
    "Avisos Destacados": "IV",
    "Empresas y Cooperativas": "V",
    "Marcas y Patentes": "VI",
    "Boletín Oficial de Minería": "VII",
}
ROMANO_A_CARPETA = {"I": "01", "II": "02", "III": "03", "IV": "04", "V": "05", "VI": "06", "VII": "07"}


def normalizar(texto):
    texto = texto or ""
    norm = unicodedata.normalize("NFKD", texto)
    norm = "".join(ch for ch in norm if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", norm).strip().upper()


class BloqueoWAF(Exception):
    """El firewall del Diario Oficial bloqueo la IP (Connection reset).
    La corrida debe abortar y reintentar en la proxima ejecucion del cron."""


_SESSION = None
_FALLOS_CONSECUTIVOS = [0]


def _sesion():
    global _SESSION
    if _SESSION is None:
        _SESSION = requests.Session()
        _SESSION.headers.update(HEADERS)
    return _SESSION


def _contar_fallo(es_red):
    if es_red:
        _FALLOS_CONSECUTIVOS[0] += 1
        if _FALLOS_CONSECUTIVOS[0] >= 4:
            raise BloqueoWAF("4 fallos de red consecutivos: WAF bloqueando la IP.")
    else:
        _FALLOS_CONSECUTIVOS[0] = 0


def descargar_pdf(url, destino=None, reintentos=3):
    for intento in range(1, reintentos + 1):
        try:
            r = _sesion().get(url, headers=HEADERS, timeout=(10, 30), stream=True)
            chunks = []
            total = 0
            for chunk in r.iter_content(65536):
                chunks.append(chunk)
                total += len(chunk)
                if total > 30 * 1024 * 1024:
                    break
            r.close()
            data = b"".join(chunks)
            if data[:4] == b"%PDF":
                _contar_fallo(False)
                if destino:
                    with open(destino, "wb") as f:
                        f.write(data)
                    return destino
                return data
            _contar_fallo(False)
        except Exception as exc:
            es_red = isinstance(exc, (requests.exceptions.ConnectionError, ConnectionResetError))
            print(f"  [do_ediciones] Error descargando {url}: {str(exc)[:70]}", flush=True)
            _contar_fallo(es_red)
        time.sleep(1.5 * intento + 0.2)
    return None


def _ultimos_dias_utiles(fecha_iso, n):
    dias = []
    d = datetime.date.fromisoformat(fecha_iso)
    while len(dias) < n:
        d -= datetime.timedelta(days=1)
        if d.weekday() <= 5:
            dias.append(d.isoformat())
    return sorted(dias)


def _dias_utiles_entre(fecha_a_iso, fecha_b_iso):
    a = datetime.date.fromisoformat(fecha_a_iso)
    b = datetime.date.fromisoformat(fecha_b_iso)
    if b <= a:
        return 0
    count = 0
    d = a + datetime.timedelta(days=1)
    while d <= b:
        if d.weekday() <= 5:
            count += 1
        d += datetime.timedelta(days=1)
    return count


def cargar_estado():
    if os.path.exists(ESTADO_FILE):
        try:
            with open(ESTADO_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"fecha": "2026-07-30", "edicion": 44512}


def guardar_estado(fecha_iso, edicion):
    os.makedirs(EDICIONES_DIR, exist_ok=True)
    with open(ESTADO_FILE, "w", encoding="utf-8") as f:
        json.dump({"fecha": fecha_iso, "edicion": edicion}, f, indent=2)


def _url_sumario(fecha_iso, edicion):
    y, m, d = fecha_iso.split("-")
    return f"https://www.diariooficial.interior.gob.cl/publicaciones/{y}/{m}/{d}/sumarios/{edicion}.pdf"


def _url_articulo(fecha_iso, edicion, carpeta, cve):
    y, m, d = fecha_iso.split("-")
    return f"https://www.diariooficial.interior.gob.cl/publicaciones/{y}/{m}/{d}/{edicion}/{carpeta}/{cve}.pdf"


def descargar_pdf(url, destino=None, reintentos=3):
    for intento in range(1, reintentos + 1):
        try:
            r = _sesion().get(url, headers=HEADERS, timeout=(10, 30), stream=True)
            chunks = []
            total = 0
            for chunk in r.iter_content(65536):
                chunks.append(chunk)
                total += len(chunk)
                if total > 30 * 1024 * 1024:
                    break
            r.close()
            data = b"".join(chunks)
            if data[:4] == b"%PDF":
                _contar_fallo(False)
                if destino:
                    with open(destino, "wb") as f:
                        f.write(data)
                    return destino
                return data
            _contar_fallo(False)
        except Exception as exc:
            es_red = isinstance(exc, (requests.exceptions.ConnectionError, ConnectionResetError, requests.exceptions.Timeout))
            print(f"  [do_ediciones] Error descargando {url}: {str(exc)[:70]}", flush=True)
            _contar_fallo(es_red)
        time.sleep(1.5 * intento + 0.2)
    return None


def _leer_texto_pdf(archivo):
    try:
        reader = PdfReader(archivo)
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception:
        return ""


def _validar_sumario(texto, edicion):
    return bool(texto) and "SUMARIO" in texto.upper() and f"Núm. {edicion}" in texto


def edicion_del_dia(fecha_iso=None):
    fecha_iso = fecha_iso or datetime.date.today().isoformat()
    estado = cargar_estado()
    base_edicion = estado.get("edicion", 44512)
    base_fecha = estado.get("fecha", "2026-07-30")
    diff = _dias_utiles_entre(base_fecha, fecha_iso)
    candidatos = [base_edicion + diff, base_edicion + diff + 1, base_edicion + diff + 2,
                  base_edicion + diff + 3, base_edicion + diff - 1, base_edicion + diff - 2,
                  base_edicion + diff + 4]
    vistos = []
    for edicion in candidatos:
        if edicion in vistos:
            continue
        vistos.append(edicion)
        data = descargar_pdf(_url_sumario(fecha_iso, edicion))
        if data is None:
            continue
        texto = _leer_texto_pdf_rapido(data)
        if _validar_sumario(texto, edicion):
            guardar_estado(fecha_iso, edicion)
            return edicion
        print(f"  [do_ediciones] {fecha_iso}: candidato edicion {edicion} no corresponde")
    return None


def _leer_texto_pdf_rapido(data):
    try:
        reader = PdfReader(__import__("io").BytesIO(data))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception:
        return ""


def _parsear_sumario(texto, fecha_iso, edicion):
    secciones = []
    for nombre in NOMBRE_SECCION_A_ROMANO:
        idx = texto.find(nombre)
        if idx == -1:
            continue
        inicio = idx
        fin = len(texto)
        for otro in NOMBRE_SECCION_A_ROMANO:
            if otro == nombre:
                continue
            pos = texto.find(otro, inicio + len(nombre))
            if pos != -1 and pos < fin:
                fin = pos
        bloque = texto[inicio:fin]
        carpeta = ROMANO_A_CARPETA[NOMBRE_SECCION_A_ROMANO[nombre]]
        lineas = [ln.strip() for ln in bloque.splitlines()]
        for i, linea in enumerate(lineas):
            m = re.search(r"\(CVE:\s*(\d{6,7})\)", linea)
            if not m:
                continue
            cve = m.group(1)
            titulo = ""
            j = i - 1
            while j >= 0 and not titulo:
                candidata = lineas[j]
                if candidata and not re.match(r"^[IVX]+$", candidata):
                    titulo = candidata
                j -= 1
            if re.match(r"^[IVX]+$", titulo.strip()):
                titulo = ""
            secciones.append({
                "fecha": fecha_iso,
                "edicion": edicion,
                "seccion": nombre,
                "carpeta": carpeta,
                "cve": int(cve),
                "titulo": titulo[:300],
            })
    return secciones


def _descargar_articulo(meta, destino=None):
    url = _url_articulo(meta["fecha"], meta["edicion"], meta["carpeta"], meta["cve"])
    data = descargar_pdf(url)
    if data is None:
        for carpeta in sorted(SECCIONES.keys()):
            if carpeta == meta["carpeta"]:
                continue
            url_alt = _url_articulo(meta["fecha"], meta["edicion"], carpeta, meta["cve"])
            data = descargar_pdf(url_alt)
            if data is not None:
                meta["carpeta"] = carpeta
                meta["seccion"] = SECCIONES[carpeta]
                url = url_alt
                break
    if data is None:
        return None
    if destino:
        with open(destino, "wb") as f:
            f.write(data)
    texto = _leer_texto_pdf_rapido(data)
    meta["texto"] = texto
    meta["url"] = url
    meta["bytes"] = len(data)
    return meta


def descargar_edicion(fecha_iso=None, forzar=False, solo_meta=False):
    fecha_iso = fecha_iso or datetime.date.today().isoformat()
    carpeta_dia = os.path.join(EDICIONES_DIR, fecha_iso)
    sumario_path = os.path.join(carpeta_dia, "sumario.pdf")
    index_path = os.path.join(carpeta_dia, "articulos.json")

    if not forzar and os.path.exists(index_path):
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                cache = json.load(f)
            if cache.get("fallidos", 0) == 0:
                return cache
            print(f"[do_ediciones] {fecha_iso}: cache parcial ({cache.get('fallidos')} fallidos) — completando faltantes...", flush=True)
        except Exception:
            pass

    print(f"[do_ediciones] Buscando edicion para {fecha_iso}...")
    edicion = edicion_del_dia(fecha_iso)
    if edicion is None:
        print(f"[do_ediciones] {fecha_iso}: no hay edicion publicada aun (retraso/feriado).")
        return None

    data_sumario = descargar_pdf(_url_sumario(fecha_iso, edicion))
    if data_sumario is None:
        print(f"[do_ediciones] No se pudo bajar el sumario de la edicion {edicion}.")
        return None

    texto_sumario = _leer_texto_pdf_rapido(data_sumario)
    metas = _parsear_sumario(texto_sumario, fecha_iso, edicion)
    print(f"[do_ediciones] Edicion {edicion} ({fecha_iso}): {len(metas)} publicaciones en el sumario.")

    os.makedirs(carpeta_dia, exist_ok=True)
    articulos_dir = os.path.join(carpeta_dia, "articulos")
    os.makedirs(articulos_dir, exist_ok=True)
    with open(sumario_path, "wb") as f:
        f.write(data_sumario)

    articulos = []
    fallidos = 0
    pendientes = []
    for meta in metas:
        destino = os.path.join(articulos_dir, f"{meta['carpeta']}_{meta['cve']}.pdf")
        meta["archivo_pdf"] = destino
        if not forzar and os.path.exists(destino):
            meta["texto"] = _leer_texto_pdf(destino)
            meta["url"] = _url_articulo(fecha_iso, edicion, meta["carpeta"], meta["cve"])
            meta["bytes"] = os.path.getsize(destino)
            articulos.append(meta)
        else:
            pendientes.append(meta)

    def _bajar(meta):
        destino = meta["archivo_pdf"]
        ok = _descargar_articulo(meta, destino=destino)
        if ok is None:
            return None
        return meta

    if pendientes:
        import concurrent.futures
        max_workers = 3
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
            futuros = {pool.submit(_bajar, m): m for m in pendientes}
            for n, fut in enumerate(concurrent.futures.as_completed(futuros), start=1):
                try:
                    res = fut.result()
                except BloqueoWAF:
                    print("[do_ediciones] WAF bloqueando: se aborta la corrida.", flush=True)
                    raise
                if res is None:
                    fallidos += 1
                else:
                    articulos.append(res)
                if n % 25 == 0:
                    print(f"[do_ediciones] ...{n}/{len(pendientes)} articulos", flush=True)
                time.sleep(0.35)

    print(f"[do_ediciones] Edicion {edicion}: {len(articulos)} articulos descargados, {fallidos} fallidos.", flush=True)

    resultado = {
        "fecha": fecha_iso,
        "edicion": edicion,
        "articulos": articulos,
        "descargado_en": datetime.datetime.now().isoformat(),
        "fallidos": fallidos,
    }
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    return resultado


def buscar_terminos(articulos, terminos):
    variantes = []
    for t in terminos:
        t = str(t or "").strip()
        if not t:
            continue
        base = normalizar(t)
        variantes.append(base)
        if re.search(r"\d", t):
            limpio = base.replace(" ", "").replace(".", "").replace("-", "")
            variantes.append(limpio)
            semidig = base.replace(".", "")
            variantes.append(semidig)
    variantes = list(dict.fromkeys([v for v in variantes if v]))
    if not variantes:
        return []
    coincidencias = []
    for art in articulos:
        texto_norm = normalizar(art.get("texto", ""))
        if not texto_norm:
            continue
        encontrados = [v for v in variantes if v in texto_norm]
        if encontrados:
            coincidencias.append({
                "articulo": art,
                "terminos": encontrados,
                "snippet": art.get("texto", "")[:600],
            })
    return coincidencias


if __name__ == "__main__":
    import sys
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    forzar = "--forzar" in sys.argv
    fecha = args[0] if args else None
    res = descargar_edicion(fecha, forzar=forzar)
    if res:
        print(f"OK edicion {res['edicion']} fecha {res['fecha']}: {len(res['articulos'])} articulos, {res['fallidos']} fallidos")
        por_seccion = {}
        for a in res["articulos"]:
            por_seccion[a["seccion"]] = por_seccion.get(a["seccion"], 0) + 1
        for s, n in sorted(por_seccion.items()):
            print(f"  {s}: {n}")
    else:
        print("SIN EDICION (aun no publicada o dia no habil)")
