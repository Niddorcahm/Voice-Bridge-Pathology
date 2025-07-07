#!/bin/bash

cd ~/voice-bridge-claude/voice-bridge-project

echo "==================================="
echo "   Voice Bridge - Modo Directo     "
echo "==================================="

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no encontrado"
    exit 1
fi

# Verificar Azure
if [ -z "$AZURE_SPEECH_KEY" ]; then
    echo "⚠️  AZURE_SPEECH_KEY no configurado"
    echo "   Variables disponibles: ${AZURE_SPEECH_KEY:+SI}"
fi

# Activar entorno virtual si existe
if [ -d ".venv" ]; then
    echo "✅ Activando entorno virtual..."
    source .venv/bin/activate
fi

# Verificar dependencias críticas
python3 -c "import azure.cognitiveservices.speech; print('✅ Azure Speech SDK disponible')" || {
    echo "❌ Instalando Azure Speech SDK..."
    pip install azure-cognitiveservices-speech
}

python3 -c "import tkinter; print('✅ Tkinter disponible')" || {
    echo "❌ Instalando tkinter..."
    sudo apt install -y python3-tk
}

echo "✅ Iniciando Voice Bridge..."
python3 voice_bridge_app.py

echo "Voice Bridge finalizado"
