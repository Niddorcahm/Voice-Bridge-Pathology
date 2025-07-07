#!/bin/bash

# Script de inicio Voice Bridge System
cd "$(dirname "$0")"

echo "=================================="
echo "   Iniciando Voice Bridge System  "
echo "=================================="

# Verificar que UV esté disponible
if ! command -v uv &> /dev/null; then
    echo "❌ UV no está disponible"
    echo "   Reinstala UV o verifica PATH"
    exit 1
fi

# Verificar configuración Azure
if [ -z "$AZURE_SPEECH_KEY" ]; then
    echo "⚠️  AZURE_SPEECH_KEY no configurado"
    echo "   Configura las variables antes de continuar:"
    echo "   export AZURE_SPEECH_KEY='tu_key_aqui'"
    echo "   export AZURE_SPEECH_REGION='eastus'"
    echo ""
    echo "   O edita: config/voice_bridge_config.ini"
    echo ""
    read -p "¿Continuar sin Azure configurado? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "✅ Iniciando Voice Bridge Application..."

# Entrar al entorno UV
cd voice-bridge-project

# Ejecutar aplicación principal  
uv run python voice_bridge_app.py

echo "Voice Bridge finalizado"
