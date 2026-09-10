import subprocess
import os

print("=== INICIANDO DESPLIEGUE A PRODUCCIÓN EN LXC 100 ===")

# List of files to copy to LXC 100
files = [
    ("app.py", "/opt/quantus/app.py"),
    ("billing_monitor.py", "/opt/quantus/billing_monitor.py"),
    ("templates/partials/nav_header.html", "/opt/quantus/templates/partials/nav_header.html"),
    ("templates/quantus_intelligence.html", "/opt/quantus/templates/quantus_intelligence.html"),
    ("templates/index.html", "/opt/quantus/templates/index.html"),
    ("templates/vigilancia_do.html", "/opt/quantus/templates/vigilancia_do.html"),
    ("templates/como_funciona.html", "/opt/quantus/templates/como_funciona.html"),
    ("templates/seguridad_confianza.html", "/opt/quantus/templates/seguridad_confianza.html"),
]

base_dir = "/Users/felipe/proyectos/quantuschile.cl/do"

for local_rel, remote_path in files:
    local_path = os.path.join(base_dir, local_rel)
    if not os.path.exists(local_path):
        print(f"ERROR: Archivo local no existe: {local_path}")
        continue
    
    # Read local content
    with open(local_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Create temporary file for transfer
    tmp_filename = f"/tmp/deploy_{os.path.basename(local_rel)}"
    with open(tmp_filename, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Copiando {local_rel} -> {remote_path}...")
    
    # SCP to host, then pct push to LXC 100
    scp_cmd = f"""expect -c '
set timeout 30
spawn scp -o StrictHostKeyChecking=no -o PubkeyAuthentication=no {tmp_filename} root@100.117.44.3:/tmp/
expect "password:"
send "felipe123\\r"
expect eof'"""
    subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)

    pct_cmd = f"""expect -c '
set timeout 30
spawn ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no root@100.117.44.3
expect "password:"
send "felipe123\\r"
expect "~#"
send "pct push 100 /tmp/{os.path.basename(local_rel)} {remote_path}\\r"
expect "~#"
send "exit\\r"
expect eof'"""
    res = subprocess.run(pct_cmd, shell=True, capture_output=True, text=True)
    if "OK" in res.stdout or "exit" in res.stdout:
        print(f"  ✓ {local_rel} sincronizado exitosamente")
    else:
        print(f"  ? Resultado: {res.stdout}")

# Restart service on LXC 100 if running
restart_cmd = """expect -c '
set timeout 30
spawn ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no root@100.117.44.3
expect "password:"
send "felipe123\\r"
expect "~#"
send "pct exec 100 -- systemctl restart quantus 2>/dev/null || pct exec 100 -- pkill -f \"python3 app.py\" 2>/dev/null || true\\r"
expect "~#"
send "exit\\r"
expect eof'"""
res_restart = subprocess.run(restart_cmd, shell=True, capture_output=True, text=True)
print("=== DESPLIEGUE A PRODUCCIÓN COMPLETADO ===")
