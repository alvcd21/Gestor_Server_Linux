import paramiko
import psutil
from models import Server, SystemMetrics, db
from datetime import datetime
import paramiko
from models import db, SystemMetrics, Server
from flask import Blueprint
from flask_login import current_user


monitoring_bp = Blueprint("monitoring", __name__, url_prefix="/monitoring")

def get_remote_metrics(server):
    """Conecta a un servidor remoto vía SSH y obtiene métricas del sistema y procesos."""
    metrics = {
        "cpu": None,
        "memory": None,
        "disk": None,
        "system_info": {},
        "processes": [],
        "error": None
    }

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=server.ip_address,
            username=server.username,
            password=server.password
        )

        # Obtener métricas
        stdin, stdout, stderr = ssh.exec_command("top -bn1 | grep '%Cpu'")
        cpu_line = stdout.read().decode().strip()
        if cpu_line:
            cpu_usage = float(cpu_line.split()[1].replace(",", "."))  # Ajusta según el formato
            metrics["cpu"] = cpu_usage

        stdin, stdout, stderr = ssh.exec_command("free | grep Mem")
        mem_line = stdout.read().decode().strip().split()
        if mem_line:
            total = float(mem_line[1])
            used = float(mem_line[2])
            metrics["memory"] = (used / total) * 100

        stdin, stdout, stderr = ssh.exec_command("df / | tail -1")
        disk_line = stdout.read().decode().strip().split()
        if disk_line:
            metrics["disk"] = float(disk_line[4].replace('%', '').replace(",", "."))

        # Información del sistema
        system_info = {}
        commands = {
            "platform": "uname -s",
            "version": "uname -v",
            "processor": "uname -p",
            "architecture": "uname -m",
            "hostname": "hostname"
        }
        for key, cmd in commands.items():
            stdin, stdout, stderr = ssh.exec_command(cmd)
            system_info[key] = stdout.read().decode().strip()
        metrics["system_info"] = system_info

        # Obtener procesos activos
        stdin, stdout, stderr = ssh.exec_command("ps -eo pid,comm,user,%cpu,%mem --sort=-%mem | head -n 10")
        process_lines = stdout.read().decode().strip().split("\n")[1:]  # omitir encabezado
        processes = []
        for line in process_lines:
            parts = line.split()
            if len(parts) >= 5:
                processes.append({
                    "pid": parts[0],
                    "name": parts[1],
                    "user": parts[2],
                    "cpu": parts[3],
                    "memory": parts[4]
                })
        metrics["processes"] = processes

        ssh.close()

    except Exception as e:
        metrics["error"] = str(e)

    return metrics




def record_all_servers_metrics():
    with app.app_context():

        servers = Server.query.all()
        if not servers:
            print("⚠️ No hay servidores registrados.")
            return

        for server in servers:
            try:
                # Inicializar cliente SSH
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(
                    hostname=server.ip_address,
                    username=server.username,
                    password=server.password,
                    timeout=5
                )


                # 🔸 Obtener CPU (extraído del comando `top`)
                stdin, stdout, stderr = client.exec_command("top -bn1 | grep 'Cpu(s)'")
                cpu_raw = stdout.read().decode()
                if not cpu_raw.strip():
                    raise Exception("No se pudo obtener datos de CPU.")
                cpu_idle = float(cpu_raw.split('%')[0].split()[-1])
                cpu_usage = round(100 - cpu_idle, 2)

                # 🔸 Obtener Memoria (comando `free`)
                stdin, stdout, stderr = client.exec_command("free | grep Mem")
                mem_raw = stdout.read().decode().split()
                if len(mem_raw) < 3:
                    raise Exception("No se pudo obtener datos de Memoria.")
                mem_total = int(mem_raw[1])
                mem_used = int(mem_raw[2])
                mem_usage = round((mem_used / mem_total) * 100, 2)

                # 🔸 Obtener Disco (comando `df`)
                stdin, stdout, stderr = client.exec_command("df -h / | tail -1")
                disk_raw = stdout.read().decode().split()
                if len(disk_raw) < 5:
                    raise Exception("No se pudo obtener datos de Disco.")
                disk_usage = float(disk_raw[4].replace('%', ''))

                # 🔸 Guardar en la base de datos
                metric = SystemMetrics(
                    timestamp=datetime.utcnow(),
                    cpu_usage=cpu_usage,
                    memory_usage=mem_usage,
                    disk_usage=disk_usage,
                    server_id=server.id
                )
                db.session.add(metric)
                db.session.commit()
                print(f"✅ Métricas registradas para servidor: {server.name} ({server.ip_address})")

                client.close()

            except Exception as e:
                print(f"❌ Error al obtener métricas del servidor {server.name} ({server.ip_address}): {e}")
