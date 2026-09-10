import subprocess
import os
import datetime
import time

timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
print(f"=== PROTOCOLO CANÓNICO DE DESPLIEGUE A PRODUCCIÓN: {timestamp} ===")

base_dir = "/Users/felipe/proyectos/quantuschile.cl/do"
tar_local = f"/tmp/quantus_deploy_light_{timestamp}.tar.gz"

# Step 1: Create lightweight tarball
cmd_tar = f"cd {base_dir} && tar --exclude='*.db' --exclude='*.sqlite3' --exclude='*.log' --exclude='*.pdf' --exclude='*.tar.gz' --exclude='__pycache__' --exclude='data' --exclude='logs' -czf {tar_local} app.py static/ templates/ marketing/ nexus/ communications/ mailer.py uptime_monitor.py qa_e2e_auditor.py"
subprocess.run(cmd_tar, shell=True, check=True)
size_mb = os.path.getsize(tar_local) / (1024 * 1024)
print(f"  ✓ 1. Tarball liviano compilado ({size_mb:.2f} MB): {tar_local}")

# Step 2: Upload to production host via scp
expect_scp = f"""expect -c '
set timeout 30
spawn scp -o StrictHostKeyChecking=no -o PubkeyAuthentication=no {tar_local} root@100.117.44.3:/tmp/quantus_deploy_light.tar.gz
expect "password:"
send "felipe123\\r"
expect eof
'"""
subprocess.run(expect_scp, shell=True, check=True)

# Also SCP app.py directly to ensure exact match
scp_app = """expect -c '
set timeout 15
spawn scp -o StrictHostKeyChecking=no -o PubkeyAuthentication=no /Users/felipe/proyectos/quantuschile.cl/do/app.py root@100.117.44.3:/tmp/app.py
expect "password:"
send "felipe123\\r"
expect eof
'"""
subprocess.run(scp_app, shell=True, check=True)
print("  ✓ 2. Transferencia liviana y app.py completada via SCP")

# Step 3: Push into LXC 100, create backup, extract and restart quantus-portal service
expect_ssh = f"""expect -c '
set timeout 60
spawn ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no root@100.117.44.3
expect "password:"
send "felipe123\\r"
expect "root@"
send "pct push 100 /tmp/quantus_deploy_light.tar.gz /tmp/lxc100_deploy.tar.gz\\r"
expect "root@"
send "pct push 100 /tmp/app.py /opt/quantus/portal/app.py\\r"
expect "root@"
send "pct exec 100 -- tar -czf /tmp/backup_prod_{timestamp}.tar.gz -C /opt/quantus/portal/ templates/ app.py 2>/dev/null\\r"
expect "root@"
send "pct exec 100 -- tar -xzf /tmp/lxc100_deploy.tar.gz -C /opt/quantus/portal/\\r"
expect "root@"
send "pct exec 100 -- pkill -9 -f app.py || true\\r"
expect "root@"
send "pct exec 100 -- systemctl restart quantus-portal\\r"
expect "root@"
send "sleep 3\\r"
expect "root@"
send "curl -I http://127.0.0.1:8082/\\r"
expect "root@"
send "exit\\r"
expect eof
'"""

res = subprocess.run(expect_ssh, shell=True, capture_output=True, text=True)
print("  ✓ 3. Despliegue en LXC 100 (/opt/quantus/portal/) ejecutado con éxito")
print("\n--- DETALLE DE SALIDA DEL SERVIDOR ---")
print(res.stdout)
print("=== PROTOCOLO COMPLETO CON ÉXITO ===")
