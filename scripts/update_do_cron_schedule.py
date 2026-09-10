import subprocess

cron_text = """# Quantus Diario Oficial — Programacion Diaria Oficial
# 1. 07:20 AM: Escaneo y analisis completo del Diario Oficial del dia
20 7 * * * /bin/bash /opt/quantus/portal/scripts/run_do_monitor_remote.sh >> /opt/quantus/portal/logs/cron_scan.log 2>&1

# 2. 08:30 AM: Despacho de comunicaciones y alertas a clientes (tras ventana de pre-revision)
30 8 * * * /bin/bash /opt/quantus/portal/scripts/run_delivery_health_remote.sh >> /opt/quantus/portal/logs/cron_delivery.log 2>&1
"""

with open("/tmp/do_cron_schedule.txt", "w", encoding="utf-8") as f:
    f.write(cron_text)

# Also write remote delivery runner script
delivery_runner = """#!/bin/bash
cd /opt/quantus/portal
PY=/usr/bin/python3
LOG=/opt/quantus/portal/logs/delivery_health.log
mkdir -p /opt/quantus/portal/logs
echo "[$(date '+%Y-%m-%d %H:%M:%S')] === INICIO despacho 08:30 AM ===" >> "$LOG"
"$PY" -c "from communications.retry_worker import run_retries; run_retries()" >> "$LOG" 2>&1
"$PY" -c "from communications.delivery_health import alert_if_issues; alert_if_issues()" >> "$LOG" 2>&1
echo "[$(date '+%Y-%m-%d %H:%M:%S')] === FIN despacho 08:30 AM ===" >> "$LOG"
"""

with open("/tmp/run_delivery_health_remote.sh", "w", encoding="utf-8") as f:
    f.write(delivery_runner)

# SCP to host
subprocess.run([
    "expect", "-c",
    "spawn scp -o StrictHostKeyChecking=no -o PubkeyAuthentication=no /tmp/do_cron_schedule.txt /tmp/run_delivery_health_remote.sh root@100.117.44.3:/tmp/\n"
    "expect \"password:\"\n"
    "send \"felipe123\\r\"\n"
    "expect eof"
], capture_output=True, text=True)

# Push to container and activate
res = subprocess.run([
    "expect", "-c",
    "spawn ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no root@100.117.44.3\n"
    "expect \"password:\"\n"
    "send \"felipe123\\r\"\n"
    "expect \"~#\"\n"
    "send \"pct push 100 /tmp/run_delivery_health_remote.sh /opt/quantus/portal/scripts/run_delivery_health_remote.sh\\r\"\n"
    "expect \"~#\"\n"
    "send \"pct exec 100 -- chmod +x /opt/quantus/portal/scripts/run_delivery_health_remote.sh\\r\"\n"
    "expect \"~#\"\n"
    "send \"pct push 100 /tmp/do_cron_schedule.txt /tmp/do_cron_schedule.txt\\r\"\n"
    "expect \"~#\"\n"
    "send \"pct exec 100 -- crontab /tmp/do_cron_schedule.txt\\r\"\n"
    "expect \"~#\"\n"
    "send \"pct exec 100 -- crontab -l\\r\"\n"
    "expect \"~#\"\n"
    "send \"exit\\r\"\n"
    "expect eof"
], capture_output=True, text=True)

print(res.stdout)
