import subprocess

remote_runner = """#!/bin/bash
cd /opt/quantus/portal
export PYTHONPATH=/opt/quantus/portal:$PYTHONPATH
PY=/opt/quantus-venv/bin/python3
LOG=/opt/quantus/portal/logs/do_monitor.log
mkdir -p /opt/quantus/portal/logs /opt/quantus/portal/data
echo "[$(date '+%Y-%m-%d %H:%M:%S')] === INICIO monitor DO (Servidor LXC 100) ===" >> "$LOG"
"$PY" do_personas_monitor.py >> "$LOG" 2>&1
echo "[$(date '+%Y-%m-%d %H:%M:%S')] === FIN monitor DO (exit $?) ===" >> "$LOG"
"""
with open("/tmp/run_do_monitor_remote.sh", "w", encoding="utf-8") as f:
    f.write(remote_runner)

delivery_runner = """#!/bin/bash
cd /opt/quantus/portal
export PYTHONPATH=/opt/quantus/portal:$PYTHONPATH
PY=/opt/quantus-venv/bin/python3
LOG=/opt/quantus/portal/logs/delivery_health.log
mkdir -p /opt/quantus/portal/logs
echo "[$(date '+%Y-%m-%d %H:%M:%S')] === INICIO despacho 08:30 AM ===" >> "$LOG"
"$PY" -c "from communications.retry_worker import run_retries; run_retries()" >> "$LOG" 2>&1
"$PY" -c "from communications.delivery_health import alert_if_issues; alert_if_issues()" >> "$LOG" 2>&1
echo "[$(date '+%Y-%m-%d %H:%M:%S')] === FIN despacho 08:30 AM ===" >> "$LOG"
"""
with open("/tmp/run_delivery_health_remote.sh", "w", encoding="utf-8") as f:
    f.write(delivery_runner)

subprocess.run([
    "expect", "-c",
    "spawn scp -o StrictHostKeyChecking=no -o PubkeyAuthentication=no /tmp/run_do_monitor_remote.sh /tmp/run_delivery_health_remote.sh root@100.117.44.3:/tmp/\n"
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
    "send \"pct push 100 /tmp/run_do_monitor_remote.sh /opt/quantus/portal/scripts/run_do_monitor_remote.sh\\r\"\n"
    "expect \"~#\"\n"
    "send \"pct exec 100 -- chmod +x /opt/quantus/portal/scripts/run_do_monitor_remote.sh\\r\"\n"
    "expect \"~#\"\n"
    "send \"pct push 100 /tmp/run_delivery_health_remote.sh /opt/quantus/portal/scripts/run_delivery_health_remote.sh\\r\"\n"
    "expect \"~#\"\n"
    "send \"pct exec 100 -- chmod +x /opt/quantus/portal/scripts/run_delivery_health_remote.sh\\r\"\n"
    "expect \"~#\"\n"
    "send \"exit\\r\"\n"
    "expect eof"
], capture_output=True, text=True)

print(res.stdout)
