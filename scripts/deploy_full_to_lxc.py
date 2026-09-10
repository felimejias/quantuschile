import subprocess
import os

print("=== DEPLOYING APP & MARKETING MODULE TO HOST 100.117.44.3 ===")

base_dir = "/Users/felipe/proyectos/quantuschile.cl/do"

# 1. Sync marketing folder and templates via rsync or tar over scp
tar_cmd = f"cd {base_dir} && tar -czf /tmp/marketing_deploy.tar.gz app.py marketing/ templates/marketing/"
subprocess.run(tar_cmd, shell=True, check=True)

# 2. SCP tarball to host 100.117.44.3
scp_cmd = """expect -c '
set timeout 30
spawn scp -o StrictHostKeyChecking=no -o PubkeyAuthentication=no /tmp/marketing_deploy.tar.gz root@100.117.44.3:/tmp/
expect "password:"
send "felipe123\\r"
expect eof'"""
subprocess.run(scp_cmd, shell=True, check=True)

# 3. Unpack in /mnt/proyectos/felipe/inapi_portal/ and restart gunicorn
ssh_cmd = """expect -c '
set timeout 30
spawn ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no root@100.117.44.3
expect "password:"
send "felipe123\\r"
expect "~#"
send "tar -xzf /tmp/marketing_deploy.tar.gz -C /mnt/proyectos/felipe/inapi_portal/\\r"
expect "~#"
send "pkill -9 -f gunicorn || true\\r"
expect "~#"
send "cd /mnt/proyectos/felipe/inapi_portal && nohup /usr/bin/python3 /usr/local/bin/gunicorn --workers 3 --bind 0.0.0.0:8082 app:app > /tmp/gunicorn_8082.log 2>&1 &\\r"
expect "~#"
send "sleep 2 && ss -tlpn | grep 8082\\r"
expect "~#"
send "exit\\r"
expect eof'"""
res = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)
print(res.stdout)
print("=== DEPLOY COMPLETED SUCCESSFULLY ===")
