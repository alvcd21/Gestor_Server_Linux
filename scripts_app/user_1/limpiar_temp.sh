#!/bin/bash

# Script para limpiar archivos temporales en /tmp

echo "Iniciando limpieza de archivos temporales en /tmp" >> output.log

# Eliminar archivos y carpetas temporales
sudo rm -rf /tmp/*

# Verificar si la limpieza fue exitosa
if [ $? -eq 0 ]; then
    echo "Limpieza de /tmp completada exitosamente." >> output.log
else
    echo "Error al limpiar la carpeta /tmp." >> output.log
fi
