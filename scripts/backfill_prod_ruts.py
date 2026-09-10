import sqlite3
import re
import unicodedata

def clean_rut(rut):
    if not rut:
        return ""
    rut = unicodedata.normalize('NFKD', str(rut))
    return re.sub(r'[^0-9kK]', '', rut).upper()

def run_backfill():
    db_path = "/opt/quantus/portal/data/do_historico.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    pattern = re.compile(r'\b\d{1,2}(?:\.?\d{3}){2}\s*[\-\–\—]?\s*[0-9kK]\b|\b\d{7,8}\s*[\-\–\—]?\s*[0-9kK]\b')

    total_updated = 0
    while True:
        rows = cur.execute("SELECT id, texto FROM publicaciones WHERE clean_rut IS NULL LIMIT 10000").fetchall()
        if not rows:
            break
        print(f"Procesando lote de {len(rows)} publicaciones...", flush=True)
        batch_data = []
        for row_id, text in rows:
            if text:
                found = pattern.findall(text)
                if found:
                    batch_data.append((clean_rut(found[0]), row_id))
        
        if batch_data:
            cur.executemany("UPDATE publicaciones SET clean_rut = ? WHERE id = ?", batch_data)
            conn.commit()
            total_updated += len(batch_data)
            print(f" -> Lote guardado. Total RUTs extraídos: {total_updated}", flush=True)
        else:
            cur.execute("UPDATE publicaciones SET clean_rut = '' WHERE clean_rut IS NULL")
            conn.commit()
            break

    conn.close()
    print(f"=== BACKFILL FINALIZADO: {total_updated} publicaciones indexadas por RUT ===", flush=True)

if __name__ == "__main__":
    run_backfill()
