from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from models import SystemMetrics, Server
from datetime import datetime, timedelta

historical_bp = Blueprint('historical', __name__, url_prefix='/historical')

@historical_bp.route('/<int:server_id>')
@login_required
def index(server_id):
    time_threshold = datetime.now() - timedelta(hours=24)

    server = Server.query.filter_by(id=server_id, user_id=current_user.id).first()
    if not server:
        flash("Servidor no autorizado o no encontrado", "danger")
        return redirect(url_for('servers.list_servers'))

    metrics = SystemMetrics.query.filter(
        SystemMetrics.timestamp >= time_threshold,
        SystemMetrics.server_id == server_id
    ).order_by(SystemMetrics.timestamp.desc()).all()

    if not metrics:
        flash("No hay métricas recientes para este servidor.", "info")

    return render_template('historical.html', metrics=metrics, server=server)
