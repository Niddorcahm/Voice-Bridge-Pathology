#!/bin/bash

# Voice Bridge Launcher - Carga variables de entorno y ejecuta
source ~/.bashrc
exec /home/$(whoami)/voice-bridge-claude/start_voice_bridge_gui.sh
