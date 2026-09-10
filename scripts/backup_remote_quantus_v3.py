import subprocess

cmd = """expect -c '
set timeout 120
spawn ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no root@100.117.44.3
expect "password:"
send "felipe123\\r"
expect "~#"
send "pct exec 100 -- tar -czf /tmp/quantus_prod_backup.tar.gz --exclude=backups --exclude=node_modules -C /opt/quantus .\\r"
expect "~#"
send "pct exec 100 -- ls -lh /tmp/quantus_prod_backup.tar.gz\\r"
expect "~#"
send "exit\\r"
expect eof' """

res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print(res.stdout)
