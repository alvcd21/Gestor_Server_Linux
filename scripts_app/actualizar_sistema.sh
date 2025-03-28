#!/bin/bash

# Script para actualizar el sistema en Linux

echo "Iniciando actualización del sistema..." >> output.log

# Actualizar la lista de paquetes y el sistema
sudo apt update && sudo apt upgrade -y

# Verificar si la actualización fue exitosa
if [ $? -eq 0 ]; then
    echo "Actualización del sistema completada exitosamente." >> output.log
else
    echo "Error al actualizar el sistema." >> output.log
fi
