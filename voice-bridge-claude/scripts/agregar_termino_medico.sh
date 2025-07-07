#!/bin/bash

# Script para agregar términos médicos sin modificar código
DICT_DIR="$HOME/voice-bridge-claude/config/diccionarios"

if [ -z "$1" ]; then
    echo "Uso: $0 'término médico' [categoria]"
    echo "Categorías: patologia_molecular, frases_completas"
    echo "Ejemplo: $0 'carcinoma adenoescamoso' patologia_molecular"
    exit 1
fi

TERMINO="$1"
CATEGORIA="${2:-patologia_molecular}"
DICCIONARIO="$DICT_DIR/${CATEGORIA}.txt"

if [ ! -f "$DICCIONARIO" ]; then
    echo "❌ Diccionario $CATEGORIA no existe"
    exit 1
fi

if grep -qi "^$TERMINO$" "$DICCIONARIO"; then
    echo "⚠️ El término '$TERMINO' ya existe en $CATEGORIA"
else
    echo "$TERMINO" >> "$DICCIONARIO"
    echo "✅ Término '$TERMINO' agregado a $CATEGORIA"
    echo "💡 Reinicia Voice Bridge para aplicar cambios"
fi
