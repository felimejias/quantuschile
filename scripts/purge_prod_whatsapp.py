import subprocess

py_clean_code = """import sqlite3, os
db_path = '/opt/quantus/portal/data/do_intelligence.sqlite3'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM whatsapp_outbox WHERE status != 'sent'")
        deleted = cur.rowcount
        conn.commit()
        print(f"Prod WhatsApp outbox limpiado: {deleted} mensajes pendientes eliminados.")
    except Exception as e:
        print("Error en limpieza:", e)
    finally:
        conn.close()
else:
    print("No se encontro la BD en:", db_path)
"""

with open("/tmp/clean_whatsapp_prod.py", "w", encoding="utf-8") as f:
    f.write(py_clean_code)

# SCP script to host
subprocess.run([
    "expect", "-c",
    "spawn scp -o StrictHostKeyChecking=no -o PubkeyAuthentication=no /tmp/clean_whatsapp_prod.py root@100.117.44.3:/tmp/\n"
    "expect \"password:\"\n"
    "send \"felipe123\\r\"\n"
    "expect eof"
], capture_output=True, text=True)

# Push to LXC 100 container and execute
res = subprocess.run([
    "expect", "-c",
    "spawn ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no root@100.117.44.3\n"
    "expect \"password:\"\n"
    "send \"felipe123\\r\"\n"
    "expect \"~#\"\n"
    "send \"pct push 100 /tmp/clean_whatsapp_prod.py /tmp/clean_whatsapp_prod.py\\r\"\n"
    "expect \"~#\"\n"
    "send \"pct exec 100 -- python3 /tmp/clean_whatsapp_prod.py\\r\"\n"
    "expect \"~#\"\n"
    "send \"exit\\r\"\n"
    "expect eof"
], capture_output=True, text=True)

print(res.stdout)
