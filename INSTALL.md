# Installation Guide - Voice Bridge for Pathology

This guide provides complete installation instructions for Voice Bridge, a specialized speech recognition system for molecular pathology.

## 📋 Prerequisites

### System Requirements
- **Operating System**: Ubuntu 24.04 LTS (recommended)
- **Python**: 3.12+
- **RAM**: Minimum 4GB, recommended 8GB
- **Storage**: 2GB free space
- **Audio**: Quality microphone (USB or built-in)
- **Network**: Stable internet connection for Azure

### Required Accounts
- **Azure Speech Services**: Active subscription
- **Claude Desktop**: Installed and configured
- **Obsidian**: With MCP integration (optional but recommended)

## 🔧 Step 1: System Dependencies

### Install Ubuntu Packages
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    wmctrl \
    xdotool \
    xclip \
    pulseaudio-utils \
    alsa-utils \
    inkscape \
    imagemagick \
    curl \
    git

# Install audio tools
sudo apt install -y pavucontrol pulseaudio
```

### Configure Audio System
```bash
# Verify audio devices
pactl list sources short

# Set default microphone (replace with your device)
pactl set-default-source alsa_input.pci-0000_0b_00.4.analog-stereo.2

# Test audio
speaker-test -t wav -c 2 -l 1
```

## ☁️ Step 2: Azure Speech Services Setup

### 2.1 Create Azure Resource
1. Go to [Azure Portal](https://portal.azure.com)
2. Create new resource → AI + Machine Learning → Speech Services
3. Configuration:
   - **Subscription**: Your Azure subscription
   - **Resource Group**: Create `rg-medical-pathology`
   - **Name**: `speech-medical-pathology-[yourname]`
   - **Region**: `East US` (recommended)
   - **Pricing**: Standard S0 (for professional use)

### 2.2 Get Service Keys
1. Navigate to your Speech resource
2. Go to Keys and Endpoint
3. Copy **Key 1** and **Region**

### 2.3 Configure Environment Variables
```bash
# Edit bash profile
nano ~/.bashrc

# Add these lines at the end:
export AZURE_SPEECH_KEY="your_azure_key_here"
export AZURE_SPEECH_REGION="eastus"
export SPEECH_LANGUAGE="es-CO"
export TTS_VOICE="es-CO-SalomeNeural"

# Save file (Ctrl+O, Enter, Ctrl+X)

# Reload environment
source ~/.bashrc

# Verify configuration
echo "Azure Key: ${AZURE_SPEECH_KEY:0:8}..."
echo "Region: $AZURE_SPEECH_REGION"
```

### 2.4 Test Azure Connection
```bash
# Test connectivity
curl -s -w "%{http_code}" \
  -X POST \
  -H "Ocp-Apim-Subscription-Key: $AZURE_SPEECH_KEY" \
  -H "Content-Length: 0" \
  "https://$AZURE_SPEECH_REGION.api.cognitive.microsoft.com/sts/v1.0/issuetoken" \
  -o /dev/null

# Should return: 200
```

## 🏗️ Step 3: Voice Bridge Installation

### 3.1 Create Project Structure
```bash
# Create main directory
mkdir -p ~/voice-bridge-claude/{voice-bridge-project,config/diccionarios,assets,scripts,logs}
cd ~/voice-bridge-claude
```

### 3.2 Python Environment Setup
```bash
# Navigate to project directory
cd voice-bridge-project

# Create virtual environment
python3 -m venv .venv

# Activate environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install \
    azure-cognitiveservices-speech>=1.35.0 \
    pyautogui>=0.9.54 \
    pynput>=1.7.6 \
    pyyaml>=6.0.1 \
    python-dotenv>=1.0.0
```

### 3.3 Download Voice Bridge Application
```bash
# Download main application file
wget -O voice_bridge_app.py https://raw.githubusercontent.com/zapataperezluis/voice-bridge-pathology/main/voice_bridge_app.py

# Make executable
chmod +x voice_bridge_app.py
```

### 3.4 Create Configuration Files

#### Main Configuration
```bash
# Create configuration file
cat > ~/voice-bridge-claude/config/voice_bridge_config.ini << 'EOF'
[DEFAULT]
azure_speech_key = 
azure_region = eastus
speech_language = es-CO
tts_voice = es-CO-SalomeNeural
hotkey_start = ctrl+shift+v
hotkey_stop = ctrl+shift+s
hotkey_emergency = ctrl+shift+x
auto_send_to_claude = true
claude_window_title = Claude
medical_mode = true
confidence_threshold = 0.2
tts_enabled = true
claude_activation_delay = 0.2
EOF
```

#### Medical Dictionary - Pathology Terms
```bash
# Create pathology molecular dictionary
cat > ~/voice-bridge-claude/config/diccionarios/patologia_molecular.txt << 'EOF'
# Diccionario Médico Personalizado - Patología Molecular
Claude
pleomorfismo nuclear
carcinoma basocelular
carcinoma escamocelular
carcinoma urotelial
adenocarcinoma
células atípicas
células en anillo de sello
hiperqueratosis
dermis papilar
invasión focal
invasión vascular
invasión perineural
compatible con
gastritis crónica
gastropatía atrófica
metaplasia intestinal
metaplasia columnar
helicobacter spp
proceso inflamatorio
neutrófilos estromales
folículos linfoides
hiperplasia foveolar
atrofia antral
atrofia corporal
fibrosis estromal
congestión vascular
microhemorragia
edema
clasificación de viena
clasificación de marsh
olga estadio
olgim estadio
protocolo de sydney
células endocervicales
células exocervicales
microbiota bacilar
virus papiloma humano
cambios coilocíticos
atipias escamosas
asc us
tinción de papanicolau
hematoxilina eosina
inmunohistoquímica
esofagitis erosiva
esofagitis crónica
esófago de barrett
reflujo gastroesofágico
hiperplasia basal
papilomatosis
epitelio escamoso
ulceración focal
erosión epitelial
duodenitis crónica
vellosidades conservadas
linfocitos intraepiteliales
relación vellosidad cripta
lámina basal
enfermedad celiaca
dermis papilar
cistitis crónica
carcinoma urotelial
lámina propia
capa muscular
dermatitis espongiótica
paraqueratosis
estrato granuloso
espongiosis leve
EOF
```

#### Complete Medical Phrases
```bash
# Create complete phrases dictionary
cat > ~/voice-bridge-claude/config/diccionarios/frases_completas.txt << 'EOF'
# Frases Médicas Completas - MÁXIMA PRIORIDAD
Claude observo en la biopsia
Claude inicio análisis caso
Claude agregar al informe
Claude consultar plantilla
Claude generar informe
células atípicas en la capa basal
pleomorfismo nuclear y invasión focal
compatible con carcinoma basocelular
invasión de la dermis papilar
márgenes libres de neoplasia
se observa hiperqueratosis marcada
proceso inflamatorio crónico inespecífico
sin evidencia de malignidad
se sugiere correlación clínica
gastritis crónica moderada activa
metaplasia intestinal incompleta antral
presencia de helicobacter spp
clasificación uno de viena
clasificación dos de viena
olga estadio cero
olgim estadio uno
protocolo de sydney
fragmentos de mucosa gástrica
lámina propia con edema
negativo para células neoplásicas
muestra satisfactoria
EOF
```

### 3.5 Create Startup Scripts

#### Main GUI Script
```bash
# Create GUI startup script
cat > ~/voice-bridge-claude/start_voice_bridge_gui.sh << 'EOF'
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
EOF

chmod +x ~/voice-bridge-claude/start_voice_bridge_gui.sh
```

#### Azure Connection Test
```bash
# Create Azure test script
cat > ~/voice-bridge-claude/test_azure_connection.sh << 'EOF'
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

# Test de conectividad
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
else
    echo "❌ Error de conectividad (HTTP $response)"
    echo "   Verificar credenciales y región en Azure Portal"
fi
EOF

chmod +x ~/voice-bridge-claude/test_azure_connection.sh
```

#### Medical Term Management
```bash
# Create medical term addition script
cat > ~/voice-bridge-claude/scripts/agregar_termino_medico.sh << 'EOF'
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
EOF

chmod +x ~/voice-bridge-claude/scripts/agregar_termino_medico.sh
```

## 🎨 Step 4: System Integration

### 4.1 Create Application Icon
```bash
# Create icon SVG
cat > ~/voice-bridge-claude/assets/voice-bridge-icon.svg << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="128" height="128" viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
  <!-- Fondo circular -->
  <circle cx="64" cy="64" r="60" fill="#2563eb" stroke="#1d4ed8" stroke-width="2"/>
  
  <!-- Micrófono central -->
  <rect x="52" y="32" width="24" height="32" rx="12" fill="white"/>
  <rect x="58" y="68" width="12" height="12" fill="white"/>
  <path d="M 46 55 Q 46 75 64 75 Q 82 75 82 55" stroke="white" stroke-width="3" fill="none"/>
  
  <!-- Ondas sonoras -->
  <path d="M 25 45 Q 35 55 25 65" stroke="#60a5fa" stroke-width="3" fill="none"/>
  <path d="M 20 40 Q 32 55 20 70" stroke="#60a5fa" stroke-width="2" fill="none"/>
  <path d="M 103 45 Q 93 55 103 65" stroke="#60a5fa" stroke-width="3" fill="none"/>
  <path d="M 108 40 Q 96 55 108 70" stroke="#60a5fa" stroke-width="2" fill="none"/>
  
  <!-- Símbolo médico (cruz) -->
  <rect x="100" y="20" width="8" height="20" fill="#ef4444" rx="2"/>
  <rect x="96" y="24" width="16" height="8" fill="#ef4444" rx="2"/>
  
  <!-- Texto Voice Bridge -->
  <text x="64" y="105" text-anchor="middle" font-family="Arial, sans-serif" font-size="10" font-weight="bold" fill="white">VOICE BRIDGE</text>
  <text x="64" y="118" text-anchor="middle" font-family="Arial, sans-serif" font-size="8" fill="#94a3b8">Patología</text>
</svg>
EOF

# Convert to PNG
inkscape ~/voice-bridge-claude/assets/voice-bridge-icon.svg -w 128 -h 128 -o ~/.local/share/pixmaps/voice-bridge-pathology.png
```

### 4.2 Create Desktop Entry
```bash
# Create application launcher
cat > ~/.local/share/applications/voice-bridge-pathology.desktop << 'EOF'
[Desktop Entry]
Name=Voice Bridge
Exec=/home/$(whoami)/voice-bridge-claude/start_voice_bridge_gui.sh
Icon=voice-bridge-pathology
Type=Application
Terminal=false
Categories=AudioVideo;
Comment=Reconocimiento de voz para patología molecular
StartupNotify=true
Keywords=voz;voice;patologia;pathology;medicina;medical;
EOF

chmod +x ~/.local/share/applications/voice-bridge-pathology.desktop

# Update applications database
update-desktop-database ~/.local/share/applications/
```

## ✅ Step 5: Verification and Testing

### 5.1 Test Azure Connection
```bash
cd ~/voice-bridge-claude
./test_azure_connection.sh

# Expected output:
# ✅ Conectividad exitosa con Azure Speech Services
# ✅ El sistema está listo para usar
```

### 5.2 Test Voice Bridge Application
```bash
# Start Voice Bridge
./start_voice_bridge_gui.sh

# Expected log output:
# 🎤 Iniciando Voice Bridge - Patología Molecular...
# ✅ Iniciando Voice Bridge...
# 2025-07-07 XX:XX:XX - INFO - === Iniciando Voice Bridge Pathology ===
# 2025-07-07 XX:XX:XX - INFO - ✅ Azure Speech Services configurado correctamente
# 2025-07-07 XX:XX:XX - INFO - Diccionario frases_completas.txt: 26 términos cargados
# 2025-07-07 XX:XX:XX - INFO - Diccionario patologia_molecular.txt: 69 términos cargados
# 2025-07-07 XX:XX:XX - INFO - Total términos médicos personalizados: 95
# 2025-07-07 XX:XX:XX - INFO - Voice Bridge iniciado correctamente
```

### 5.3 Test Basic Functionality
1. **GUI appears**: Voice Bridge window opens
2. **Status shows**: "🟢 Sistema listo"
3. **Press Ctrl+Shift+V**: Should hear "Reconocimiento iniciado"
4. **Say**: "pleomorfismo nuclear" → Should transcribe correctly
5. **Press Ctrl+Shift+S**: Should hear "Reconocimiento detenido"

### 5.4 Test Medical Dictionary
```bash
# Test critical medical terms
# Say each term and verify correct recognition:

# Basic pathology terms
"pleomorfismo nuclear"      # Should NOT be "empleomorfismo"
"carcinoma basocelular"     # Should NOT be "vasocelular"
"células atípicas"          # Should be perfect
"invasión focal"            # Should be perfect
"compatible con"            # Should be perfect

# Long medical phrase
"Observo en la biopsia de piel una hiperqueratosis marcada con células atípicas en la capa basal que muestran pleomorfismo nuclear y invasión focal de la dermis papilar compatible con carcinoma basocelular"
# Should transcribe as single continuous phrase
```

### 5.5 Test System Integration
```bash
# Test application launcher
gtk-launch voice-bridge-pathology

# Should start Voice Bridge successfully

# Test Claude Desktop integration (if installed)
wmctrl -l | grep Claude
# Should show Claude Desktop window if open
```

## 🔧 Step 6: Claude Desktop Integration (Optional)

### 6.1 Install Claude Desktop
```bash
# Download Claude Desktop AppImage
wget -O ~/Applications/claude-desktop.AppImage https://github.com/Anthropic/claude-desktop/releases/latest/download/claude-desktop-linux.AppImage

chmod +x ~/Applications/claude-desktop.AppImage

# Create desktop entry for Claude
cat > ~/.local/share/applications/claude-desktop.desktop << 'EOF'
[Desktop Entry]
Name=Claude Desktop
Exec=/home/$(whoami)/Applications/claude-desktop.AppImage
Icon=claude
Type=Application
Terminal=false
Categories=Network;Utility;
Comment=Claude Desktop for Linux
EOF
```

### 6.2 Test Claude Integration
1. **Start Claude Desktop**
2. **Start Voice Bridge**
3. **Enable "Envío automático a Claude"** in Voice Bridge
4. **Dictate medical observation**
5. **Verify automatic sending to Claude**

## 📝 Post-Installation Configuration

### Audio Optimization
```bash
# Set optimal microphone levels
pactl set-source-volume @DEFAULT_SOURCE@ 85%
pactl set-source-mute @DEFAULT_SOURCE@ false

# Test microphone
arecord -f cd -t wav -d 5 test.wav && aplay test.wav
```

### Performance Optimization
```bash
# Add to ~/.bashrc for better performance
echo "# Voice Bridge optimizations" >> ~/.bashrc
echo "export PYTHONUNBUFFERED=1" >> ~/.bashrc
echo "export PULSE_LATENCY_MSEC=30" >> ~/.bashrc
source ~/.bashrc
```

### Medical Dictionary Customization
```bash
# Add your specific medical terms
~/voice-bridge-claude/scripts/agregar_termino_medico.sh "your_medical_term" patologia_molecular

# Example
~/voice-bridge-claude/scripts/agregar_termino_medico.sh "carcinoma adenoescamoso" patologia_molecular
```

## 🎯 Verification Checklist

After installation, verify these components:

- [ ] **Azure connection**: Test script shows ✅ success
- [ ] **Voice Bridge starts**: GUI appears without errors
- [ ] **95 terms loaded**: Log shows medical dictionaries loaded
- [ ] **Audio works**: Can hear TTS confirmations
- [ ] **Recognition works**: Medical terms recognized correctly
- [ ] **System integration**: Icon appears in applications menu
- [ ] **Hotkeys work**: Ctrl+Shift+V/S controls recognition
- [ ] **Long phrases**: No cuts in medical observations
- [ ] **Claude integration**: Automatic sending works (if configured)

## 🚨 Troubleshooting Common Issues

### Azure Authentication Error
```bash
# Verify key format
echo $AZURE_SPEECH_KEY | wc -c
# Should be 64 characters

# Test key manually
curl -H "Ocp-Apim-Subscription-Key: $AZURE_SPEECH_KEY" \
  "https://$AZURE_SPEECH_REGION.api.cognitive.microsoft.com/sts/v1.0/issuetoken"
```

### Audio Issues
```bash
# List audio devices
pactl list sources short

# Set correct default microphone
pactl set-default-source [your_microphone_id]

# Check permissions
groups $USER | grep audio
```

### Python Dependencies
```bash
# Reinstall if needed
cd ~/voice-bridge-claude/voice-bridge-project
source .venv/bin/activate
pip install --force-reinstall azure-cognitiveservices-speech
```

### GUI Issues
```bash
# Install additional GUI dependencies
sudo apt install python3-tk python3-pil python3-pil.imagetk
```

## 📚 Next Steps

After successful installation:

1. **Read [Usage Guide](USAGE.md)**: Learn daily workflow
2. **Configure Obsidian**: Set up MCP integration for templates
3. **Customize Dictionary**: Add your specific medical terms
4. **Practice Dictation**: Start with short phrases, build to complex observations
5. **Optimize Workflow**: Integrate with your daily pathology routine

## 💡 Tips for Success

- **Speak clearly**: Consistent pace works better than slow speech
- **Use medical terms**: The system is optimized for pathology vocabulary
- **Practice hotkeys**: Muscle memory improves workflow efficiency
- **Customize dictionary**: Add terms specific to your practice
- **Regular updates**: Keep dictionaries current with new terminology

---

**Installation complete! You now have a fully functional Voice Bridge system optimized for molecular pathology.**

For usage instructions, see [USAGE.md](USAGE.md)