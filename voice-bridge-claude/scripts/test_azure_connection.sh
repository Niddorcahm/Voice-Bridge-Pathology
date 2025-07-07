#!/bin/bash

# Script de verificación Azure Speech Services
echo "=== Test Azure Speech Services ==="
echo ""

# Verificar variables de entorno
if [ -z "$AZURE_SPEECH_KEY" ]; then
    echo "❌ AZURE_SPEECH_KEY no configurado"
    echo "   Configura en ~/.bashrc:"
    echo "   export AZURE_SPEECH_KEY='tu_key_aqui'"
    exit 1
fi

if [ -z "$AZURE_SPEECH_REGION" ]; then
    echo "❌ AZURE_SPEECH_REGION no configurado"
    echo "   Valor por defecto: eastus"
    export AZURE_SPEECH_REGION="eastus"
fi

echo "✅ Variables configuradas"
echo "   Region: $AZURE_SPEECH_REGION" 
echo "   Speech Key: ${AZURE_SPEECH_KEY:0:8}..."
echo ""

# Test de conectividad con Content-Length apropiado
echo "Probando conectividad con Azure..."
response=$(curl -s -w "%{http_code}" \
  -X POST \
  -H "Ocp-Apim-Subscription-Key: $AZURE_SPEECH_KEY" \
  -H "Content-Length: 0" \
  "https://$AZURE_SPEECH_REGION.api.cognitive.microsoft.com/sts/v1.0/issuetoken" \
  -o /dev/null 2>/dev/null)

if [ "$response" = "200" ]; then
    echo "✅ Conectividad exitosa con Azure Speech Services"
    echo "✅ El sistema está listo para usar"
    echo ""
    echo "=== Configuración de Voces ==="
    echo "   Idioma: es-CO (Español Colombiano)"
    echo "   Voz TTS: es-CO-SalomeNeural (Femenina)"
    echo "   Alternativa: es-CO-GonzaloNeural (Masculina)"
elif [ "$response" = "401" ]; then
    echo "❌ Error de autenticación (HTTP 401)"
    echo "   La clave Azure es incorrecta o inválida"
    echo "   Verifica en Azure Portal: speech-medical-pathology-Luis"
elif [ "$response" = "403" ]; then
    echo "❌ Error de permisos (HTTP 403)"
    echo "   El recurso puede estar suspendido o sin cuota"
    echo "   Verifica el estado en Azure Portal"
else
    echo "❌ Error de conectividad (HTTP $response)"
    echo "   Verificar credenciales y región en Azure Portal"
    echo "   Endpoint: https://$AZURE_SPEECH_REGION.api.cognitive.microsoft.com/"
    
    # Test adicional de conectividad básica
    echo ""
    echo "Probando conectividad básica..."
    if ping -c 1 azure.microsoft.com > /dev/null 2>&1; then
        echo "✅ Conectividad a internet: OK"
    else
        echo "❌ Problema de conectividad a internet"
    fi
fi

echo ""
echo "=== Información de Debug ==="
echo "   Endpoint: https://$AZURE_SPEECH_REGION.api.cognitive.microsoft.com/sts/v1.0/issuetoken"
echo "   HTTP Response Code: $response"
