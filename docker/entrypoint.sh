#!/bin/bash

# Voice Bridge Pathology - Docker Entrypoint Script
# Handles initialization and runtime configuration for containerized deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[DOCKER]${NC} $1"
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

# Function to check required environment variables
check_environment() {
    print_status "Checking environment variables..."
    
    # Check Azure credentials
    if [ -z "$AZURE_SPEECH_KEY" ]; then
        print_error "AZURE_SPEECH_KEY environment variable is required"
        print_status "Set it with: docker run -e AZURE_SPEECH_KEY=your_key ..."
        exit 1
    fi
    
    if [ -z "$AZURE_SPEECH_REGION" ]; then
        print_warning "AZURE_SPEECH_REGION not set, using default: eastus"
        export AZURE_SPEECH_REGION="eastus"
    fi
    
    print_success "Environment variables validated"
}

# Function to setup directories and permissions
setup_directories() {
    print_status "Setting up directories..."
    
    # Create necessary directories
    mkdir -p /app/logs
    mkdir -p /app/audit-logs
    mkdir -p /app/backups
    mkdir -p /app/config/diccionarios
    
    # Set proper permissions (user should already own /app)
    chmod 755 /app/logs
    chmod 755 /app/audit-logs
    chmod 755 /app/backups
    chmod 755 /app/config
    chmod 755 /app/config/diccionarios
    
    print_success "Directories configured"
}

# Function to initialize configuration
init_configuration() {
    print_status "Initializing configuration..."
    
    # If no config file exists, create from template
    if [ ! -f "/app/config/voice_bridge_config.ini" ]; then
        print_status "Creating default configuration file..."
        
        cat > /app/config/voice_bridge_config.ini << EOF
[DEFAULT]
# Azure Cognitive Services Configuration
azure_speech_key = ${AZURE_SPEECH_KEY}
azure_region = ${AZURE_SPEECH_REGION}
speech_language = ${SPEECH_LANGUAGE:-es-CO}
tts_voice = ${TTS_VOICE:-es-CO-SalomeNeural}

# Application Settings
hotkey_start = ctrl+shift+v
hotkey_stop = ctrl+shift+s
hotkey_emergency = ctrl+shift+x
auto_send_to_claude = false
claude_window_title = Claude
medical_mode = ${MEDICAL_MODE:-true}
confidence_threshold = 0.7
tts_enabled = true
claude_activation_delay = 0.2

# Security and Compliance
hipaa_compliance = ${HIPAA_COMPLIANCE:-true}
encrypt_transcriptions = ${ENCRYPT_TRANSCRIPTIONS:-true}
audit_logging = ${AUDIT_LOGGING:-true}
detailed_audit_trails = true
data_retention_days = ${DATA_RETENTION_DAYS:-2555}

# Performance Settings
debug_mode = ${DEBUG_MODE:-false}
max_session_duration = 480
auto_save_transcriptions = true
auto_save_interval = 5
EOF
        
        chmod 600 /app/config/voice_bridge_config.ini
        print_success "Configuration file created"
    else
        print_success "Using existing configuration file"
    fi
}

# Function to setup virtual display for GUI applications
setup_display() {
    print_status "Setting up virtual display..."
    
    # Start Xvfb if DISPLAY is set to :99 (headless mode)
    if [ "$DISPLAY" = ":99" ]; then
        print_status "Starting virtual display for headless operation..."
        Xvfb :99 -screen 0 1024x768x24 -ac +extension GLX +render -noreset &
        export XVFB_PID=$!
        sleep 2
        print_success "Virtual display started (PID: $XVFB_PID)"
    else
        print_status "Using host display: $DISPLAY"
    fi
}

# Function to setup audio system
setup_audio() {
    print_status "Setting up audio system..."
    
    # Check if audio devices are accessible
    if [ -e "/dev/snd" ]; then
        print_success "Audio devices found"
    else
        print_warning "No audio devices found - voice recognition may not work"
    fi
    
    # Initialize PulseAudio in container if needed
    if command -v pulseaudio &> /dev/null; then
        print_status "Initializing PulseAudio..."
        # Start PulseAudio in system mode for container
        pulseaudio --system --disallow-exit --disallow-module-loading=false &
        sleep 2
        print_success "PulseAudio initialized"
    fi
}

# Function to validate medical dictionaries
validate_dictionaries() {
    print_status "Validating medical dictionaries..."
    
    dict_dir="/app/config/diccionarios"
    
    # Check primary dictionary
    if [ ! -f "$dict_dir/patologia_molecular.txt" ]; then
        print_warning "Primary dictionary missing, creating default..."
        echo "# Default Pathology Dictionary" > "$dict_dir/patologia_molecular.txt"
        echo "carcinoma basocelular" >> "$dict_dir/patologia_molecular.txt"
        echo "adenocarcinoma" >> "$dict_dir/patologia_molecular.txt"
        echo "pleomorfismo nuclear" >> "$dict_dir/patologia_molecular.txt"
    fi
    
    # Check phrases dictionary
    if [ ! -f "$dict_dir/frases_completas.txt" ]; then
        print_warning "Phrases dictionary missing, creating default..."
        echo "# Default Phrases Dictionary" > "$dict_dir/frases_completas.txt"
        echo "compatible con neoplasia maligna" >> "$dict_dir/frases_completas.txt"
        echo "negativo para malignidad" >> "$dict_dir/frases_completas.txt"
    fi
    
    # Count terms
    primary_count=$(grep -v '^#' "$dict_dir/patologia_molecular.txt" | grep -v '^$' | wc -l)
    phrases_count=$(grep -v '^#' "$dict_dir/frases_completas.txt" | grep -v '^$' | wc -l)
    
    print_success "Medical dictionaries validated (Primary: $primary_count terms, Phrases: $phrases_count)"
}

# Function to test Azure connectivity
test_azure_connectivity() {
    print_status "Testing Azure Speech Services connectivity..."
    
    # Test Azure endpoint
    response=$(curl -s -w "%{http_code}" \
        -X POST \
        -H "Ocp-Apim-Subscription-Key: $AZURE_SPEECH_KEY" \
        -H "Content-Length: 0" \
        "https://$AZURE_SPEECH_REGION.api.cognitive.microsoft.com/sts/v1.0/issuetoken" \
        -o /dev/null 2>/dev/null || echo "000")
    
    if [ "$response" = "200" ]; then
        print_success "Azure connectivity test successful"
    elif [ "$response" = "401" ]; then
        print_error "Azure authentication failed - check AZURE_SPEECH_KEY"
        exit 1
    elif [ "$response" = "403" ]; then
        print_error "Azure access forbidden - check subscription status"
        exit 1
    else
        print_warning "Azure connectivity test failed (HTTP $response) - continuing anyway"
    fi
}

# Function to setup logging
setup_logging() {
    print_status "Setting up logging..."
    
    # Create log files with proper permissions
    touch /app/logs/voice_bridge_$(date +%Y%m%d).log
    touch /app/audit-logs/audit_$(date +%Y%m%d).log
    
    chmod 644 /app/logs/*.log 2>/dev/null || true
    chmod 644 /app/audit-logs/*.log 2>/dev/null || true
    
    print_success "Logging configured"
}

# Function to cleanup on exit
cleanup() {
    print_status "Cleaning up..."
    
    # Kill Xvfb if we started it
    if [ -n "$XVFB_PID" ]; then
        kill $XVFB_PID 2>/dev/null || true
    fi
    
    # Kill PulseAudio if running
    pkill pulseaudio 2>/dev/null || true
    
    print_success "Cleanup completed"
}

# Set up signal handlers
trap cleanup EXIT INT TERM

# Main initialization sequence
main() {
    print_status "Starting Voice Bridge Pathology container initialization..."
    echo ""
    
    check_environment
    setup_directories
    init_configuration
    setup_display
    setup_audio
    validate_dictionaries
    setup_logging
    test_azure_connectivity
    
    echo ""
    print_success "Container initialization completed successfully!"
    print_status "Starting Voice Bridge Pathology application..."
    echo ""
    
    # Execute the main command
    exec "$@"
}

# Run main function with all arguments
main "$@"
