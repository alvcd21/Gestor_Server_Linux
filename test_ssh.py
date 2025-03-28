import paramiko

server_ip = "10.10.10.12"  # Reemplaza con la IP de tu servidor
server_user = "alvaro-cadenas"
server_password = "cadenas21"

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=server_ip,
        username=server_user,
        password=server_password,
        timeout=5
    )

    # 🔹 Ejecutar comando remoto para verificar conexión
    stdin, stdout, stderr = client.exec_command("uptime")
    print(stdout.read().decode().strip())  # 🔹 Debería mostrar el tiempo de actividad del servidor

    print("✅ Conexión SSH exitosa.")

except Exception as e:
    print(f"❌ Error en la conexión SSH: {e}")

finally:
    client.close()  # 🔹 Cerrar conexión correctamente
