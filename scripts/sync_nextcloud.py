#!/usr/bin/env python3

import subprocess
import os
import datetime
from pathlib import Path

# Set up log file
timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
logfile = f'/var/log/nextcloud_backup.log'

def log(message):
    log_message = f"{datetime.datetime.now().isoformat()}: {message}"
    with open(logfile, 'a') as log_file:
        log_file.write(log_message + '\n')
    print(log_message)

def main():
    log("===========----------------------==========")
    log("          backup nextcloud         ")
    log("===========----------------------==========")
    log("Iniciando o script de backup/sync...")

    # Remote SSH Alias
    remote_ssh_alias = "srv-prod"

    # Start backup process
    log("Iniciando novo backup a quente do Nextcloud")

    # Dump the database
    log("Copiando o banco de dados...")
    subprocess.run(["sudo", "-u", "postgres", "psql", "-c", "DROP DATABASE nextcloud_db"])
    subprocess.run(["sudo", "-u", "postgres", "psql", "-c", "CREATE DATABASE nextcloud_db"])
    #subprocess.run(["ssh", remote_ssh_alias, "sudo", "-u", "postgres", "pg_dump", "-d", "nextcloud_db", "-C", "-c", "-Fc", "|", "sudo", "-u", "postgres", "pg_restore", "-d", "nextcloud_db"])
    subprocess.run(f"ssh {remote_ssh_alias} sudo -u postgres pg_dump -d nextcloud_db -C -c -Fc | sudo -u postgres pg_restore -d nextcloud_db", shell=True)

    # Copy Nextcloud application files
    log("Realizando copia dos arquivos da aplicacao Nextcloud...")
    subprocess.run(["rsync", "-az", "--delete", "--stats", "-h", f"{remote_ssh_alias}:/var/www/nextcloud/", "/var/www/nextcloud"])

    # Copy user data
    log("Realizando copia dos Dados de usuarios...")
    subprocess.run(["rsync", "-az", "--delete", "--stats", "-h", f"{remote_ssh_alias}:/mnt/ncdata/", "/mnt/ncdata"])

    # Copy Let's Encrypt certificates
    log("Realizando copia de certificados...")
    subprocess.run(["rsync", "-az", "--delete", "--stats", "-h", f"{remote_ssh_alias}:/etc/letsencrypt/", "/etc/letsencrypt"])

    # Copy Apache configurations
    log("Realizando copia de configuracao do apache...")
    subprocess.run(["rsync", "-az", "--delete", "--stats", "-h", f"{remote_ssh_alias}:/etc/apache2/", "/etc/apache2"])

    # Change database password
    new_db_password = subprocess.check_output(["php", "-r", "include '/var/www/nextcloud/config/config.php'; echo $CONFIG['dbpassword'];"]).decode().strip()
    log("Reconfigurando a conexao com o banco...")
    subprocess.run(["sudo", "-u", "postgres", "psql", "-c", f"ALTER ROLE nextcloud_db_user WITH PASSWORD '{new_db_password}'"])

    # Change Redis password
    new_redis_password = subprocess.check_output(["php", "-r", "include '/var/www/nextcloud/config/config.php'; echo $CONFIG['redis']['password'];"]).decode().strip()
    log("Configurando a conexao com o redis...")
    with open("/etc/redis/redis.conf", "r") as redis_conf_file:
        lines = redis_conf_file.readlines()
    with open("/etc/redis/redis.conf", "w") as redis_conf_file:
        for line in lines:
            if "requirepass" in line:
                redis_conf_file.write(f"requirepass {new_redis_password}\n")
            else:
                redis_conf_file.write(line)

    subprocess.run(["systemctl", "restart", "redis-server"])

    mail_script = Path(os.curdir).joinpath('send_email.py')
    if mail_script.exists():
        subprocess.run(["python3", mail_script.absolute()])


    log("Finalizado o backup do nextcloud")

if __name__ == "__main__":
    main()

