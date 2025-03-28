
import psutil
import platform
from flask import Flask, render_template, redirect, url_for, flash
from flask_apscheduler import APScheduler
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from datetime import datetime
from models import User, SystemMetrics, Server
from models import db 
from tasks import record_all_servers_metrics
from services import services_bp
from scripts import scripts_bp
from historical import historical_bp
from servers import servers_bp
from monitoring import monitoring_bp
from auth import auth_bp  

# 🔹 Inicializar Flask
app = Flask(__name__)
app.secret_key = "cadenas21"  # Cambia esto por una clave segura

# 🔹 Configuración de la base de datos (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///metrics.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SCHEDULER_API_ENABLED'] = True  # Habilitar el scheduler

db.init_app(app)

# 🔹 Configurar Flask-Login
login_manager = LoginManager()
login_manager.login_view = "auth.login"  # Redirigir a login si no está autenticado
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 🔹 Configuración del scheduler
scheduler = APScheduler()

# ---------------------------
# Módulo de Alertas y Registro Histórico
alerts = []

def check_system_alerts():
    """Revisa umbrales y guarda alertas en la variable global."""
    global alerts
    alerts.clear()  # Reinicia las alertas
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent

    if cpu > 80:
        alerts.append(f"⚠️ Alerta: Uso de CPU alto: {cpu}%")
    if mem > 80:
        alerts.append(f"⚠️ Alerta: Uso de Memoria alta: {mem}%")
    if disk > 90:
        alerts.append(f"⚠️ Alerta: Espacio en Disco crítico: {disk}%")

def record_system_metrics():
    """Registra las métricas del sistema en la base de datos."""
    with app.app_context():
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        print(f"Registrando métricas: CPU={cpu}%, Memoria={mem}%, Disco={disk}%")  # Para depuración
        metric = SystemMetrics(cpu_usage=cpu, memory_usage=mem, disk_usage=disk)
        db.session.add(metric)
        db.session.commit()

# ---------------------------
# Función para formatear bytes a formato legible
def format_bytes(size):
    power = 1024
    n = 0
    power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size > power and n < 4:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}"

app.jinja_env.filters['filesizeformat'] = format_bytes

def get_system_info():
    """Obtiene información básica del sistema."""
    return {
        'platform': platform.system(),
        'platform_release': platform.release(),
        'platform_version': platform.version(),
        'architecture': platform.machine(),
        'hostname': platform.node(),
        'processor': platform.processor(),
        'cpu_usage': psutil.cpu_percent(interval=1),
        'memory': psutil.virtual_memory()._asdict(),
        'disk': psutil.disk_usage('/')._asdict()
    }

def get_processes():
    """Obtiene la lista de procesos en ejecución."""
    process_list = []
    for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
        try:
            process_list.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return process_list

# ---------------------------
# Rutas principales
@app.route("/")
def index():
    system_info = get_system_info()
    processes = get_processes()
    return render_template("index.html", system_info=system_info, processes=processes, alerts=alerts)

@app.route("/kill/<int:pid>", methods=["POST"])
def kill_process(pid):
    """Intenta terminar el proceso indicado."""
    try:
        proc = psutil.Process(pid)
        proc.terminate()
        proc.wait(timeout=3)
        flash(f"Proceso {pid} terminado correctamente.", "success")
    except Exception as e:
        flash(f"Error al terminar el proceso {pid}: {str(e)}", "danger")
    return redirect(url_for("index"))

# 🔹 Inicializar `scheduler` dentro del contexto de la app
with app.app_context():
    db.create_all()
    scheduler.init_app(app)
    scheduler.start()
    
    scheduler.add_job(id='Check_Alerts', func=check_system_alerts, trigger='interval', seconds=60)
    scheduler.add_job(id='Record_Metrics', func=lambda: record_all_servers_metrics(app), trigger='interval', seconds=60)




app.register_blueprint(services_bp)
app.register_blueprint(scripts_bp)
app.register_blueprint(historical_bp)
app.register_blueprint(servers_bp)
app.register_blueprint(monitoring_bp)
app.register_blueprint(auth_bp)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
