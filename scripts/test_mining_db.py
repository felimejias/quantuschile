import sqlite3

conn = sqlite3.connect("/opt/quantus/portal/data/do_historico.db")
c = conn.cursor()

c.execute("SELECT id, fecha, edicion, seccion, carpeta, cve, titulo FROM publicaciones WHERE carpeta = '07' OR seccion LIKE '%Mineria%' OR seccion LIKE '%mineria%' LIMIT 10;")
rows = c.fetchall()
print(f"Total Mining Articles Found in do_historico.db: {len(rows)}")
for r in rows:
    print(r)
