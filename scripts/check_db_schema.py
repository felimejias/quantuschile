import sqlite3

db_path = "/opt/quantus/portal/data/do_historico.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("PRAGMA table_info(publicaciones);")
cols = [r[1] for r in c.fetchall()]
print("Columns in publicaciones table:", cols)

c.execute("SELECT * FROM publicaciones LIMIT 1;")
row = c.fetchone()
print("Sample row:", row)
