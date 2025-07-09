#!/bin/bash

# Voice Bridge Pathology - Configuration Validation Script
# Validates all configuration files and system requirements

set -e

# Configuration
INSTALL_DIR="$HOME/voice-bridge-claude"
CONFIG_FILE="$INSTALL_DIR/config/voice_bridge_config.ini"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Validation counters
ERRORS=0
WARNINGS=0
CHECKS=0

# Function to increment counters
increment_check() {
    CHECKS=$((CHECKS + 1))
}

increment_error() {
    ERRORS=$((ERRORS + 1))
    increment_check
}

increment_warning() {
    WARNINGS=$((WARNINGS + 1))
    increment_check
}

increment_success() {
    increment_check
}

# Validate installation directory
validate_installation() {
    print_status "Validating installation structure..."
    
    if [ -d "$INSTALL_DIR" ]; then
        print_success "Installation directory exists"
        increment_success
    else
        print_error "Installation directory not found: $INSTALL_DIR"
        increment_error
        return
    fi
    
    # Check required subdirectories
    local required_dirs=("config" "logs" "assets" "scripts")
    for dir in "${required_dirs[@]}"; do
        if [ -d "$INSTALL_DIR/$dir" ]; then
            print_success "Directory exists: $dir"
            increment_success
        else
            print_warning "Directory missing: $dir"
            increment_warning
        fi
    done
}

# Validate Python environment
validate_python_environment() {
    print_status "Validating Python environment..."
    
    # Check Python version
    if command -v python3 &> /dev/null; then
        python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        print_success "Python 3 available: $python_version"
        increment_success
        
        # Check if version is adequate
        if python3 -c "import sys; exit(sys.version_info < (3, 8))"; then
            print_success "Python version is compatible (>= 3.8)"
            increment_success
        else
            print_error "Python version is too old. Minimum required: 3.8"
            increment_error
        fi
    else
        print_error "Python 3 not found"
        increment_error
    fi
    
    # Check virtual environment
    venv_path="$INSTALL_DIR/voice-bridge-project/.venv"
    if [ -d "$venv_path" ]; then
        print_success "Virtual environment exists"
        increment_success
        
        # Activate and check packages
        if source "$venv_path/bin/activate" 2>/dev/null; then
            print_success "Virtual environment activated successfully"
            increment_success
            
            # Check required packages
            if python -c "import azure.cognitiveservices.speech" 2>/dev/null; then
                print_success "Azure Speech SDK available"
                increment_success
            else
                print_error "Azure Speech SDK not installed"
                increment_error
            fi
            
            if python -c "import tkinter" 2>/dev/null; then
                print_success "Tkinter available"
                increment_success
            else
                print_error "Tkinter not available"
                increment_error
            fi
            
            if python -c "import pyautogui" 2>/dev/null; then
                print_success "PyAutoGUI available"
                increment_success
            else
                print_warning "PyAutoGUI not installed (optional)"
                increment_warning
            fi
            
            if python -c "import pynput" 2>/dev/null; then
                print_success "Pynput available"
                increment_success
            else
                print_warning "Pynput not installed (required for hotkeys)"
                increment_error
            fi
        else
            print_error "Could not activate virtual environment"
            increment_error
        fi
    else
        print_error "Virtual environment not found"
        increment_error
    fi
}

# Validate system dependencies
validate_system_dependencies() {
    print_status "Validating system dependencies..."
    
    # Check wmctrl
    if command -v wmctrl &> /dev/null; then
        print_success "wmctrl available"
        increment_success
    else
        print_error "wmctrl not found (required for Claude integration)"
        increment_error
    fi
    
    # Check xdotool
    if command -v xdotool &> /dev/null; then
        print_success "xdotool available"
        increment_success
    else
        print_error "xdotool not found (required for Claude integration)"
        increment_error
    fi
    
    # Check audio system
    if command -v pactl &> /dev/null; then
        print_success "PulseAudio available"
        increment_success
    elif command -v aplay &> /dev/null; then
        print_success "ALSA available"
        increment_success
    else
        print_warning "Audio system uncertain - may affect microphone access"
        increment_warning
    fi
}

# Validate configuration file
validate_configuration_file() {
    print_status "Validating configuration file..."
    
    if [ -f "$CONFIG_FILE" ]; then
        print_success "Configuration file exists"
        increment_success
        
        # Check critical settings
        if grep -q "azure_speech_key.*=" "$CONFIG_FILE"; then
            azure_key=$(grep "azure_speech_key" "$CONFIG_FILE" | cut -d'=' -f2 | xargs)
            if [ -n "$azure_key" ] && [ "$azure_key" != "your_azure_speech_key_here" ]; then
                print_success "Azure Speech key configured"
                increment_success
            else
                print_error "Azure Speech key not configured"
                increment_error
            fi
        else
            print_error "Azure Speech key setting missing"
            increment_error
        fi
        
        if grep -q "azure_region.*=" "$CONFIG_FILE"; then
            print_success "Azure region configured"
            increment_success
        else
            print_warning "Azure region setting missing"
            increment_warning
        fi
        
        if grep -q "speech_language.*=" "$CONFIG_FILE"; then
            print_success "Speech language configured"
            increment_success
        else
            print_warning "Speech language setting missing"
            increment_warning
        fi
        
    else
        print_error "Configuration file not found: $CONFIG_FILE"
        increment_error
    fi
}

# Validate environment variables
validate_environment_variables() {
    print_status "Validating environment variables..."
    
    if [ -n "$AZURE_SPEECH_KEY" ]; then
        print_success "AZURE_SPEECH_KEY environment variable set"
        increment_success
    else
        print_warning "AZURE_SPEECH_KEY environment variable not set"
        increment_warning
    fi
    
    if [ -n "$AZURE_SPEECH_REGION" ]; then
        print_success "AZURE_SPEECH_REGION environment variable set"
        increment_success
    else
        print_warning "AZURE_SPEECH_REGION environment variable not set"
        increment_warning
    fi
}

# Validate medical dictionaries
validate_medical_dictionaries() {
    print_status "Validating medical dictionaries..."
    
    dict_dir="$INSTALL_DIR/config/diccionarios"
    if [ -d "$dict_dir" ]; then
        print_success "Medical dictionaries directory exists"
        increment_success
        
        # Check primary dictionary
        if [ -f "$dict_dir/patologia_molecular.txt" ]; then
            term_count=$(wc -l < "$dict_dir/patologia_molecular.txt")
            print_success "Primary dictionary exists ($term_count terms)"
            increment_success
        else
            print_warning "Primary dictionary missing: patologia_molecular.txt"
            increment_warning
        fi
        
        # Check phrases dictionary
        if [ -f "$dict_dir/frases_completas.txt" ]; then
            phrase_count=$(wc -l < "$dict_dir/frases_completas.txt")
            print_success "Phrases dictionary exists ($phrase_count phrases)"
            increment_success
        else
            print_warning "Phrases dictionary missing: frases_completas.txt"
            increment_warning
        fi
        
        # Check for empty dictionaries
        for dict_file in "$dict_dir"/*.txt; do
            if [ -f "$dict_file" ]; then
                if [ -s "$dict_file" ]; then
                    dict_name=$(basename "$dict_file")
                    print_success "Dictionary not empty: $dict_name"
                    increment_success
                else
                    dict_name=$(basename "$dict_file")
                    print_warning "Dictionary is empty: $dict_name"
                    increment_warning
                fi
            fi
        done
        
    else
        print_error "Medical dictionaries directory not found"
        increment_error
    fi
}

# Validate scripts
validate_scripts() {
    print_status "Validating scripts..."
    
    scripts_dir="$INSTALL_DIR/scripts"
    if [ -d "$scripts_dir" ]; then
        print_success "Scripts directory exists"
        increment_success
        
        # Check for essential scripts
        local required_scripts=("start_voice_bridge.sh" "test_azure_connection.sh" "add_medical_term.sh")
        for script in "${required_scripts[@]}"; do
            script_path="$scripts_dir/$script"
            if [ -f "$script_path" ]; then
                if [ -x "$script_path" ]; then
                    print_success "Script exists and executable: $script"
                    increment_success
                else
                    print_warning "Script exists but not executable: $script"
                    increment_warning
                fi
            else
                print_warning "Script missing: $script"
                increment_warning
            fi
        done
    else
        print_warning "Scripts directory not found"
        increment_warning
    fi
}

# Test Azure connectivity
test_azure_connectivity() {
    print_status "Testing Azure connectivity..."
    
    # Get Azure configuration
    azure_key=""
    azure_region=""
    
    # Try environment variables first
    if [ -n "$AZURE_SPEECH_KEY" ]; then
        azure_key="$AZURE_SPEECH_KEY"
    elif [ -f "$CONFIG_FILE" ]; then
        azure_key=$(grep "azure_speech_key" "$CONFIG_FILE" | cut -d'=' -f2 | xargs)
    fi
    
    if [ -n "$AZURE_SPEECH_REGION" ]; then
        azure_region="$AZURE_SPEECH_REGION"
    elif [ -f "$CONFIG_FILE" ]; then
        azure_region=$(grep "azure_region" "$CONFIG_FILE" | cut -d'=' -f2 | xargs)
    fi
    
    if [ -n "$azure_key" ] && [ "$azure_key" != "your_azure_speech_key_here" ] && [ -n "$azure_region" ]; then
        print_status "Testing Azure Speech Services connectivity..."
        
        response=$(curl -s -w "%{http_code}" \
            -X POST \
            -H "Ocp-Apim-Subscription-Key: $azure_key" \
            -H "Content-Length: 0" \
            "https://$azure_region.api.cognitive.microsoft.com/sts/v1.0/issuetoken" \
            -o /dev/null 2>/dev/null || echo "000")
        
        if [ "$response" = "200" ]; then
            print_success "Azure Speech Services connectivity successful"
            increment_success
        elif [ "$response" = "401" ]; then
            print_error "Azure authentication failed (invalid key)"
            increment_error
        elif [ "$response" = "403" ]; then
            print_error "Azure access forbidden (check subscription)"
            increment_error
        else
            print_warning "Azure connectivity test failed (HTTP $response)"
            increment_warning
        fi
    else
        print_warning "Azure credentials not configured - skipping connectivity test"
        increment_warning
    fi
}

# Validate file permissions
validate_permissions() {
    print_status "Validating file permissions..."
    
    # Check if user can write to installation directory
    if [ -w "$INSTALL_DIR" ]; then
        print_success "Installation directory is writable"
        increment_success
    else
        print_error "Installation directory is not writable"
        increment_error
    fi
    
    # Check logs directory
    if [ -d "$INSTALL_DIR/logs" ]; then
        if [ -w "$INSTALL_DIR/logs" ]; then
            print_success "Logs directory is writable"
            increment_success
        else
            print_error "Logs directory is not writable"
            increment_error
        fi
    fi
    
    # Check config directory
    if [ -d "$INSTALL_DIR/config" ]; then
        if [ -w "$INSTALL_DIR/config" ]; then
            print_success "Config directory is writable"
            increment_success
        else
            print_error "Config directory is not writable"
            increment_error
        fi
    fi
}

# Generate validation report
generate_report() {
    local report_file="$INSTALL_DIR/validation_report_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$report_file" << EOF
# Voice Bridge Pathology - Validation Report
# Generated: $(date)

## Summary
- Total checks: $CHECKS
- Successful: $((CHECKS - ERRORS - WARNINGS))
- Warnings: $WARNINGS  
- Errors: $ERRORS

## System Information
- System: $(uname -a)
- Python: $(python3 --version 2>/dev/null || echo "Not found")
- User: $(whoami)
- Installation: $INSTALL_DIR

## Validation Results
EOF

    if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
        echo "✅ ALL CHECKS PASSED - System ready for use" >> "$report_file"
    elif [ $ERRORS -eq 0 ]; then
        echo "⚠️  MINOR ISSUES FOUND - System usable with warnings" >> "$report_file"
    else
        echo "❌ CRITICAL ISSUES FOUND - System may not work properly" >> "$report_file"
    fi
    
    echo "" >> "$report_file"
    echo "For detailed validation output, run this script again." >> "$report_file"
    
    print_status "Validation report saved: $report_file"
}

# Main validation function
main() {
    echo "================================================"
    echo "   Voice Bridge Pathology - System Validation  "
    echo "================================================"
    echo ""
    
    validate_installation
    validate_python_environment
    validate_system_dependencies
    validate_configuration_file
    validate_environment_variables
    validate_medical_dictionaries
    validate_scripts
    validate_permissions
    test_azure_connectivity
    
    echo ""
    echo "================================================"
    echo "   Validation Summary                           "
    echo "================================================"
    echo ""
    
    print_status "Total checks performed: $CHECKS"
    print_success "Successful: $((CHECKS - ERRORS - WARNINGS))"
    
    if [ $WARNINGS -gt 0 ]; then
        print_warning "Warnings: $WARNINGS"
    fi
    
    if [ $ERRORS -gt 0 ]; then
        print_error "Errors: $ERRORS"
    fi
    
    echo ""
    
    if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
        print_success "ALL CHECKS PASSED! System is ready for use."
        echo ""
        echo "You can now start Voice Bridge with:"
        echo "  $INSTALL_DIR/scripts/start_voice_bridge.sh"
        generate_report
        exit 0
    elif [ $ERRORS -eq 0 ]; then
        print_warning "System is usable but has minor issues."
        echo ""
        echo "Review the warnings above and consider fixing them for optimal performance."
        generate_report
        exit 1
    else
        print_error "CRITICAL ISSUES FOUND! System may not work properly."
        echo ""
        echo "Please fix the errors above before using Voice Bridge."
        echo ""
        echo "Common solutions:"
        echo "  - Run the installation script: ./install.sh"
        echo "  - Configure Azure credentials in ~/.bashrc or config file"
        echo "  - Install missing system packages"
        echo "  - Fix file permissions"
        generate_report
        exit 2
    fi
}

# Run main function
main "$@"
