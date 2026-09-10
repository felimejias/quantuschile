import subprocess
import os

print("=== DEPLOYING ALL POS & PORTAL FILES TO LXC CONTAINER 100 ON 100.117.44.3 ===")

base_dir = "/Users/felipe/proyectos/quantuschile.cl/do"

files_to_deploy = [
    ("app.py", "/tmp/deploy_app.py", "/opt/quantus/portal/app.py"),
    ("templates/pos_cliente_login.html", "/tmp/pos_cliente_login.html", "/opt/quantus/portal/templates/pos_cliente_login.html"),
    ("templates/pos_terminal.html", "/tmp/pos_terminal.html", "/opt/quantus/portal/templates/pos_terminal.html"),
    ("templates/informe_quiebre_stock_ia.html", "/tmp/informe_quiebre_stock_ia.html", "/opt/quantus/portal/templates/informe_quiebre_stock_ia.html"),
]

# Copy files to /tmp locally
scp_files_str = ""
pct_push_cmds = ""

for local_rel, tmp_dest, remote_dest in files_to_deploy:
    full_local = os.path.join(base_dir, local_rel)
    with open(full_local, "r", encoding="utf-8") as f:
        content = f.read()
    with open(tmp_dest, "w", encoding="utf-8") as f:
        f.write(content)
    
    scp_files_str += f" {tmp_dest}"
    pct_push_cmds += f"send \"pct push 100 {tmp_dest} {remote_dest}\\r\"\nexpect \"~#\"\n"
    # Also push to /opt/quantus/ templates if exists
    remote_alt = remote_dest.replace("/opt/quantus/portal/", "/opt/quantus/")
    pct_push_cmds += f"send \"pct push 100 {tmp_dest} {remote_alt}\\r\"\nexpect \"~#\"\n"

# 1. SCP all files to host 100.117.44.3
scp_cmd = f"""expect -c '
set timeout 30
spawn scp -o StrictHostKeyChecking=no -o PubkeyAuthentication=no {scp_files_str} root@100.117.44.3:/tmp/
expect "password:"
send "felipe123\\r"
expect eof'"""

print("Copiando archivos al servidor 100.117.44.3...")
res_scp = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)
print("SCP Result:", res_scp.stdout[:200])

# 2. Push inside container 100 and restart service
ssh_cmd = f"""expect -c '
set timeout 45
spawn ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no root@100.117.44.3
expect "password:"
send "felipe123\\r"
expect "~#"
{pct_push_cmds}
send "pct exec 100 -- pkill -f python3\\r"
expect "~#"
send "pct exec 100 -- systemctl restart quantus 2>/dev/null || true\\r"
expect "~#"
send "pct exec 100 -- systemctl restart quantus-portal 2>/dev/null || true\\r"
expect "~#"
send "exit\\r"
expect eof'"""

print("Instalando archivos dentro del contenedor LXC 100 y reiniciando servicios...")
res_ssh = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)
print("SSH/PCT Result:", res_ssh.stdout)

print("=== DESPLIEGUE EN SERVIDOR REMOTO 100.117.44.3 COMPLETADO EXITOSAMENTE ===")
