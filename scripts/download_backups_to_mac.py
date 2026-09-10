import subprocess

cmd = """expect -c '
set timeout 300
spawn scp -o StrictHostKeyChecking=no -o PubkeyAuthentication=no root@100.117.44.3:/tmp/quantus_prod_backup.tar.gz /Users/felipe/proyectos/quantuschile.cl/do/00_estrategia/
expect "password:"
send "felipe123\\r"
expect eof' """

res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print(res.stdout)

cmd_pg = """expect -c '
set timeout 300
spawn scp -o StrictHostKeyChecking=no -o PubkeyAuthentication=no root@100.117.44.3:/tmp/quantus_pg_docker_dump.sql /Users/felipe/proyectos/quantuschile.cl/do/00_estrategia/
expect "password:"
send "felipe123\\r"
expect eof' """

res_pg = subprocess.run(cmd_pg, shell=True, capture_output=True, text=True)
print(res_pg.stdout)
