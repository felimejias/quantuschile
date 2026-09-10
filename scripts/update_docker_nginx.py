import subprocess

print("=== UPDATING DOCKER NGINX CONFIGURATION ON LXC 100 ===")

update_script = """
with open('/etc/nginx/conf.d/default.conf', 'r') as f:
    text = f.read()

target = 'location ~ ^/(registro|payment|gracias_suscripcion'
replacement = 'location ~ ^/(pos|pos_terminal|clientes|informe-quiebre-stock-ia|app|registro|payment|gracias_suscripcion'

if target in text:
    text = text.replace(target, replacement)
    with open('/etc/nginx/conf.d/default.conf', 'w') as f:
        f.write(text)
    print("Updated default.conf successfully.")
else:
    print("Target string not found or already updated.")
"""

with open("/tmp/update_nginx.py", "w", encoding="utf-8") as f:
    f.write(update_script)

scp_cmd = """expect -c '
set timeout 30
spawn scp -o StrictHostKeyChecking=no -o PubkeyAuthentication=no /tmp/update_nginx.py root@100.117.44.3:/tmp/
expect "password:"
send "felipe123\\r"
expect eof'"""

subprocess.run(scp_cmd, shell=True, check=True)

ssh_cmd = """expect -c '
set timeout 30
spawn ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no root@100.117.44.3
expect "password:"
send "felipe123\\r"
expect "~#"
send "pct push 100 /tmp/update_nginx.py /tmp/update_nginx.py\\r"
expect "~#"
send "pct exec 100 -- docker cp /tmp/update_nginx.py quantus-nginx:/tmp/update_nginx.py\\r"
expect "~#"
send "pct exec 100 -- docker exec quantus-nginx python3 /tmp/update_nginx.py 2>/dev/null || pct exec 100 -- docker exec quantus-nginx sh -c \"sed -i \\\"s/registro|payment/pos|pos_terminal|clientes|informe-quiebre-stock-ia|app|registro|payment/g\\\" /etc/nginx/conf.d/default.conf\"\\r"
expect "~#"
send "pct exec 100 -- docker exec quantus-nginx nginx -t\\r"
expect "~#"
send "pct exec 100 -- docker exec quantus-nginx nginx -s reload\\r"
expect "~#"
send "exit\\r"
expect eof'"""

subprocess.run(ssh_cmd, shell=True, check=True)
print("=== DOCKER NGINX RE-ROUTING COMPLETED SUCCESSFULLY ===")
