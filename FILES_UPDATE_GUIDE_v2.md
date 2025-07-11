# Voice Bridge v2.0 - Guía de Actualización de Archivos para GitHub

## 📁 Resumen de Archivos para Actualizar

### ✅ Archivos NUEVOS Creados (v2)
- [x] `README_v2.md` - ✅ Ya creado
- [x] `CHANGELOG_v2.md` - ✅ Ya creado
- [ ] `config/voice_bridge_config_v2.ini.example` - 🔄 Por crear
- [ ] `docs/VOICE_COMMANDS.md` - 🔄 Por crear
- [ ] `docs/DICTATION_MODE.md` - 🔄 Por crear
- [ ] `scripts/upgrade_to_v2.sh` - 🔄 Por crear

### 📝 Archivos a ACTUALIZAR (Reemplazar con v2)

| Archivo | Estado | Acción |
|---------|---------|--------|
| `voice_bridge_app.py` | 🔄 | Reemplazar con código v2 completo |
| `README.md` | 🔄 | Reemplazar con contenido de README_v2.md |
| `CHANGELOG.md` | 🔄 | Agregar sección v2.0.0 |
| `requirements.txt` | 🔄 | Verificar versión Azure SDK |
| `INSTALL.md` | 🔄 | Actualizar instrucciones para v2 |
| `USAGE.md` | 🔄 | Agregar comandos de voz |
| `TROUBLESHOOTING.md` | 🔄 | Agregar problemas v2 |
| `UPGRADE.md` | 🔄 | Crear guía migración v1→v2 |

### ✅ Archivos que se MANTIENEN Sin Cambios

| Archivo | Razón |
|---------|-------|
| `scripts/test_azure_connection.sh` | Compatible con v2 |
| `scripts/agregar_termino_medico.sh` | Compatible con v2 |
| `config/diccionarios/patologia_molecular.txt` | Usar versión actual |
| `config/diccionarios/frases_completas.txt` | Usar versión actual |
| `start_voice_bridge_gui.sh` | Compatible con v2 |
| `LICENSE.md` | Sin cambios |
| `CODE_OF_CONDUCT.md` | Sin cambios |
| `CONTRIBUTING.md` | Sin cambios |
| `SECURITY.md` | Sin cambios |
| `.gitignore` | Sin cambios |

### ❌ Archivos a NO SUBIR (Privados)

| Archivo | Razón |
|---------|-------|
| `config/voice_bridge_config_v2.ini` | Contiene Azure Key personal |
| `logs/*.log` | Datos de sesiones |
| `logs/transcripciones_*.txt` | Datos médicos privados |
| `.venv/` | Entorno virtual local |

---

## 📋 Plan de Actualización Paso a Paso

### Paso 1: Preparar Archivos Nuevos

#### 1.1 Crear `config/voice_bridge_config_v2.ini.example`
```ini
[DEFAULT]
# Azure Speech Services
azure_speech_key = YOUR_AZURE_SPEECH_KEY_HERE
azure_region = eastus
speech_language = es-CO
tts_voice = es-CO-SalomeNeural

# Hotkeys
hotkey_start = ctrl+shift+v
hotkey_stop = ctrl+shift+s
hotkey_dictation = ctrl+shift+d

# Behavior
auto_send_to_claude = false
claude_window_title = Claude
medical_mode = true
confidence_threshold = 0.5
tts_enabled = true
claude_activation_delay = 0.5

# Voice Bridge v2 Features
dictation_mode = continuous
anti_coupling = true
tts_during_dictation = false
auto_correct_medical = true
dictation_timeout_seconds = 8
timeout_warning_seconds = 3
timeout_audio_warning = true
```

#### 1.2 Crear `scripts/upgrade_to_v2.sh`
```bash
#!/bin/bash
# Voice Bridge v1 to v2 Upgrade Script

echo "=== Voice Bridge v2 Upgrade Script ==="
echo

# Backup current installation
echo "Creating backup..."
cp voice_bridge_app.py voice_bridge_app_v1_backup.py
cp config/voice_bridge_config.ini config/voice_bridge_config_v1_backup.ini

# Create v2 config
echo "Creating v2 configuration..."
if [ ! -f config/voice_bridge_config_v2.ini ]; then
    cp config/voice_bridge_config.ini config/voice_bridge_config_v2.ini
    echo "
# Voice Bridge v2 Settings
dictation_mode = continuous
anti_coupling = true
auto_correct_medical = true
dictation_timeout_seconds = 8
" >> config/voice_bridge_config_v2.ini
fi

# Update dependencies
echo "Updating dependencies..."
pip install --upgrade azure-cognitiveservices-speech

echo
echo "✅ Upgrade complete!"
echo "Please update voice_bridge_app.py with the v2 code"
```

### Paso 2: Actualizar Archivos Principales

#### 2.1 Reemplazar `README.md`
- Copiar contenido de `README_v2.md` a `README.md`
- Eliminar `README_v2.md` después

#### 2.2 Actualizar `CHANGELOG.md`
- Agregar contenido de `CHANGELOG_v2.md` al inicio
- Mantener historial v1.x debajo

#### 2.3 Actualizar `requirements.txt`
```txt
azure-cognitiveservices-speech>=1.35.0
pyautogui>=0.9.54
pynput>=1.7.6
pyyaml>=6.0.1
requests>=2.31.0
python-dotenv>=1.0.0
tkinter-tooltip>=2.0.0
```

### Paso 3: Crear Documentación Adicional

#### 3.1 Crear `docs/VOICE_COMMANDS.md`
```markdown
# Voice Commands Reference

## Dictation Commands
- **"inicio dictado"** - Start continuous dictation mode
- **"fin dictado"** - End dictation and preview
- **"cancelar dictado"** - Cancel current dictation
- **"enviar a claude"** - Send buffer to Claude

## System Commands
- **"repetir última"** - Repeat last segment via TTS
- **"estado del sistema"** - Speak system status

## Command Tips
- Speak clearly with slight pause after command
- Commands work during dictation mode
- Visual confirmation appears when recognized
```

#### 3.2 Crear `docs/DICTATION_MODE.md`
```markdown
# Continuous Dictation Mode Guide

## Overview
Voice Bridge v2 introduces continuous dictation mode for uninterrupted medical dictation.

## How It Works
1. Say "inicio dictado" to start
2. Speak continuously - no need to pause
3. System accumulates all speech in buffer
4. Auto-finalizes after 8 seconds of silence
5. Or say "fin dictado" to stop manually

## Features
- Visual buffer display
- Timeout countdown
- Auto-corrections
- Command detection during dictation
```

### Paso 4: Verificar y Limpiar

#### 4.1 Verificar que NO incluyas:
- [ ] Claves Azure reales
- [ ] Datos personales (nombre, email personal)
- [ ] Transcripciones médicas reales
- [ ] Rutas absolutas personales

#### 4.2 Reemplazar en el código:
- `/home/zapataperezluis/` → `/home/user/`
- Emails personales → `user@example.com`
- Azure keys → `YOUR_AZURE_KEY_HERE`

---

## 🚀 Comandos Git para Actualizar

```bash
# 1. Crear nueva rama para v2
git checkout -b release/v2.0.0

# 2. Agregar archivos actualizados
git add voice_bridge_app.py
git add README.md CHANGELOG.md
git add config/voice_bridge_config_v2.ini.example
git add scripts/upgrade_to_v2.sh
git add docs/VOICE_COMMANDS.md docs/DICTATION_MODE.md

# 3. Commit con mensaje descriptivo
git commit -m "feat: Voice Bridge v2.0.0 - Continuous dictation mode

- Add continuous dictation with voice commands
- Implement 8-second timeout system
- Add medical term auto-correction
- Improve Azure Speech configuration
- Add anti-coupling system for TTS
- Update documentation for v2"

# 4. Push a GitHub
git push origin release/v2.0.0

# 5. Crear Pull Request en GitHub
```

---

## ✅ Checklist Final Pre-Publicación

- [ ] Código v2 sin errores de PropertyId
- [ ] Configuración example sin datos personales
- [ ] README actualizado y profesional
- [ ] CHANGELOG completo con fecha
- [ ] Scripts de upgrade funcionando
- [ ] Documentación de comandos de voz
- [ ] Screenshots actualizados (si aplica)
- [ ] Verificar .gitignore excluye archivos privados

---

## 📊 Resumen de Cambios para GitHub

### Archivos a Subir (13 archivos)
1. `voice_bridge_app.py` (v2 actualizado)
2. `README.md` (reemplazado con v2)
3. `CHANGELOG.md` (actualizado)
4. `requirements.txt` (verificado)
5. `config/voice_bridge_config_v2.ini.example` (nuevo)
6. `scripts/upgrade_to_v2.sh` (nuevo)
7. `docs/VOICE_COMMANDS.md` (nuevo)
8. `docs/DICTATION_MODE.md` (nuevo)
9. `INSTALL.md` (actualizado)
10. `USAGE.md` (actualizado)
11. `TROUBLESHOOTING.md` (actualizado)
12. `UPGRADE.md` (nuevo)
13. Scripts existentes compatibles

### Archivos NO Modificados (se mantienen)
- Diccionarios médicos
- Scripts de utilidad
- Archivos de licencia y contribución
- Configuración Docker
- Tests

---

*Documento creado: 2025-01-09*
*Voice Bridge v2.0.0 Release*