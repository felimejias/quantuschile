import subprocess
import os

base_dir = "/Users/felipe/proyectos/quantuschile.cl/do"
worker_local = os.path.join(base_dir, "remates_radar_worker.py")
worker_tmp = "/tmp/remates_radar_worker.py"

with open(worker_local, "r", encoding="utf-8") as f:
    content = f.read()

with open(worker_tmp, "w", encoding="utf-8") as f:
    f.write(content)

# 1. SCP to host 100.117.44.3
scp_cmd = """expect -c '
set timeout 30
spawn scp -o StrictHostKeyChecking=no -o PubkeyAuthentication=no /tmp/remates_radar_worker.py root@100.117.44.3:/tmp/
expect "password:"
send "felipe123\\r"
expect eof'"""
res_scp = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)
print("SCP:", res_scp.stdout[:200])

# 2. Push to LXC 100 and run
ssh_cmd = """expect -c '
set timeout 60
spawn ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no root@100.117.44.3
expect "password:"
send "felipe123\\r"
expect "~#"
send "pct push 100 /tmp/remates_radar_worker.py /opt/quantus/portal/remates_radar_worker.py\\r"
expect "~#"
send "pct push 100 /tmp/remates_radar_worker.py /opt/quantus/remates_radar_worker.py\\r"
expect "~#"
send "pct exec 100 -- bash -c \\"cd /opt/quantus/portal && mkdir -p data && python3 remates_radar_worker.py --source=all\\"\\r"
expect "~#"
send "exit\\r"
expect eof'"""
res_ssh = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)
print("SSH/PCT Output:", res_ssh.stdout)
