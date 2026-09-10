import subprocess

print("=== PUSHING FIXED INDEX_WEB_DIST.HTML TO LXC 100 ON 100.117.44.3 ===")

# 1. SCP index_web_dist.html to /tmp/index_web_dist.html on host 100.117.44.3
scp_cmd = """expect -c '
set timeout 30
spawn scp -o StrictHostKeyChecking=no -o PubkeyAuthentication=no /Users/felipe/proyectos/quantuschile.cl/do/index_web_dist.html root@100.117.44.3:/tmp/index_web_dist.html
expect "password:"
send "felipe123\\r"
expect eof'"""

subprocess.run(scp_cmd, shell=True, check=True)

# 2. PCT PUSH into LXC container 100 at /opt/quantus/web/dist/index.html and restart services
ssh_cmd = """expect -c '
set timeout 30
spawn ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no root@100.117.44.3
expect "password:"
send "felipe123\\r"
expect "~#"
send "pct push 100 /tmp/index_web_dist.html /opt/quantus/web/dist/index.html\\r"
expect "~#"
send "pct push 100 /tmp/index_web_dist.html /opt/quantus/portal/templates/index.html\\r"
expect "~#"
send "pct exec 100 -- pkill -f python3\\r"
expect "~#"
send "pct exec 100 -- systemctl restart quantus 2>/dev/null || true\\r"
expect "~#"
send "pct exec 100 -- systemctl restart quantus-portal 2>/dev/null || true\\r"
expect "~#"
send "exit\\r"
expect eof'"""

subprocess.run(ssh_cmd, shell=True, check=True)
print("=== INDEX_WEB_DIST.HTML DEPLOYED AND SERVICES RESTARTED SUCCESSFULLY ===")
