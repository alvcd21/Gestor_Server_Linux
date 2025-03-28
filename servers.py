import paramiko
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Server
from models import Server, SystemMetrics, db
from monitoring import get_remote_metrics  


# Crear Blueprint
servers_bp = Blueprint("servers", __name__, url_prefix="/servers")

@servers_bp.route("/")
@login_required
def list_servers():
    """Muestra la lista de servidores agregados por el usuario."""
    servers = Server.query.filter_by(user_id=current_user.id).all()
    return render_template("servers.html", servers=servers)


@servers_bp.route("/metrics/<int:server_id>")
@login_required
def view_metrics(server_id):
    """Vista de métricas para un servidor específico."""
    server = Server.query.filter_by(id=server_id, user_id=current_user.id).first()
    if not server:
        flash("Servidor no encontrado o no autorizado.", "danger")
        return redirect(url_for("servers.list_servers"))

    # Obtener métricas históricas almacenadas en la BD
    metrics = SystemMetrics.query.filter_by(server_id=server.id).order_by(SystemMetrics.timestamp.desc()).limit(10).all()

    remote_metrics = get_remote_metrics(server)

    return render_template("server_metrics.html",
        server=server,
        metrics=metrics,
        system_info=remote_metrics.get("system_info"),
        processes=remote_metrics.get("processes"),
        remote_error=remote_metrics.get("error"),
        cpu_usage=remote_metrics.get("cpu"),
        memory_usage=remote_metrics.get("memory"),
        disk_usage=remote_metrics.get("disk")
    )

@servers_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_server():
    if request.method == "POST":
        name = request.form["name"]
        ip_address = request.form["ip_address"]
        username = request.form["username"]
        password = request.form["password"]

        # Validación básica
        if not name or not ip_address or not username or not password:
            flash("Todos los campos son obligatorios.", "danger")
            return render_template("add_server.html", name=name, ip_address=ip_address, username=username)

        # ✅ Verificar conexión SSH antes de guardar
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh_client.connect(
                hostname=ip_address,
                username=username,
                password=password,
                timeout=5
            )
            ssh_client.close()
        except Exception as e:
            flash(f"❌ No se pudo conectar al servidor: {str(e)}", "danger")
            return render_template("add_server.html", name=name, ip_address=ip_address, username=username)

        new_server = Server(
            name=name,
            ip_address=ip_address,
            username=username,
            password=password,
            user_id=current_user.id,
        )




        db.session.add(new_server)
        db.session.commit()
        flash("✅ Servidor agregado correctamente.", "success")
        return redirect(url_for("servers.list_servers"))

    # GET inicial
    return render_template("add_server.html")


@servers_bp.route("/delete/<int:server_id>", methods=["POST"])
@login_required
def delete_server(server_id):
    """Elimina un servidor."""
    server = Server.query.filter_by(id=server_id, user_id=current_user.id).first()
    if server:
        db.session.delete(server)
        db.session.commit()
        flash("Servidor eliminado correctamente.", "success")
    else:
        flash("Servidor no encontrado.", "danger")
    
    return redirect(url_for("servers.list_servers"))
