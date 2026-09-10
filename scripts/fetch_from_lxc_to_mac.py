import subprocess

cmd = """expect -c '
set timeout 300
spawn ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no root@100.117.44.3
expect "password:"
send "felipe123\\r"
expect "~#"
send "pct pull 100 /tmp/quantus_prod_backup.tar.gz /root/quantus_prod_backup.tar.gz\\r"
expect "~#"
send "pct pull 100 /tmp/quantus_pg_docker_dump.sql /root/quantus_pg_docker_dump.sql\\r"
expect "~#"
send "ls -lh /root/quantus_*.gz /root/quantus_*.sql\\r"
expect "~#"
send "exit\\r"
expect eof' """

res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print(res.stdout)

cmd_scp = """expect -c '
set timeout 300
spawn scp -o StrictHostKeyChecking=no -o PubkeyAuthentication=no root@100.117.44.3:/root/quantus_prod_backup.tar.gz /Users/felipe/proyectos/quantuschile.cl/do/00_estrategia/
expect "password:"
send "felipe123\\r"
expect eof' """

subprocess.run(cmd_scp, shell=True, capture_output=True, text=True)

cmd_scp2 = """expect -c '
set timeout 300
spawn scp -o StrictHostKeyChecking=no -o PubkeyAuthentication=no root@100.117.44.3:/root/quantus_pg_docker_dump.sql /Users/felipe/proyectos/quantuschile.cl/do/00_estrategia/
expect "password:"
send "felipe123\\r"
expect eof' """

subprocess.run(cmd_scp2, shell=True, capture_output=True, text=True)
