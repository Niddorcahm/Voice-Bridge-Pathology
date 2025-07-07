#!/bin/bash

# Voice Bridge - Patología Molecular
# Script con carga automática de variables de entorno

# Cargar variables de entorno del usuario
if [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi

# Ir al directorio del script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "🎤 Iniciando Voice Bridge - Patología Molecular..."

# Verificar entorno virtual
if [ ! -d "voice-bridge-project/.venv" ]; then
    echo "❌ Entorno virtual no encontrado"
    exit 1
fi

# Activar entorno virtual
source voice-bridge-project/.venv/bin/activate

# Verificar Azure Speech Key
if [ -z "$AZURE_SPEECH_KEY" ]; then
    echo "❌ AZURE_SPEECH_KEY no configurado"
    echo "Configurar variables de entorno en ~/.bashrc"
    exit 1
fi

# Verificar dependencias críticas
if ! python -c "import azure.cognitiveservices.speech" 2>/dev/null; then
    echo "❌ Azure Speech SDK no disponible"
    exit 1
fi

if ! python -c "import tkinter" 2>/dev/null; then
    echo "❌ Tkinter no disponible"
    exit 1
fi

# Iniciar Voice Bridge
echo "✅ Iniciando Voice Bridge..."
cd voice-bridge-project
python3 voice_bridge_app.py

# Capturar código de salida
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "❌ Voice Bridge terminó con errores: $EXIT_CODE"
    read -p "Presiona Enter para cerrar..."
fi

exit $EXIT_CODE
