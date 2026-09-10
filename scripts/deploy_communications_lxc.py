import subprocess
import os

base_dir = "/Users/felipe/proyectos/quantuschile.cl/do"
comm_dir = os.path.join(base_dir, "communications")

# Create communications dir on remote LXC 100
subprocess.run([
    "expect", "-c",
    "spawn ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no root@100.117.44.3\n"
    "expect \"password:\"\n"
    "send \"felipe123\\r\"\n"
    "expect \"~#\"\n"
    "send \"pct exec 100 -- mkdir -p /opt/quantus/portal/communications /opt/quantus/portal/communications/templates\\r\"\n"
    "expect \"~#\"\n"
    "send \"exit\\r\"\n"
    "expect eof"
], capture_output=True, text=True)

for root, dirs, files in os.walk(comm_dir):
    for f in files:
        if f.endswith(".py") or f.endswith(".html") or f.endswith(".txt") or f.endswith(".json"):
            local_file = os.path.join(root, f)
            rel_path = os.path.relpath(local_file, base_dir)
            remote_path = f"/opt/quantus/portal/{rel_path}"

            with open(local_file, "r", encoding="utf-8") as fh:
                content = fh.read()

            tmp_file = f"/tmp/deploy_comm_{f}"
            with open(tmp_file, "w", encoding="utf-8") as fh:
                fh.write(content)

            subprocess.run([
                "expect", "-c",
                f"spawn scp -o StrictHostKeyChecking=no -o PubkeyAuthentication=no {tmp_file} root@100.117.44.3:/tmp/\n"
                "expect \"password:\"\n"
                "send \"felipe123\\r\"\n"
                "expect eof"
            ], capture_output=True, text=True)

            subprocess.run([
                "expect", "-c",
                "spawn ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no root@100.117.44.3\n"
                "expect \"password:\"\n"
                "send \"felipe123\\r\"\n"
                "expect \"~#\"\n"
                f"send \"pct push 100 {tmp_file} {remote_path}\\r\"\n"
                "expect \"~#\"\n"
                "send \"exit\\r\"\n"
                "expect eof"
            ], capture_output=True, text=True)

print("Communications module deployed to LXC 100 successfully!")
