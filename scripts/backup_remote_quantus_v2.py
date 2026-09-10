import subprocess

cmd = """expect -c '
set timeout 120
spawn ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no root@100.117.44.3
expect "password:"
send "felipe123\\r"
expect "#"
send "pct exec 100 -- bash -lc \\"mkdir -p /opt/quantus/backups/oracle_bundle && cd /opt/quantus && tar -czf /opt/quantus/backups/oracle_bundle/quantus_prod_backup.tar.gz --exclude=backups --exclude=node_modules . && ls -lh /opt/quantus/backups/oracle_bundle/\\"\\r"
expect "#"
send "exit\\r"
expect eof' """

res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print(res.stdout)
