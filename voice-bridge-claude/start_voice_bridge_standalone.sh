#!/bin/bash

# Voice Bridge Standalone - Como Claude.AppImage
# Autocontenido, no depende de variables externas

# Variables de Azure (reemplaza con tus valores reales)
export AZURE_SPEECH_KEY="1lIytba7GOVjIUX51KfljpxUKYxm8uJiuG8GoPTy94Kv90Y9AlOPJQQJ99BGACYeBjFXJ3w3AAAYACOGPK2G"
export AZURE_SPEECH_REGION="eastus"
export SPEECH_LANGUAGE="es-CO"
export TTS_VOICE="es-CO-SalomeNeural"

# Ir al directorio de Voice Bridge
cd /home/zapataperezluis/voice-bridge-claude

# Activar entorno virtual
source voice-bridge-project/.venv/bin/activate

# Iniciar aplicación
cd voice-bridge-project
exec python3 voice_bridge_app.py
