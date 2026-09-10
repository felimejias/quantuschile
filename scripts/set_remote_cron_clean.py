import subprocess

# Write cron file
with open("/tmp/do_cron.txt", "w", encoding="utf-8") as f:
    f.write("5 */2 * * * /bin/bash /opt/quantus/scripts/run_do_monitor_remote.sh\n")

# SCP file to host
subprocess.run([
    "expect", "-c",
    "spawn scp -o StrictHostKeyChecking=no -o PubkeyAuthentication=no /tmp/do_cron.txt root@100.117.44.3:/tmp/\n"
    "expect \"password:\"\n"
    "send \"felipe123\\r\"\n"
    "expect eof"
])

# Push to container and activate crontab
res = subprocess.run([
    "expect", "-c",
    "spawn ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no root@100.117.44.3\n"
    "expect \"password:\"\n"
    "send \"felipe123\\r\"\n"
    "expect \"~#\"\n"
    "send \"pct push 100 /tmp/do_cron.txt /tmp/do_cron.txt\\r\"\n"
    "expect \"~#\"\n"
    "send \"pct exec 100 -- crontab /tmp/do_cron.txt\\r\"\n"
    "expect \"~#\"\n"
    "send \"pct exec 100 -- crontab -l\\r\"\n"
    "expect \"~#\"\n"
    "send \"exit\\r\"\n"
    "expect eof"
], capture_output=True, text=True)

print(res.stdout)
