from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
import subprocess
from models import Server

services_bp = Blueprint('services', __name__, url_prefix='/services')

def get_services():
    """📌 Obtiene la lista de servicios usando systemctl."""
    try:
        result = subprocess.run(
            ['systemctl', 'list-units', '--type=service', '--all', '--no-pager', '--no-legend'],
            capture_output=True, text=True, check=True
        )
        lines = result.stdout.strip().split('\n')
        services = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 4:
                service_name = parts[0]
                load = parts[1]
                active = parts[2]
                sub = parts[3]
                description = " ".join(parts[4:])
                services.append({
                    'name': service_name,
                    'load': load,
                    'active': active,
                    'sub': sub,
                    'description': description
                })
        return services
    except subprocess.CalledProcessError:
        return []

@services_bp.route('/')
@login_required
def index():
    """📌 Muestra los servicios del servidor seleccionado por el usuario"""
    servers = Server.query.filter_by(user_id=current_user.id).all()
    return render_template('services.html', servers=servers)

@services_bp.route('/<int:server_id>')
@login_required
def list_services(server_id):
    """📌 Lista servicios solo de los servidores del usuario autenticado"""
    server = Server.query.get_or_404(server_id)

    if server.user_id != current_user.id:
        flash("No tienes permiso para ver los servicios de este servidor.", "danger")
        return redirect(url_for('services.index'))

    services = get_services()
    return render_template('services.html', server=server, services=services)

@services_bp.route('/action/<int:server_id>/<service_name>/<action>', methods=['POST'])
@login_required
def service_action(server_id, service_name, action):
    """📌 Ejecuta una acción (start, stop, restart) en un servicio del servidor seleccionado"""
    server = Server.query.get_or_404(server_id)

    if server.user_id != current_user.id:
        flash("No tienes permiso para administrar servicios en este servidor.", "danger")
        return redirect(url_for('services.index'))

    if action not in ['start', 'stop', 'restart']:
        flash("Acción no válida.", "danger")
        return redirect(url_for('services.index'))

    try:
        # 🔹 Se debe configurar `sudoers` para que no pida contraseña en systemctl
        subprocess.run(['sudo', 'systemctl', action, service_name], check=True)
        flash(f"Servicio {service_name} {action}e exitosamente.", "success")
    except subprocess.CalledProcessError as e:
        flash(f"Error al ejecutar {action} en {service_name}: {str(e)}", "danger")

    return redirect(url_for('services.list_services', server_id=server_id))
