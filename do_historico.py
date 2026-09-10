import os
import re
import sqlite3
import datetime

from do_ediciones import EDICIONES_DIR, normalizar

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "data", "do_historico.db")

RETENCION_RAW_DIAS = 9


def get_db():
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE, timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS publicaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            edicion INTEGER NOT NULL,
            seccion TEXT NOT NULL,
            carpeta TEXT NOT NULL,
            cve INTEGER NOT NULL,
            url TEXT UNIQUE NOT NULL,
            titulo TEXT,
            texto TEXT,
            texto_norm TEXT,
            bytes_pdf INTEGER,
            creado_utc TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_pub_fecha ON publicaciones(fecha)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_pub_cve ON publicaciones(cve)")
    conn.commit()
    conn.close()


def guardar_publicaciones(articulos):
    init_db()
    conn = get_db()
    ahora = datetime.datetime.utcnow().isoformat()
    insertados = 0
    for a in articulos or []:
        try:
            conn.execute(
                """INSERT OR IGNORE INTO publicaciones
                   (fecha, edicion, seccion, carpeta, cve, url, titulo, texto, texto_norm, bytes_pdf, creado_utc)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    a.get("fecha", ""),
                    a.get("edicion", 0),
                    a.get("seccion", ""),
                    a.get("carpeta", ""),
                    a.get("cve", 0),
                    a.get("url") or f"cve:{a.get('cve', 0)}:{a.get('fecha', '')}",
                    a.get("titulo", ""),
                    a.get("texto", ""),
                    normalizar(a.get("texto", "")),
                    a.get("bytes", 0),
                    ahora,
                ),
            )
            if conn.total_changes > 0:
                insertados += 1
        except sqlite3.IntegrityError:
            continue
    conn.commit()
    conn.close()
    return insertados


def _variantes_normalizadas(terminos):
    variantes = []
    for t in terminos or []:
        t = str(t or "").strip()
        if not t:
            continue
        base = normalizar(t)
        variantes.append(base)
        if re.search(r"\d", t):
            limpio = base.replace(" ", "").replace(".", "").replace("-", "")
            variantes.append(limpio)
    return list(dict.fromkeys([v for v in variantes if v]))


def buscar_historico(terminos, desde=None, hasta=None):
    init_db()
    variantes = _variantes_normalizadas(terminos)
    if not variantes:
        return []
    conn = get_db()
    sql = "SELECT * FROM publicaciones WHERE 1=1"
    params = []
    if desde:
        sql += " AND fecha >= ?"
        params.append(desde)
    if hasta:
        sql += " AND fecha <= ?"
        params.append(hasta)
    sql += " ORDER BY fecha ASC, cve ASC"
    filas = conn.execute(sql, params).fetchall()
    conn.close()
    resultados = []
    for fila in filas:
        texto_norm = fila["texto_norm"] or ""
        encontrados = [v for v in variantes if v in texto_norm]
        if encontrados:
            resultados.append({
                "fecha": fila["fecha"],
                "edicion": fila["edicion"],
                "seccion": fila["seccion"],
                "cve": fila["cve"],
                "url": fila["url"],
                "titulo": fila["titulo"],
                "terminos": encontrados,
                "snippet": (fila["texto"] or "")[:600],
            })
    return resultados


def dias_por_fecha(desde=None, hasta=None):
    init_db()
    conn = get_db()
    sql = "SELECT DISTINCT fecha FROM publicaciones"
    params = []
    if desde:
        sql += " WHERE fecha >= ?"
        params.append(desde)
    if hasta:
        sql += " WHERE fecha <= ?"
        params.append(hasta)
    filas = conn.execute(sql, params).fetchall()
    conn.close()
    return sorted(r["fecha"] for r in filas)


def purgar_raw(retener_dias=RETENCION_RAW_DIAS):
    """Borra los PDFs crudos de ediciones con mas de N dias.
    La base de datos (texto e indice) se conserva para siempre."""
    if not os.path.isdir(EDICIONES_DIR):
        return 0
    corte = datetime.date.today() - datetime.timedelta(days=retener_dias)
    borrados = 0
    for nombre in os.listdir(EDICIONES_DIR):
        if nombre in ("estado.json",):
            continue
        try:
            fecha = datetime.date.fromisoformat(nombre)
        except ValueError:
            continue
        if fecha < corte:
            ruta = os.path.join(EDICIONES_DIR, nombre)
            for root, dirs, files in os.walk(ruta, topdown=False):
                for fn in files:
                    os.remove(os.path.join(root, fn))
                for d in dirs:
                    os.rmdir(os.path.join(root, d))
            os.rmdir(ruta)
            borrados += 1
    return borrados


def resumen():
    init_db()
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM publicaciones").fetchone()[0]
    fechas = conn.execute("SELECT COUNT(DISTINCT fecha) FROM publicaciones").fetchone()[0]
    ultima = conn.execute("SELECT MAX(fecha) FROM publicaciones").fetchone()[0]
    conn.close()
    return {"total_publicaciones": total, "fechas_distintas": fechas, "ultima_fecha": ultima}


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--purgar":
        n = purgar_raw()
        print(f"Purga completada: {n} carpeta(s) de ediciones eliminadas.")
    print(resumen())
