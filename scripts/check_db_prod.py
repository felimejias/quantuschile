import sqlite3
import os

dbs = [
    "/opt/quantus/portal/do_historico.db",
    "/opt/quantus/portal/do_intelligence.sqlite3",
    "/opt/quantus/portal/data/do_historico.db"
]

for db_path in dbs:
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in c.fetchall()]
        print(f"[{db_path}] Tables: {tables}")
        for t in tables:
            try:
                c.execute(f"SELECT count(*) FROM {t}")
                cnt = c.fetchone()[0]
                print(f"   Table {t}: {cnt} rows")
            except Exception as e:
                print(f"   Table {t}: Error {e}")
    else:
        print(f"[{db_path}] Not found")
