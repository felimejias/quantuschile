import subprocess

cmd = """expect -c '
set timeout 45
spawn ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no root@100.117.44.3
expect "password:"
send "felipe123\\r"
expect "~#"
send "pct exec 100 -- bash -c \\"docker exec quantus-postgres pg_dumpall -U postgres > /tmp/quantus_pg_docker.sql\\"\\r"
expect "~#"
send "pct exec 100 -- ls -lh /tmp/quantus_pg_docker.sql\\r"
expect "~#"
send "exit\\r"
expect eof' """

res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print(res.stdout)
