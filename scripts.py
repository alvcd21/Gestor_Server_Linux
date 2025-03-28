from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Server
import os
import paramiko

scripts_bp = Blueprint('scripts', __name__, url_prefix='/scripts')

BASE_SCRIPTS_DIRECTORY = os.path.join(os.getcwd(), 'scripts_app')

def get_user_scripts_directory():
    user_scripts_directory = os.path.join(BASE_SCRIPTS_DIRECTORY, f"user_{current_user.id}")
    if not os.path.exists(user_scripts_directory):
        os.makedirs(user_scripts_directory)
    return user_scripts_directory

def get_scripts():
    scripts_directory = get_user_scripts_directory()
    return [f for f in os.listdir(scripts_directory) if os.path.isfile(os.path.join(scripts_directory, f)) and os.access(os.path.join(scripts_directory, f), os.X_OK)]

@scripts_bp.route('/<int:server_id>')
@login_required
def index(server_id):
    scripts = get_scripts()
    server = Server.query.get_or_404(server_id)
    return render_template('scripts.html', scripts=scripts, server=server)

@scripts_bp.route('/<int:server_id>/run/<script_name>', methods=['POST'])
@login_required
def run_script(server_id, script_name):
    scripts_directory = get_user_scripts_directory()
    script_path = os.path.join(scripts_directory, script_name)
    
    server = Server.query.get_or_404(server_id)

    if not os.path.exists(script_path):
        flash("El script no existe en tu directorio de usuario.", "danger")
        return redirect(url_for('scripts.index', server_id=server.id))

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=server.ip_address,
            username=server.username,
            password=server.password
        )

        sftp = ssh.open_sftp()
        remote_path = f"/tmp/{script_name}"
        sftp.put(script_path, remote_path)
        sftp.chmod(remote_path, 0o755)
        sftp.close()

        stdin, stdout, stderr = ssh.exec_command(f"bash {remote_path}")
        output = stdout.read().decode()
        error = stderr.read().decode()
        ssh.close()

        if error:
            flash(f"⚠️ Error al ejecutar el script:\n{error}", "danger")
        else:
            flash(f"✅ Script ejecutado correctamente:\n{output}", "success")

    except Exception as e:
        flash(f"❌ Error en la conexión SSH o ejecución del script: {str(e)}", "danger")

    return redirect(url_for('scripts.index', server_id=server.id))
