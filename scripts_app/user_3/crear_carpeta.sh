#!/bin/bash

# 📁 Nombre de la carpeta que se va a crear
NOMBRE_CARPETA="mi_nueva_carpeta"

# 📂 Ruta donde se creará la carpeta (puedes cambiarla si quieres)
RUTA="/home/$NOMBRE_CARPETA"

# 🛠 Crear la carpeta si no existe
if [ ! -d "$RUTA" ]; then
    mkdir "$RUTA"
    echo "✅ Carpeta creada en: $RUTA"
else
    echo "⚠️ La carpeta ya existe en: $RUTA"
fi
