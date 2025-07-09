#!/bin/bash

# Voice Bridge Pathology - Automated Installation Script
# This script automates the complete installation process
# Author: Voice Bridge Development Team
# Date: 2025-07-07

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="voice-bridge-pathology"
INSTALL_DIR="$HOME/voice-bridge-claude"
VENV_DIR="$INSTALL_DIR/voice-bridge-project"
PYTHON_MIN_VERSION="3.8"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo "=============================================="
    echo "   Voice Bridge Pathology - Installation    "
    echo "=============================================="
    echo ""
}

# Function to check Python version
check_python_version() {
    print_status "Checking Python version..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        print_status "Found Python $PYTHON_VERSION"
        
        # Compare versions
        if python3 -c "import sys; exit(sys.version_info < (3, 8))"; then
            print_success "Python version is compatible ($PYTHON_VERSION >= $PYTHON_MIN_VERSION)"
        else
            print_error "Python version $PYTHON_VERSION is too old. Minimum required: $PYTHON_MIN_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 not found. Please install Python 3.8 or higher."
        exit 1
    fi
}

# Function to install system dependencies
install_system_dependencies() {
    print_status "Installing system dependencies..."
    
    # Detect package manager
    if command -v apt &> /dev/null; then
        print_status "Detected APT package manager (Ubuntu/Debian)"
        
        # Update package list
        print_status "Updating package list..."
        sudo apt update
        
        # Install required packages
        print_status "Installing required system packages..."
        sudo apt install -y \
            python3-pip \
            python3-venv \
            python3-tk \
            wmctrl \
            xdotool \
            portaudio19-dev \
            build-essential \
            curl \
            wget \
            git
            
        print_success "System dependencies installed successfully"
        
    elif command -v yum &> /dev/null; then
        print_status "Detected YUM package manager (RHEL/CentOS/Fedora)"
        print_warning "YUM-based systems may require manual dependency installation"
        
        sudo yum install -y \
            python3-pip \
            python3-tkinter \
            xdotool \
            portaudio-devel \
            gcc \
            curl \
            wget \
            git
            
    elif command -v pacman &> /dev/null; then
        print_status "Detected Pacman package manager (Arch Linux)"
        
        sudo pacman -S --noconfirm \
            python-pip \
            tk \
            xdotool \
            portaudio \
            base-devel \
            curl \
            wget \
            git
            
    else
        print_warning "Could not detect package manager. Please install dependencies manually:"
        echo "  - Python 3.8+"
        echo "  - python3-pip"
        echo "  - python3-venv"
        echo "  - python3-tk"
        echo "  - wmctrl"
        echo "  - xdotool"
        echo "  - portaudio development headers"
        echo ""
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Function to install UV (modern Python package manager)
install_uv() {
    print_status "Installing UV package manager..."
    
    if command -v uv &> /dev/null; then
        print_success "UV is already installed"
        uv --version
    else
        print_status "Downloading and installing UV..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        
        # Add UV to PATH for current session
        export PATH="$HOME/.cargo/bin:$PATH"
        
        if command -v uv &> /dev/null; then
            print_success "UV installed successfully"
            uv --version
        else
            print_error "UV installation failed"
            exit 1
        fi
    fi
}

# Function to create project structure
create_project_structure() {
    print_status "Creating project structure..."
    
    # Create main directory
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # Create subdirectories
    mkdir -p config/diccionarios
    mkdir -p logs
    mkdir -p assets
    mkdir -p scripts
    
    print_success "Project structure created at $INSTALL_DIR"
}

# Function to setup Python environment
setup_python_environment() {
    print_status "Setting up Python virtual environment..."
    
    cd "$INSTALL_DIR"
    
    # Create virtual environment
    python3 -m venv voice-bridge-project/.venv
    
    # Activate virtual environment
    source voice-bridge-project/.venv/bin/activate
    
    # Upgrade pip
    print_status "Upgrading pip..."
    pip install --upgrade pip
    
    print_success "Virtual environment created and activated"
}

# Function to install Python dependencies
install_python_dependencies() {
    print_status "Installing Python dependencies..."
    
    cd "$VENV_DIR"
    source .venv/bin/activate
    
    # Install core dependencies
    pip install azure-cognitiveservices-speech==1.34.0
    pip install PyAutoGUI==0.9.54
    pip install pynput==1.7.6
    
    # Install development dependencies (optional)
    read -p "Install development dependencies (pytest, black, etc.)? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pip install pytest pytest-cov black isort flake8 mypy
        print_success "Development dependencies installed"
    fi
    
    print_success "Python dependencies installed successfully"
}

# Function to create configuration files
create_configuration_files() {
    print_status "Creating configuration files..."
    
    # Create main configuration file
    cat > "$INSTALL_DIR/config/voice_bridge_config.ini" << 'EOF'
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
confidence_threshold = 0.7
tts_enabled = true
claude_activation_delay = 0.2
EOF

    # Create medical dictionaries
    cat > "$INSTALL_DIR/config/diccionarios/patologia_molecular.txt" << 'EOF'
# Diccionario de Patología Molecular
# Un término por línea
carcinoma basocelular
carcinoma escamocelular
adenocarcinoma
pleomorfismo nuclear
células atípicas
invasión focal
dermis papilar
compatible con
gastritis crónica
metaplasia intestinal
Helicobacter spp
clasificación de Viena
OLGA estadio
OLGIM estadio
hiperqueratosis
paraqueratosis
acantosis
espongiosis
exocitosis
queratinocitos
melanocitos
células dendríticas
infiltrado inflamatorio
fibroblastos
colágeno
elastina
vasos sanguíneos
anexos cutáneos
folículos pilosos
glándulas sebáceas
glándulas sudoríparas
EOF

    cat > "$INSTALL_DIR/config/diccionarios/frases_completas.txt" << 'EOF'
# Frases completas para patología
# Una frase por línea
compatible con neoplasia maligna
negativo para malignidad
células atípicas escasas
infiltrado inflamatorio crónico
cambios reactivos benignos
hiperplasia seudoepiteliomatosa
queratosis actínica severa
carcinoma in situ
invasión de dermis papilar
invasión de dermis reticular
márgenes quirúrgicos libres
márgenes quirúrgicos comprometidos
gastritis crónica moderada
metaplasia intestinal incompleta
displasia de bajo grado
displasia de alto grado
Helicobacter pylori positivo
clasificación de Viena categoría
OLGA estadio tres
OLGIM estadio dos
compatible con Claude
EOF

    print_success "Configuration files created"
}

# Function to create startup scripts
create_startup_scripts() {
    print_status "Creating startup scripts..."
    
    # Create main startup script
    cat > "$INSTALL_DIR/scripts/start_voice_bridge.sh" << 'EOF'
#!/bin/bash

# Voice Bridge Pathology - Startup Script
cd "$(dirname "$0")/.."

echo "=================================="
echo "   Voice Bridge Pathology Start   "
echo "=================================="

# Load environment variables
if [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi

# Check Azure configuration
if [ -z "$AZURE_SPEECH_KEY" ]; then
    echo "⚠️  AZURE_SPEECH_KEY not configured"
    echo "   Set environment variables:"
    echo "   export AZURE_SPEECH_KEY='your_key_here'"
    echo "   export AZURE_SPEECH_REGION='eastus'"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Activate virtual environment
source voice-bridge-project/.venv/bin/activate

# Start application
cd voice-bridge-project
python voice_bridge_app.py

echo "Voice Bridge finished"
EOF

    # Create Azure test script
    cat > "$INSTALL_DIR/scripts/test_azure_connection.sh" << 'EOF'
#!/bin/bash

# Azure Speech Services Connection Test
echo "=== Testing Azure Speech Services ==="

# Check environment variables
if [ -z "$AZURE_SPEECH_KEY" ]; then
    echo "❌ AZURE_SPEECH_KEY not configured"
    exit 1
fi

if [ -z "$AZURE_SPEECH_REGION" ]; then
    echo "⚠️  AZURE_SPEECH_REGION not set, using default: eastus"
    export AZURE_SPEECH_REGION="eastus"
fi

echo "✅ Variables configured"
echo "   Region: $AZURE_SPEECH_REGION"
echo "   Key: ${AZURE_SPEECH_KEY:0:8}..."

# Test connectivity
echo "Testing connectivity..."
response=$(curl -s -w "%{http_code}" \
  -X POST \
  -H "Ocp-Apim-Subscription-Key: $AZURE_SPEECH_KEY" \
  -H "Content-Length: 0" \
  "https://$AZURE_SPEECH_REGION.api.cognitive.microsoft.com/sts/v1.0/issuetoken" \
  -o /dev/null)

if [ "$response" = "200" ]; then
    echo "✅ Azure Speech Services connection successful"
else
    echo "❌ Connection failed (HTTP $response)"
fi
EOF

    # Create term addition script
    cat > "$INSTALL_DIR/scripts/add_medical_term.sh" << 'EOF'
#!/bin/bash

# Add medical term to dictionary
DICT_DIR="../config/diccionarios"

if [ -z "$1" ]; then
    echo "Usage: $0 'medical_term' [category]"
    echo "Categories: patologia_molecular, frases_completas"
    exit 1
fi

TERM="$1"
CATEGORY="${2:-patologia_molecular}"
DICTIONARY="$DICT_DIR/${CATEGORY}.txt"

if [ ! -f "$DICTIONARY" ]; then
    echo "❌ Dictionary $CATEGORY not found"
    exit 1
fi

if grep -qi "^$TERM$" "$DICTIONARY"; then
    echo "⚠️  Term '$TERM' already exists in $CATEGORY"
else
    echo "$TERM" >> "$DICTIONARY"
    echo "✅ Term '$TERM' added to $CATEGORY"
    echo "💡 Restart Voice Bridge to apply changes"
fi
EOF

    # Make scripts executable
    chmod +x "$INSTALL_DIR/scripts/"*.sh
    
    print_success "Startup scripts created"
}

# Function to create desktop entry
create_desktop_entry() {
    print_status "Creating desktop entry..."
    
    DESKTOP_FILE="$HOME/.local/share/applications/voice-bridge-pathology.desktop"
    mkdir -p "$(dirname "$DESKTOP_FILE")"
    
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Voice Bridge Pathology
Comment=Medical voice recognition for pathology professionals
Exec=$INSTALL_DIR/scripts/start_voice_bridge.sh
Icon=$INSTALL_DIR/assets/voice-bridge.png
Terminal=true
Categories=Office;Medical;Development;
Keywords=voice;recognition;medical;pathology;speech;
EOF

    print_success "Desktop entry created"
}

# Function to setup environment variables template
setup_environment_template() {
    print_status "Setting up environment template..."
    
    cat > "$INSTALL_DIR/environment_template.sh" << 'EOF'
#!/bin/bash
# Voice Bridge Pathology - Environment Variables Template
# Copy these lines to your ~/.bashrc file

# Azure Speech Services Configuration
export AZURE_SPEECH_KEY="your_azure_speech_key_here"
export AZURE_SPEECH_REGION="eastus"
export SPEECH_LANGUAGE="es-CO"
export TTS_VOICE="es-CO-SalomeNeural"

# Optional: Add Voice Bridge scripts to PATH
export PATH="$HOME/voice-bridge-claude/scripts:$PATH"

echo "Voice Bridge environment loaded"
EOF

    print_success "Environment template created at $INSTALL_DIR/environment_template.sh"
}

# Function to run post-installation checks
run_post_installation_checks() {
    print_status "Running post-installation checks..."
    
    # Check Python environment
    cd "$VENV_DIR"
    source .venv/bin/activate
    
    if python -c "import azure.cognitiveservices.speech" 2>/dev/null; then
        print_success "Azure Speech SDK is working"
    else
        print_error "Azure Speech SDK not properly installed"
        return 1
    fi
    
    if python -c "import tkinter" 2>/dev/null; then
        print_success "Tkinter is working"
    else
        print_error "Tkinter not available"
        return 1
    fi
    
    # Check system tools
    if command -v wmctrl &> /dev/null; then
        print_success "wmctrl is available"
    else
        print_warning "wmctrl not found - Claude integration may not work"
    fi
    
    if command -v xdotool &> /dev/null; then
        print_success "xdotool is available"
    else
        print_warning "xdotool not found - Claude integration may not work"
    fi
    
    print_success "Post-installation checks completed"
}

# Function to print installation summary
print_installation_summary() {
    print_success "Installation completed successfully!"
    echo ""
    echo "=============================================="
    echo "   Installation Summary"
    echo "=============================================="
    echo ""
    echo "📁 Installation directory: $INSTALL_DIR"
    echo "🐍 Python environment: $VENV_DIR/.venv"
    echo "⚙️  Configuration: $INSTALL_DIR/config/"
    echo "📝 Logs: $INSTALL_DIR/logs/"
    echo "🚀 Scripts: $INSTALL_DIR/scripts/"
    echo ""
    echo "Next steps:"
    echo "1. Configure Azure Speech Services:"
    echo "   - Add these lines to ~/.bashrc:"
    echo "     export AZURE_SPEECH_KEY='your_key_here'"
    echo "     export AZURE_SPEECH_REGION='eastus'"
    echo "   - Or edit: $INSTALL_DIR/config/voice_bridge_config.ini"
    echo ""
    echo "2. Test Azure connection:"
    echo "   $INSTALL_DIR/scripts/test_azure_connection.sh"
    echo ""
    echo "3. Start Voice Bridge:"
    echo "   $INSTALL_DIR/scripts/start_voice_bridge.sh"
    echo ""
    echo "4. Add custom medical terms:"
    echo "   $INSTALL_DIR/scripts/add_medical_term.sh 'new term' patologia_molecular"
    echo ""
    print_warning "Remember: Configure AZURE_SPEECH_KEY before first use!"
}

# Main installation function
main() {
    print_header
    
    # Check if running as root
    if [ "$EUID" -eq 0 ]; then
        print_error "Do not run this script as root (sudo)"
        exit 1
    fi
    
    # Installation steps
    check_python_version
    install_system_dependencies
    install_uv  # Optional but recommended
    create_project_structure
    setup_python_environment
    install_python_dependencies
    create_configuration_files
    create_startup_scripts
    create_desktop_entry
    setup_environment_template
    run_post_installation_checks
    print_installation_summary
    
    print_success "Voice Bridge Pathology installation completed!"
}

# Run main function
main "$@"
