from flask import Blueprint, render_template, flash
import psutil
import smtplib
from email.mime.text import MIMEText

alerts_bp = Blueprint('alerts', __name__, url_prefix='/alerts')

# Umbrales de alerta
CPU_THRESHOLD = 80  # % Uso de CPU
MEM_THRESHOLD = 80  # % Uso de Memoria
DISK_THRESHOLD = 90  # % Uso de Disco

# Lista de alertas
alerts = []

def check_system_alerts():
    """Revisa umbrales y guarda alertas."""
    global alerts
    alerts = []  # Reiniciar lista

    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent

    if cpu > CPU_THRESHOLD:
        alerts.append(f"⚠️ Alerta: Uso de CPU alto ({cpu}%)")
    if mem > MEM_THRESHOLD:
        alerts.append(f"⚠️ Alerta: Uso de Memoria alta ({mem}%)")
    if disk > DISK_THRESHOLD:
        alerts
