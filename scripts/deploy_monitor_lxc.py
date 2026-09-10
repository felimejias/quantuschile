import subprocess
import os

print("=== SINCRONIZANDO MONITOR DO A /opt/quantus/portal/ EN LXC 100 ===")

files = [
    ("do_personas_monitor.py", "/opt/quantus/portal/do_personas_monitor.py"),
    ("do_historico.py", "/opt/quantus/portal/do_historico.py"),
    ("do_ediciones.py", "/opt/quantus/portal/do_ediciones.py"),
    ("app.py", "/opt/quantus/portal/app.py"),
    ("billing_monitor.py", "/opt/quantus/portal/billing_monitor.py"),
    ("templates/partials/nav_header.html", "/opt/quantus/portal/templates/partials/nav_header.html"),
    ("templates/quantus_intelligence.html", "/opt/quantus/portal/templates/quantus_intelligence.html"),
    ("templates/index.html", "/opt/quantus/portal/templates/index.html"),
    ("templates/vigilancia_do.html", "/opt/quantus/portal/templates/vigilancia_do.html"),
    ("templates/como_funciona.html", "/opt/quantus/portal/templates/como_funciona.html"),
    ("templates/seguridad_confianza.html", "/opt/quantus/portal/templates/seguridad_confianza.html"),
]

base_dir = "/Users/felipe/proyectos/quantuschile.cl/do"

for local_rel, remote_path in files:
    local_path = os.path.join(base_dir, local_rel)
    if not os.path.exists(local_path):
        print(f"No existe: {local_path}")
        continue
    with open(local_path, "r", encoding="utf-8") as f:
        content = f.read()

    tmp_file = f"/tmp/deploy_{os.path.basename(local_rel)}"
    with open(tmp_file, "w", encoding="utf-8") as f:
        f.write(content)

    subprocess.run([
        "expect", "-c",
        f"spawn scp -o StrictHostKeyChecking=no -o PubkeyAuthentication=no {tmp_file} root@100.117.44.3:/tmp/\n"
        "expect \"password:\"\n"
        "send \"felipe123\\r\"\n"
        "expect eof"
    ], capture_output=True, text=True)

    subprocess.run([
        "expect", "-c",
        "spawn ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no root@100.117.44.3\n"
        "expect \"password:\"\n"
        "send \"felipe123\\r\"\n"
        "expect \"~#\"\n"
        f"send \"pct push 100 {tmp_file} {remote_path}\\r\"\n"
        "expect \"~#\"\n"
        "send \"exit\\r\"\n"
        "expect eof"
    ], capture_output=True, text=True)

print("Files pushed to /opt/quantus/portal/ successfully!")

# Write remote runner script
remote_runner = """#!/bin/bash
cd /opt/quantus/portal
PY=/usr/bin/python3
LOG=/opt/quantus/portal/logs/do_monitor.log
mkdir -p /opt/quantus/portal/logs /opt/quantus/portal/data
echo "[$(date '+%Y-%m-%d %H:%M:%S')] === INICIO monitor DO (Servidor LXC 100) ===" >> "$LOG"
"$PY" do_personas_monitor.py >> "$LOG" 2>&1
echo "[$(date '+%Y-%m-%d %H:%M:%S')] === FIN monitor DO (exit $?) ===" >> "$LOG"
"""
with open("/tmp/run_do_monitor_remote.sh", "w", encoding="utf-8") as f:
    f.write(remote_runner)

subprocess.run([
    "expect", "-c",
    "spawn scp -o StrictHostKeyChecking=no -o PubkeyAuthentication=no /tmp/run_do_monitor_remote.sh root@100.117.44.3:/tmp/\n"
    "expect \"password:\"\n"
    "send \"felipe123\\r\"\n"
    "expect eof"
], capture_output=True, text=True)

subprocess.run([
    "expect", "-c",
    "spawn ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no root@100.117.44.3\n"
    "expect \"password:\"\n"
    "send \"felipe123\\r\"\n"
    "expect \"~#\"\n"
    "send \"pct push 100 /tmp/run_do_monitor_remote.sh /opt/quantus/portal/scripts/run_do_monitor_remote.sh\\r\"\n"
    "expect \"~#\"\n"
    "send \"pct exec 100 -- chmod +x /opt/quantus/portal/scripts/run_do_monitor_remote.sh\\r\"\n"
    "expect \"~#\"\n"
    "send \"exit\\r\"\n"
    "expect eof"
], capture_output=True, text=True)

# Install cron in container pointing to /opt/quantus/portal/scripts/run_do_monitor_remote.sh
with open("/tmp/do_cron.txt", "w", encoding="utf-8") as f:
    f.write("5 */2 * * * /bin/bash /opt/quantus/portal/scripts/run_do_monitor_remote.sh\n")

subprocess.run([
    "expect", "-c",
    "spawn scp -o StrictHostKeyChecking=no -o PubkeyAuthentication=no /tmp/do_cron.txt root@100.117.44.3:/tmp/\n"
    "expect \"password:\"\n"
    "send \"felipe123\\r\"\n"
    "expect eof"
], capture_output=True, text=True)

res = subprocess.run([
    "expect", "-c",
    "spawn ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no root@100.117.44.3\n"
    "expect \"password:\"\n"
    "send \"felipe123\\r\"\n"
    "expect \"~#\"\n"
    "send \"pct push 100 /tmp/do_cron.txt /tmp/do_cron.txt\\r\"\n"
    "expect \"~#\"\n"
    "send \"pct exec 100 -- crontab /tmp/do_cron.txt\\r\"\n"
    "expect \"~#\"\n"
    "send \"pct exec 100 -- crontab -l\\r\"\n"
    "expect \"~#\"\n"
    "send \"exit\\r\"\n"
    "expect eof"
], capture_output=True, text=True)

print(res.stdout)
