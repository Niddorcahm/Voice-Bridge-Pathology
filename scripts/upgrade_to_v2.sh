#!/bin/bash
#
# Voice Bridge v1 to v2 Upgrade Script
# This script helps migrate from Voice Bridge v1.x to v2.0
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "==========================================="
echo "   Voice Bridge v2.0 Upgrade Script"
echo "==========================================="
echo

# Check if we're in the right directory
if [ ! -f "$PROJECT_DIR/voice_bridge_app.py" ]; then
    echo "❌ Error: voice_bridge_app.py not found"
    echo "   Please run this script from the voice-bridge-pathology directory"
    exit 1
fi

# Function to create backup
create_backup() {
    echo "📦 Creating backup of current installation..."
    
    BACKUP_DIR="$PROJECT_DIR/backup_v1_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup Python files
    if [ -f "$PROJECT_DIR/voice_bridge_app.py" ]; then
        cp "$PROJECT_DIR/voice_bridge_app.py" "$BACKUP_DIR/"
        echo "   ✓ Backed up voice_bridge_app.py"
    fi
    
    # Backup configuration
    if [ -d "$PROJECT_DIR/config" ]; then
        cp -r "$PROJECT_DIR/config" "$BACKUP_DIR/"
        echo "   ✓ Backed up config directory"
    fi
    
    echo "   ✓ Backup created in: $BACKUP_DIR"
    echo
}

# Function to update configuration
update_configuration() {
    echo "⚙️  Updating configuration..."
    
    CONFIG_DIR="$PROJECT_DIR/config"
    V1_CONFIG="$CONFIG_DIR/voice_bridge_config.ini"
    V2_CONFIG="$CONFIG_DIR/voice_bridge_config_v2.ini"
    
    # Create v2 config if it doesn't exist
    if [ -f "$V1_CONFIG" ] && [ ! -f "$V2_CONFIG" ]; then
        echo "   Creating v2 configuration from v1..."
        cp "$V1_CONFIG" "$V2_CONFIG"
        
        # Add v2 specific settings
        cat >> "$V2_CONFIG" << 'EOF'

# ===== Voice Bridge v2.0 Settings =====
# Added by upgrade script

# Dictation mode: continuous or segmented
dictation_mode = continuous

# Anti-coupling prevents TTS from being transcribed
anti_coupling = true
tts_during_dictation = false

# Medical term auto-correction
auto_correct_medical = true

# Timeout settings (in seconds)
dictation_timeout_seconds = 8
timeout_warning_seconds = 3
timeout_audio_warning = true

# Command detection settings
command_confidence_threshold = 0.7
repetition_threshold = 0.85

# GUI enhancements
show_buffer_display = true
show_timeout_progress = true
EOF
        
        echo "   ✓ Created voice_bridge_config_v2.ini"
    elif [ -f "$V2_CONFIG" ]; then
        echo "   ✓ v2 configuration already exists"
    else
        echo "   ⚠️  No configuration found, using example"
        if [ -f "$CONFIG_DIR/voice_bridge_config_v2.ini.example" ]; then
            cp "$CONFIG_DIR/voice_bridge_config_v2.ini.example" "$V2_CONFIG"
            echo "   ✓ Created v2 configuration from example"
        fi
    fi
    echo
}

# Function to check dependencies
check_dependencies() {
    echo "🔍 Checking dependencies..."
    
    # Check Python version
    PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
    echo "   Python version: $PYTHON_VERSION"
    
    # Check if virtual environment exists
    if [ -d "$PROJECT_DIR/.venv" ]; then
        echo "   ✓ Virtual environment found"
        
        # Activate venv
        source "$PROJECT_DIR/.venv/bin/activate"
        
        # Check Azure Speech SDK
        if pip show azure-cognitiveservices-speech &> /dev/null; then
            SDK_VERSION=$(pip show azure-cognitiveservices-speech | grep Version | cut -d' ' -f2)
            echo "   ✓ Azure Speech SDK installed (v$SDK_VERSION)"
            
            # Check version compatibility
            if [[ "$SDK_VERSION" < "1.35.0" ]]; then
                echo "   ⚠️  SDK version is old, updating..."
                pip install --upgrade azure-cognitiveservices-speech
            fi
        else
            echo "   ⚠️  Azure Speech SDK not found, installing..."
            pip install azure-cognitiveservices-speech
        fi
        
        # Check other dependencies
        echo "   Checking other dependencies..."
        pip install -q pyautogui pynput pyyaml requests python-dotenv tkinter-tooltip
        echo "   ✓ All Python dependencies installed"
        
    else
        echo "   ⚠️  Virtual environment not found"
        echo "   Please create it with: python3 -m venv .venv"
    fi
    
    # Check system dependencies
    echo "   Checking system dependencies..."
    for cmd in wmctrl xdotool; do
        if command -v $cmd &> /dev/null; then
            echo "   ✓ $cmd is installed"
        else
            echo "   ❌ $cmd is NOT installed"
            echo "      Install with: sudo apt install $cmd"
        fi
    done
    echo
}

# Function to update launcher scripts
update_launchers() {
    echo "🚀 Updating launcher scripts..."
    
    # Create v2 launcher
    V2_LAUNCHER="$PROJECT_DIR/start_voice_bridge_v2.sh"
    
    cat > "$V2_LAUNCHER" << 'EOF'
#!/bin/bash
# Voice Bridge v2.0 Launcher

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starting Voice Bridge v2.0..."

# Check for virtual environment
if [ ! -d "$SCRIPT_DIR/voice-bridge-project/.venv" ]; then
    echo "❌ Virtual environment not found"
    echo "Please run the installation script first"
    exit 1
fi

# Activate virtual environment
source "$SCRIPT_DIR/voice-bridge-project/.venv/bin/activate"

# Check Azure key
if [ -z "$AZURE_SPEECH_KEY" ]; then
    echo "⚠️  AZURE_SPEECH_KEY not set in environment"
    echo "Using configuration file settings..."
fi

# Start Voice Bridge v2
cd "$SCRIPT_DIR/voice-bridge-project"
python3 voice_bridge_app.py

# Deactivate on exit
deactivate
EOF
    
    chmod +x "$V2_LAUNCHER"
    echo "   ✓ Created start_voice_bridge_v2.sh"
    
    # Update desktop entry if exists
    DESKTOP_FILE="$HOME/.local/share/applications/voice-bridge-pathology.desktop"
    if [ -f "$DESKTOP_FILE" ]; then
        echo "   Updating desktop entry..."
        sed -i "s|Exec=.*|Exec=$V2_LAUNCHER|g" "$DESKTOP_FILE"
        sed -i "s|Name=.*|Name=Voice Bridge v2|g" "$DESKTOP_FILE"
        echo "   ✓ Updated desktop entry"
    fi
    echo
}

# Function to show post-upgrade instructions
show_instructions() {
    echo "✅ Upgrade preparation complete!"
    echo
    echo "📋 Next steps:"
    echo
    echo "1. Update voice_bridge_app.py with the v2 code:"
    echo "   - Replace the entire file with the v2.0 version"
    echo "   - The v1 backup is saved in the backup directory"
    echo
    echo "2. Review your configuration:"
    echo "   - Check config/voice_bridge_config_v2.ini"
    echo "   - Update your Azure Speech key if needed"
    echo "   - Adjust timeout and behavior settings"
    echo
    echo "3. Test the upgrade:"
    echo "   - Run: ./start_voice_bridge_v2.sh"
    echo "   - Or use: python3 voice_bridge_app.py"
    echo
    echo "4. Test new features:"
    echo "   - Try 'inicio dictado' voice command"
    echo "   - Test the 8-second timeout"
    echo "   - Verify medical term corrections"
    echo
    echo "📚 Documentation:"
    echo "   - README.md - Updated for v2"
    echo "   - docs/VOICE_COMMANDS.md - Command reference"
    echo "   - docs/DICTATION_MODE.md - Dictation guide"
    echo
    echo "⚠️  Important notes:"
    echo "   - The v1 backup is in: backup_v1_*/"
    echo "   - Configuration is now: voice_bridge_config_v2.ini"
    echo "   - Some Azure properties require SDK 1.35.0+"
    echo
}

# Main upgrade process
main() {
    echo "This script will prepare your Voice Bridge installation for v2.0"
    echo "Your current installation will be backed up first."
    echo
    read -p "Continue with upgrade? (y/n) " -n 1 -r
    echo
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Upgrade cancelled."
        exit 0
    fi
    
    # Run upgrade steps
    create_backup
    update_configuration
    check_dependencies
    update_launchers
    show_instructions
}

# Run main function
main