import subprocess

script_content = """#!/bin/bash
cd /opt/quantus
PY=/usr/bin/python3
LOG=/opt/quantus/logs/do_monitor.log
echo "[$(date '+%Y-%m-%d %H:%M:%S')] === INICIO monitor DO (Servidor LXC 100) ===" >> "$LOG"
"$PY" do_personas_monitor.py >> "$LOG" 2>&1
echo "[$(date '+%Y-%m-%d %H:%M:%S')] === FIN monitor DO (exit $?) ===" >> "$LOG"
"""

tmp_path = "/tmp/run_do_monitor_remote.sh"
with open(tmp_path, "w", encoding="utf-8") as f:
    f.write(script_content)

# 1. SCP to server host
cmd1 = """expect -c '
set timeout 30
spawn scp -o StrictHostKeyChecking=no -o PubkeyAuthentication=no /tmp/run_do_monitor_remote.sh root@100.117.44.3:/tmp/
expect "password:"
send "felipe123\\r"
expect eof'"""
subprocess.run(cmd1, shell=True)

# 2. Push inside LXC 100
cmd2 = """expect -c '
set timeout 30
spawn ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no root@100.117.44.3
expect "password:"
send "felipe123\\r"
expect "~#"
send "pct push 100 /tmp/run_do_monitor_remote.sh /opt/quantus/scripts/run_do_monitor_remote.sh\\r"
expect "~#"
send "pct exec 100 -- chmod +x /opt/quantus/scripts/run_do_monitor_remote.sh\\r"
expect "~#"
send "exit\\r"
expect eof'"""
subprocess.run(cmd2, shell=True)

# 3. Add cron entry inside LXC 100
cmd3 = """expect -c '
set timeout 30
spawn ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no root@100.117.44.3
expect "password:"
send "felipe123\\r"
expect "~#"
send "pct exec 100 -- bash -c \\"(crontab -l 2>/dev/null | grep -v run_do_monitor_remote; echo \\\"5 */2 * * * /bin/bash /opt/quantus/scripts/run_do_monitor_remote.sh\\\") | crontab -\\ font\\r"
expect "~#"
send "pct exec 100 -- crontab -l\\r"
expect "~#"
send "exit\\r"
expect eof'"""
res = subprocess.run(cmd3, shell=True, capture_output=True, text=True)
print(res.stdout)
