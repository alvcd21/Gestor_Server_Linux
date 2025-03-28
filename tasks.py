import paramiko
from datetime import datetime
from models import db, Server, SystemMetrics

def record_all_servers_metrics(app):
    """Función para registrar métricas remotas de todos los servidores."""
    with app.app_context():
        servers = Server.query.all()
        for server in servers:
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(
                    hostname=server.ip_address,
                    username=server.username,
                    password=server.password
                )

                # CPU
                stdin, stdout, stderr = client.exec_command("top -bn1 | grep '%Cpu'")
                cpu_raw = stdout.read().decode().strip()
                if not cpu_raw:
                    raise ValueError("No se pudo obtener la métrica de CPU")
                cpu_parts = cpu_raw.split(',')
                cpu_idle_str = [part for part in cpu_parts if 'id' in part]
                if not cpu_idle_str:
                    raise ValueError("No se encontró valor idle en CPU")
                cpu_idle = float(cpu_idle_str[0].strip().split()[0])
                cpu_usage = round(100 - cpu_idle, 2)

                # Memoria
                stdin, stdout, stderr = client.exec_command("free | grep Mem")
                mem_raw = stdout.read().decode().strip()
                if not mem_raw:
                    raise ValueError("No se pudo obtener la métrica de memoria")
                mem_parts = mem_raw.split()
                mem_total = int(mem_parts[1])
                mem_used = int(mem_parts[2])
                mem_usage = round((mem_used / mem_total) * 100, 2)

                # Disco
                stdin, stdout, stderr = client.exec_command("df -h / | tail -1")
                disk_raw = stdout.read().decode().strip()
                if not disk_raw:
                    raise ValueError("No se pudo obtener la métrica de disco")
                disk_parts = disk_raw.split()
                disk_usage = float(disk_parts[4].replace('%', ''))

                # Guardar métricas
                metric = SystemMetrics(
                    timestamp=datetime.utcnow(),
                    cpu_usage=cpu_usage,
                    memory_usage=mem_usage,
                    disk_usage=disk_usage,
                    server_id=server.id
                )
                db.session.add(metric)
                db.session.commit()

                print(f"✅ Métricas registradas para {server.name}")

                client.close()

            except Exception as e:
                print(f"❌ Error en {server.name}: {e}")
