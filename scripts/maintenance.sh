#!/bin/bash

# Voice Bridge Pathology - System Maintenance Script
# Comprehensive maintenance tool for Voice Bridge Pathology
# Handles cleanup, optimization, monitoring, and health checks

set -e

# Configuration
INSTALL_DIR="$HOME/voice-bridge-claude"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$INSTALL_DIR/logs/maintenance_$(date +%Y%m%d).log"
BACKUP_DIR="$INSTALL_DIR/backups"
CONFIG_FILE="$INSTALL_DIR/config/voice_bridge_config.ini"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

log_header() {
    echo -e "${PURPLE}[MAINTENANCE]${NC} $1" | tee -a "$LOG_FILE"
}

# Initialize maintenance
init_maintenance() {
    log_header "Voice Bridge Pathology - System Maintenance"
    log_info "Maintenance started at $(date)"
    log_info "Installation directory: $INSTALL_DIR"
    
    # Create log directory if needed
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Verify installation
    if [ ! -d "$INSTALL_DIR" ]; then
        log_error "Voice Bridge installation not found at $INSTALL_DIR"
        exit 1
    fi
}

# System health check
health_check() {
    log_header "System Health Check"
    
    local errors=0
    local warnings=0
    
    # Check Python environment
    if command -v python3 &> /dev/null; then
        python_version=$(python3 --version 2>&1)
        log_success "Python available: $python_version"
    else
        log_error "Python 3 not found"
        ((errors++))
    fi
    
    # Check virtual environment
    if [ -d "$INSTALL_DIR/voice-bridge-project/.venv" ]; then
        log_success "Virtual environment present"
    else
        log_warning "Virtual environment missing"
        ((warnings++))
    fi
    
    # Check system dependencies
    local deps=("wmctrl" "xdotool" "curl" "pactl")
    for dep in "${deps[@]}"; do
        if command -v "$dep" &> /dev/null; then
            log_success "$dep available"
        else
            log_warning "$dep missing"
            ((warnings++))
        fi
    done
    
    # Check audio system
    if [ -e "/dev/snd" ]; then
        log_success "Audio devices found"
    else
        log_warning "No audio devices detected"
        ((warnings++))
    fi
    
    # Check configuration
    if [ -f "$CONFIG_FILE" ]; then
        log_success "Configuration file present"
        
        # Check Azure configuration
        if grep -q "azure_speech_key.*=" "$CONFIG_FILE"; then
            azure_key=$(grep "azure_speech_key" "$CONFIG_FILE" | cut -d'=' -f2 | xargs)
            if [ -n "$azure_key" ] && [ "$azure_key" != "your_azure_speech_key_here" ]; then
                log_success "Azure Speech key configured"
            else
                log_warning "Azure Speech key not configured"
                ((warnings++))
            fi
        fi
    else
        log_error "Configuration file missing"
        ((errors++))
    fi
    
    # Check medical dictionaries
    if [ -d "$INSTALL_DIR/config/diccionarios" ]; then
        local dict_count=0
        for dict in "$INSTALL_DIR/config/diccionarios"/*.txt; do
            if [ -f "$dict" ]; then
                term_count=$(grep -v '^#' "$dict" | grep -v '^$' | wc -l)
                dict_name=$(basename "$dict")
                log_success "Medical dictionary: $dict_name ($term_count terms)"
                ((dict_count++))
            fi
        done
        
        if [ $dict_count -eq 0 ]; then
            log_warning "No medical dictionaries found"
            ((warnings++))
        fi
    else
        log_error "Medical dictionaries directory missing"
        ((errors++))
    fi
    
    # Summary
    log_header "Health Check Summary"
    if [ $errors -eq 0 ] && [ $warnings -eq 0 ]; then
        log_success "System is healthy - no issues found"
        return 0
    elif [ $errors -eq 0 ]; then
        log_warning "System is functional with $warnings warning(s)"
        return 1
    else
        log_error "System has $errors error(s) and $warnings warning(s)"
        return 2
    fi
}

# Clean old files
cleanup_files() {
    log_header "File Cleanup"
    
    local cleaned_files=0
    local freed_space=0
    
    # Clean old log files (older than 30 days)
    if [ -d "$INSTALL_DIR/logs" ]; then
        log_info "Cleaning old log files..."
        while IFS= read -r -d '' file; do
            size=$(stat -c%s "$file" 2>/dev/null || echo 0)
            rm "$file"
            ((cleaned_files++))
            ((freed_space += size))
        done < <(find "$INSTALL_DIR/logs" -name "*.log" -mtime +30 -print0 2>/dev/null)
        
        if [ $cleaned_files -gt 0 ]; then
            freed_mb=$((freed_space / 1024 / 1024))
            log_success "Cleaned $cleaned_files old log files (${freed_mb}MB freed)"
        else
            log_info "No old log files to clean"
        fi
    fi
    
    # Clean temporary transcription files
    if [ -d "$INSTALL_DIR/logs" ]; then
        log_info "Cleaning temporary transcription files..."
        local temp_files=0
        while IFS= read -r -d '' file; do
            rm "$file"
            ((temp_files++))
        done < <(find "$INSTALL_DIR/logs" -name "temp_*.txt" -mtime +1 -print0 2>/dev/null)
        
        if [ $temp_files -gt 0 ]; then
            log_success "Cleaned $temp_files temporary files"
        else
            log_info "No temporary files to clean"
        fi
    fi
    
    # Clean old backups (keep last 10)
    if [ -d "$BACKUP_DIR" ]; then
        log_info "Cleaning old backup files..."
        local backup_count=$(ls -1 "$BACKUP_DIR"/voice_bridge_backup_*.tar.gz 2>/dev/null | wc -l)
        
        if [ $backup_count -gt 10 ]; then
            local to_remove=$((backup_count - 10))
            ls -1t "$BACKUP_DIR"/voice_bridge_backup_*.tar.gz | tail -n $to_remove | xargs rm -f
            log_success "Cleaned $to_remove old backup files"
        else
            log_info "Backup count within limits ($backup_count/10)"
        fi
    fi
    
    # Clean Python cache files
    log_info "Cleaning Python cache files..."
    local cache_files=0
    if [ -d "$INSTALL_DIR" ]; then
        while IFS= read -r -d '' file; do
            rm -rf "$file"
            ((cache_files++))
        done < <(find "$INSTALL_DIR" -type d -name "__pycache__" -print0 2>/dev/null)
        
        find "$INSTALL_DIR" -name "*.pyc" -delete 2>/dev/null || true
        find "$INSTALL_DIR" -name "*.pyo" -delete 2>/dev/null || true
        
        if [ $cache_files -gt 0 ]; then
            log_success "Cleaned $cache_files Python cache directories"
        fi
    fi
}

# Optimize medical dictionaries
optimize_dictionaries() {
    log_header "Medical Dictionary Optimization"
    
    if [ ! -d "$INSTALL_DIR/config/diccionarios" ]; then
        log_warning "Medical dictionaries directory not found"
        return
    fi
    
    for dict_file in "$INSTALL_DIR/config/diccionarios"/*.txt; do
        if [ ! -f "$dict_file" ]; then
            continue
        fi
        
        dict_name=$(basename "$dict_file")
        log_info "Optimizing $dict_name..."
        
        # Create backup
        cp "$dict_file" "${dict_file}.backup"
        
        # Remove duplicates and sort
        original_count=$(wc -l < "$dict_file")
        
        # Process file: remove duplicates, empty lines, sort
        grep -v '^#' "$dict_file" | grep -v '^$' | sort -u > "${dict_file}.tmp"
        
        # Add header back
        echo "# Medical Dictionary - $(date)" > "${dict_file}.new"
        echo "# Optimized by maintenance script" >> "${dict_file}.new"
        echo "" >> "${dict_file}.new"
        cat "${dict_file}.tmp" >> "${dict_file}.new"
        
        # Replace original
        mv "${dict_file}.new" "$dict_file"
        rm "${dict_file}.tmp"
        
        new_count=$(grep -v '^#' "$dict_file" | grep -v '^$' | wc -l)
        removed=$((original_count - new_count))
        
        if [ $removed -gt 0 ]; then
            log_success "$dict_name: Removed $removed duplicate/empty entries (${new_count} terms remain)"
        else
            log_info "$dict_name: No optimization needed (${new_count} terms)"
        fi
    done
}

# Validate configuration
validate_configuration() {
    log_header "Configuration Validation"
    
    if [ ! -f "$CONFIG_FILE" ]; then
        log_error "Configuration file not found"
        return 1
    fi
    
    local config_errors=0
    
    # Check required settings
    local required_settings=("azure_speech_key" "azure_region" "speech_language")
    for setting in "${required_settings[@]}"; do
        if grep -q "^${setting}.*=" "$CONFIG_FILE"; then
            value=$(grep "^${setting}" "$CONFIG_FILE" | cut -d'=' -f2 | xargs)
            if [ -n "$value" ] && [ "$value" != "your_azure_speech_key_here" ]; then
                log_success "Configuration: $setting is set"
            else
                log_warning "Configuration: $setting is not configured"
                ((config_errors++))
            fi
        else
            log_error "Configuration: $setting is missing"
            ((config_errors++))
        fi
    done
    
    # Validate file permissions
    if [ -r "$CONFIG_FILE" ]; then
        log_success "Configuration file is readable"
    else
        log_error "Configuration file is not readable"
        ((config_errors++))
    fi
    
    # Check file permissions (should be 600 for security)
    local perms=$(stat -c%a "$CONFIG_FILE")
    if [ "$perms" = "600" ]; then
        log_success "Configuration file has secure permissions (600)"
    else
        log_warning "Configuration file permissions: $perms (recommend 600)"
    fi
    
    return $config_errors
}

# Test Azure connectivity
test_azure_connectivity() {
    log_header "Azure Connectivity Test"
    
    # Extract Azure configuration
    local azure_key=""
    local azure_region=""
    
    if [ -f "$CONFIG_FILE" ]; then
        azure_key=$(grep "azure_speech_key" "$CONFIG_FILE" | cut -d'=' -f2 | xargs)
        azure_region=$(grep "azure_region" "$CONFIG_FILE" | cut -d'=' -f2 | xargs)
    fi
    
    # Check environment variables as fallback
    azure_key=${azure_key:-$AZURE_SPEECH_KEY}
    azure_region=${azure_region:-$AZURE_SPEECH_REGION}
    azure_region=${azure_region:-eastus}
    
    if [ -z "$azure_key" ] || [ "$azure_key" = "your_azure_speech_key_here" ]; then
        log_warning "Azure Speech key not configured - skipping connectivity test"
        return 1
    fi
    
    log_info "Testing connectivity to Azure Speech Services..."
    log_info "Region: $azure_region"
    log_info "Key: ${azure_key:0:8}..."
    
    # Test Azure endpoint
    local response
    response=$(curl -s -w "%{http_code}" \
        -X POST \
        -H "Ocp-Apim-Subscription-Key: $azure_key" \
        -H "Content-Length: 0" \
        "https://$azure_region.api.cognitive.microsoft.com/sts/v1.0/issuetoken" \
        -o /dev/null 2>/dev/null || echo "000")
    
    case $response in
        "200")
            log_success "Azure connectivity test successful"
            return 0
            ;;
        "401")
            log_error "Azure authentication failed - invalid key"
            return 1
            ;;
        "403")
            log_error "Azure access forbidden - check subscription status"
            return 1
            ;;
        "000")
            log_error "Network connectivity issue - check internet connection"
            return 1
            ;;
        *)
            log_warning "Unexpected response code: $response"
            return 1
            ;;
    esac
}

# Generate system report
generate_report() {
    log_header "Generating System Report"
    
    local report_file="$INSTALL_DIR/logs/system_report_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$report_file" << EOF
# Voice Bridge Pathology - System Report
# Generated: $(date)
# Maintenance Script Version: 1.0.0

## System Information
- Hostname: $(hostname)
- Operating System: $(uname -a)
- Python Version: $(python3 --version 2>&1)
- User: $(whoami)
- Installation Directory: $INSTALL_DIR

## Disk Usage
EOF
    
    # Add disk usage information
    echo "- Installation Size: $(du -sh "$INSTALL_DIR" 2>/dev/null | cut -f1)" >> "$report_file"
    echo "- Available Space: $(df -h "$INSTALL_DIR" | tail -1 | awk '{print $4}')" >> "$report_file"
    echo "" >> "$report_file"
    
    # Add medical dictionary statistics
    echo "## Medical Dictionary Statistics" >> "$report_file"
    if [ -d "$INSTALL_DIR/config/diccionarios" ]; then
        for dict in "$INSTALL_DIR/config/diccionarios"/*.txt; do
            if [ -f "$dict" ]; then
                dict_name=$(basename "$dict")
                term_count=$(grep -v '^#' "$dict" | grep -v '^$' | wc -l)
                echo "- $dict_name: $term_count terms" >> "$report_file"
            fi
        done
    else
        echo "- No medical dictionaries found" >> "$report_file"
    fi
    echo "" >> "$report_file"
    
    # Add recent log summary
    echo "## Recent Activity" >> "$report_file"
    if [ -d "$INSTALL_DIR/logs" ]; then
        log_count=$(find "$INSTALL_DIR/logs" -name "*.log" -mtime -7 | wc -l)
        echo "- Log files in last 7 days: $log_count" >> "$report_file"
        
        if [ -f "$INSTALL_DIR/logs/voice_bridge_$(date +%Y%m%d).log" ]; then
            error_count=$(grep -c "ERROR" "$INSTALL_DIR/logs/voice_bridge_$(date +%Y%m%d).log" 2>/dev/null || echo 0)
            warning_count=$(grep -c "WARNING" "$INSTALL_DIR/logs/voice_bridge_$(date +%Y%m%d).log" 2>/dev/null || echo 0)
            echo "- Today's errors: $error_count" >> "$report_file"
            echo "- Today's warnings: $warning_count" >> "$report_file"
        fi
    fi
    echo "" >> "$report_file"
    
    # Add maintenance history
    echo "## Maintenance History" >> "$report_file"
    echo "- Last maintenance: $(date)" >> "$report_file"
    echo "- Maintenance log: $LOG_FILE" >> "$report_file"
    
    log_success "System report generated: $report_file"
}

# Update system
update_system() {
    log_header "System Update Check"
    
    # Check if git repository
    if [ -d "$INSTALL_DIR/.git" ]; then
        log_info "Git repository detected - checking for updates..."
        cd "$INSTALL_DIR"
        
        # Fetch latest changes
        if git fetch origin main 2>/dev/null; then
            local commits_behind=$(git rev-list HEAD..origin/main --count 2>/dev/null || echo 0)
            
            if [ "$commits_behind" -gt 0 ]; then
                log_warning "System is $commits_behind commits behind latest version"
                log_info "Run 'git pull origin main' to update (backup first!)"
            else
                log_success "System is up to date"
            fi
        else
            log_warning "Could not check for updates (no network or remote)"
        fi
    else
        log_info "Not a git repository - manual update required"
    fi
    
    # Check Python dependencies
    if [ -f "$INSTALL_DIR/voice-bridge-project/.venv/bin/activate" ]; then
        log_info "Checking Python dependencies..."
        source "$INSTALL_DIR/voice-bridge-project/.venv/bin/activate"
        
        # Check for outdated packages
        if command -v pip &> /dev/null; then
            outdated=$(pip list --outdated --format=freeze 2>/dev/null | wc -l)
            if [ "$outdated" -gt 0 ]; then
                log_warning "$outdated packages can be updated"
                log_info "Run 'pip list --outdated' to see details"
            else
                log_success "All Python packages are up to date"
            fi
        fi
    fi
}

# Main maintenance function
main() {
    init_maintenance
    
    local operation="${1:-all}"
    local exit_code=0
    
    case $operation in
        "health"|"check")
            health_check
            exit_code=$?
            ;;
        "cleanup"|"clean")
            cleanup_files
            ;;
        "optimize"|"opt")
            optimize_dictionaries
            ;;
        "validate"|"config")
            validate_configuration
            exit_code=$?
            ;;
        "azure"|"connectivity")
            test_azure_connectivity
            exit_code=$?
            ;;
        "report")
            generate_report
            ;;
        "update")
            update_system
            ;;
        "all"|"")
            log_header "Running Full Maintenance"
            health_check
            local health_result=$?
            cleanup_files
            optimize_dictionaries
            validate_configuration
            test_azure_connectivity
            generate_report
            update_system
            
            if [ $health_result -ne 0 ]; then
                exit_code=$health_result
            fi
            ;;
        *)
            echo "Usage: $0 [health|cleanup|optimize|validate|azure|report|update|all]"
            echo ""
            echo "Operations:"
            echo "  health    - Check system health"
            echo "  cleanup   - Clean old files and cache"
            echo "  optimize  - Optimize medical dictionaries"
            echo "  validate  - Validate configuration"
            echo "  azure     - Test Azure connectivity"
            echo "  report    - Generate system report"
            echo "  update    - Check for updates"
            echo "  all       - Run all maintenance tasks (default)"
            exit 1
            ;;
    esac
    
    log_info "Maintenance completed at $(date)"
    log_info "Full log available at: $LOG_FILE"
    
    exit $exit_code
}

# Run main function with all arguments
main "$@"
