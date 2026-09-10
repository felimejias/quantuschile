import subprocess

service_content = """[Unit]
Description=Quantus Portal Web Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/quantus/portal
Environment="PORT=8082"
Environment="PYTHONPATH=/opt/quantus/portal"
ExecStart=/opt/quantus-venv/bin/python3 /opt/quantus/portal/app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""

with open("/tmp/quantus-portal.service", "w", encoding="utf-8") as f:
    f.write(service_content)

# SCP service file to host
subprocess.run([
    "expect", "-c",
    "spawn scp -o StrictHostKeyChecking=no -o PubkeyAuthentication=no /tmp/quantus-portal.service root@100.117.44.3:/tmp/\n"
    "expect \"password:\"\n"
    "send \"felipe123\\r\"\n"
    "expect eof"
], capture_output=True, text=True)

# Push inside LXC 100 and enable systemd service
res = subprocess.run([
    "expect", "-c",
    "spawn ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no root@100.117.44.3\n"
    "expect \"password:\"\n"
    "send \"felipe123\\r\"\n"
    "expect \"~#\"\n"
    "send \"pct push 100 /tmp/quantus-portal.service /etc/systemd/system/quantus-portal.service\\r\"\n"
    "expect \"~#\"\n"
    "send \"pct exec 100 -- systemctl daemon-reload\\r\"\n"
    "expect \"~#\"\n"
    "send \"pct exec 100 -- systemctl enable quantus-portal\\r\"\n"
    "expect \"~#\"\n"
    "send \"pct exec 100 -- systemctl restart quantus-portal\\r\"\n"
    "expect \"~#\"\n"
    "send \"pct exec 100 -- systemctl status quantus-portal --no-pager\\r\"\n"
    "expect \"~#\"\n"
    "send \"exit\\r\"\n"
    "expect eof"
], capture_output=True, text=True)

print(res.stdout)
