import subprocess
import os

print("=== DEPLOYING APP.PY TO LXC 100 (100.117.44.3) ===")

base_dir = "/Users/felipe/proyectos/quantuschile.cl/do"
local_path = os.path.join(base_dir, "app.py")

with open(local_path, "r", encoding="utf-8") as f:
    content = f.read()

tmp_file = "/tmp/deploy_app.py"
with open(tmp_file, "w", encoding="utf-8") as f:
    f.write(content)

# Prepare template
tpl_local = os.path.join(base_dir, "templates", "admin_radar_total.html")
tpl_tmp = "/tmp/admin_radar_total.html"
with open(tpl_local, "r", encoding="utf-8") as f:
    tpl_content = f.read()
with open(tpl_tmp, "w", encoding="utf-8") as f:
    f.write(tpl_content)

# 1. SCP to host 100.117.44.3
scp_cmd = """expect -c '
set timeout 30
spawn scp -o StrictHostKeyChecking=no -o PubkeyAuthentication=no /tmp/deploy_app.py /tmp/admin_radar_total.html root@100.117.44.3:/tmp/
expect "password:"
send "felipe123\\r"
expect eof'"""
res_scp = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)
print("SCP Output:", res_scp.stdout[:200])

# 2. Push into LXC container 100 and restart
ssh_cmd = """expect -c '
set timeout 30
spawn ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no root@100.117.44.3
expect "password:"
send "felipe123\\r"
expect "~#"
send "pct push 100 /tmp/deploy_app.py /opt/quantus/portal/app.py\\r"
expect "~#"
send "pct push 100 /tmp/deploy_app.py /opt/quantus/app.py\\r"
expect "~#"
send "pct push 100 /tmp/admin_radar_total.html /opt/quantus/portal/templates/admin_radar_total.html\\r"
expect "~#"
send "pct exec 100 -- pkill -f python3\\r"
expect "~#"
send "pct exec 100 -- systemctl restart quantus 2>/dev/null || true\\r"
expect "~#"
send "exit\\r"
expect eof'"""
res_ssh = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)
print("SSH/PCT Output:", res_ssh.stdout)

print("=== DEPLOY COMPLETED SUCCESSFULLY ===")
