import subprocess

# SCP script to host
subprocess.run([
    "expect", "-c",
    "spawn scp -o StrictHostKeyChecking=no -o PubkeyAuthentication=no /Users/felipe/proyectos/quantuschile.cl/do/scripts/ingesta_historica_background.py root@100.117.44.3:/tmp/\n"
    "expect \"password:\"\n"
    "send \"felipe123\\r\"\n"
    "expect eof"
], capture_output=True, text=True)

# Push to container and set executable
res = subprocess.run([
    "expect", "-c",
    "spawn ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no root@100.117.44.3\n"
    "expect \"password:\"\n"
    "send \"felipe123\\r\"\n"
    "expect \"~#\"\n"
    "send \"pct push 100 /tmp/ingesta_historica_background.py /opt/quantus/portal/scripts/ingesta_historica_background.py\\r\"\n"
    "expect \"~#\"\n"
    "send \"pct exec 100 -- chmod +x /opt/quantus/portal/scripts/ingesta_historica_background.py\\r\"\n"
    "expect \"~#\"\n"
    "send \"exit\\r\"\n"
    "expect eof"
], capture_output=True, text=True)

print(res.stdout)
