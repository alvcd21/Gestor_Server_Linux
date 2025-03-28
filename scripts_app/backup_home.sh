#!/bin/bash

# Script para realizar una copia de seguridad de la carpeta /home
# Guarda el archivo de respaldo en /backup con fecha y hora

# Crear la carpeta de backup si no existe
BACKUP_DIR="/backup"
if [ ! -d "$BACKUP_DIR" ]; then
    sudo mkdir -p "$BACKUP_DIR"
    sudo chmod 755 "$BACKUP_DIR"
    echo "Directorio /backup creado." >> output.log
fi

# Nombre del archivo de respaldo
FECHA=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_FILE="$BACKUP_DIR/backup_home_$FECHA.tar.gz"

# Realizar la copia de seguridad excluyendo carpetas de caché y sockets
echo "Iniciando copia de seguridad de /home en $BACKUP_FILE" >> output.log

sudo tar --exclude='/home/*/.cache' \
         --exclude='/home/*/snap/firefox' \
         --exclude='*.sock' \
         --ignore-failed-read \
         -czf "$BACKUP_FILE" /home

# Verificar si el backup fue exitoso
if [ $? -eq 0 ]; then
    echo "Copia de seguridad completada exitosamente." >> output.log
else
    echo "Error al realizar la copia de seguridad." >> output.log
fi
