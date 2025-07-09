#!/bin/bash

# Voice Bridge Pathology - Real-time Monitoring Script
# Continuous monitoring for Voice Bridge Pathology system
# Provides real-time health checks, performance metrics, and alerts

set -e

# Configuration
INSTALL_DIR="$HOME/voice-bridge-claude"
MONITOR_INTERVAL=30  # seconds
LOG_FILE="$INSTALL_DIR/logs/monitor_$(date +%Y%m%d).log"
ALERT_THRESHOLD_CPU=80
ALERT_THRESHOLD_MEMORY=85
ALERT_THRESHOLD_DISK=90
AZURE_TIMEOUT=10

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Monitoring state
MONITORING=true
AZURE_FAILURES=0
SYSTEM_ALERTS=0
LAST_AZURE_CHECK=0

# Signal handlers
cleanup() {
    echo ""
    log_info "Monitoring stopped by user"
    MONITORING=false
    exit 0
}

trap cleanup SIGINT SIGTERM

# Logging functions
log_info() {
    local timestamp=$(date '+%H:%M:%S')
    echo -e "${BLUE}[$timestamp INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    local timestamp=$(date '+%H:%M:%S')
    echo -e "${GREEN}[$timestamp OK]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    local timestamp=$(date '+%H:%M:%S')
    echo -e "${YELLOW}[$timestamp WARN]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    local timestamp=$(date '+%H:%M:%S')
    echo -e "${RED}[$timestamp ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

log_metric() {
    local timestamp=$(date '+%H:%M:%S')
    echo -e "${CYAN}[$timestamp METRIC]${NC} $1" | tee -a "$LOG_FILE"
}

log_alert() {
    local timestamp=$(date '+%H:%M:%S')
    echo -e "${PURPLE}[$timestamp ALERT]${NC} $1" | tee -a "$LOG_FILE"
    ((SYSTEM_ALERTS++))
}

# Initialize monitoring
init_monitor() {
    clear
    echo "=============================================="
    echo "   Voice Bridge Pathology - Real-time Monitor"
    echo "=============================================="
    echo ""
    log_info "Monitoring started at $(date)"
    log_info "Installation directory: $INSTALL_DIR"
    log_info "Monitor interval: ${MONITOR_INTERVAL}s"
    log_info "Log file: $LOG_FILE"
    echo ""
    log_info "Press Ctrl+C to stop monitoring"
    echo ""
    
    # Create log directory
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Verify installation
    if [ ! -d "$INSTALL_DIR" ]; then
        log_error "Voice Bridge installation not found at $INSTALL_DIR"
        exit 1
    fi
}

# Check if Voice Bridge process is running
check_voice_bridge_process() {
    if pgrep -f "voice_bridge_app.py" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Monitor system resources
monitor_system_resources() {
    # CPU usage
    local cpu_usage
    if command -v top &> /dev/null; then
        cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
        cpu_usage=${cpu_usage%.*}  # Remove decimal part
    else
        cpu_usage=0
    fi
    
    # Memory usage
    local memory_info
    if [ -f /proc/meminfo ]; then
        local mem_total=$(grep MemTotal /proc/meminfo | awk '{print $2}')
        local mem_available=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
        local memory_usage=$(( (mem_total - mem_available) * 100 / mem_total ))
    else
        local memory_usage=0
    fi
    
    # Disk usage
    local disk_usage
    if [ -d "$INSTALL_DIR" ]; then
        disk_usage=$(df "$INSTALL_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
    else
        disk_usage=0
    fi
    
    # Log metrics
    log_metric "CPU: ${cpu_usage}% | Memory: ${memory_usage}% | Disk: ${disk_usage}%"
    
    # Check thresholds and alert
    if [ "$cpu_usage" -gt "$ALERT_THRESHOLD_CPU" ]; then
        log_alert "High CPU usage: ${cpu_usage}% (threshold: ${ALERT_THRESHOLD_CPU}%)"
    fi
    
    if [ "$memory_usage" -gt "$ALERT_THRESHOLD_MEMORY" ]; then
        log_alert "High memory usage: ${memory_usage}% (threshold: ${ALERT_THRESHOLD_MEMORY}%)"
    fi
    
    if [ "$disk_usage" -gt "$ALERT_THRESHOLD_DISK" ]; then
        log_alert "High disk usage: ${disk_usage}% (threshold: ${ALERT_THRESHOLD_DISK}%)"
    fi
}

# Monitor Voice Bridge application
monitor_voice_bridge() {
    if check_voice_bridge_process; then
        log_success "Voice Bridge process is running"
        
        # Check process details
        local pid=$(pgrep -f "voice_bridge_app.py")
        local process_info=$(ps -p "$pid" -o pid,ppid,etime,pcpu,pmem --no-headers 2>/dev/null || echo "N/A")
        log_metric "Process: PID=$pid, Info=($process_info)"
        
        # Check if GUI is responsive (if X11 available)
        if [ -n "$DISPLAY" ] && command -v wmctrl &> /dev/null; then
            if wmctrl -l | grep -q "Voice Bridge"; then
                log_success "Voice Bridge GUI is visible"
            else
                log_warning "Voice Bridge GUI not found in window list"
            fi
        fi
        
    else
        log_error "Voice Bridge process is not running"
    fi
}

# Monitor audio system
monitor_audio_system() {
    # Check audio devices
    if [ -e "/dev/snd" ]; then
        local audio_devices=$(ls /dev/snd/ | grep -c "^card" 2>/dev/null || echo 0)
        log_success "Audio system: $audio_devices sound card(s) detected"
    else
        log_error "Audio system: No sound devices found"
    fi
    
    # Check PulseAudio if available
    if command -v pactl &> /dev/null; then
        if pactl info &> /dev/null; then
            local default_sink=$(pactl get-default-sink 2>/dev/null || echo "unknown")
            log_success "PulseAudio: Active (default sink: $default_sink)"
        else
            log_warning "PulseAudio: Not responding"
        fi
    fi
    
    # Check ALSA if available
    if command -v aplay &> /dev/null; then
        local alsa_devices=$(aplay -l 2>/dev/null | grep -c "^card" || echo 0)
        log_metric "ALSA: $alsa_devices audio device(s)"
    fi
}

# Monitor Azure connectivity
monitor_azure_connectivity() {
    local current_time=$(date +%s)
    
    # Only check Azure every 5 minutes to avoid rate limiting
    if [ $((current_time - LAST_AZURE_CHECK)) -lt 300 ]; then
        return
    fi
    
    LAST_AZURE_CHECK=$current_time
    
    # Get Azure configuration
    local azure_key=""
    local azure_region=""
    local config_file="$INSTALL_DIR/config/voice_bridge_config.ini"
    
    if [ -f "$config_file" ]; then
        azure_key=$(grep "azure_speech_key" "$config_file" | cut -d'=' -f2 | xargs 2>/dev/null || echo "")
        azure_region=$(grep "azure_region" "$config_file" | cut -d'=' -f2 | xargs 2>/dev/null || echo "")
    fi
    
    # Check environment variables as fallback
    azure_key=${azure_key:-$AZURE_SPEECH_KEY}
    azure_region=${azure_region:-$AZURE_SPEECH_REGION}
    azure_region=${azure_region:-eastus}
    
    if [ -z "$azure_key" ] || [ "$azure_key" = "your_azure_speech_key_here" ]; then
        log_warning "Azure: Speech key not configured"
        return
    fi
    
    # Test Azure endpoint with timeout
    local response
    response=$(timeout "$AZURE_TIMEOUT" curl -s -w "%{http_code}" \
        -X POST \
        -H "Ocp-Apim-Subscription-Key: $azure_key" \
        -H "Content-Length: 0" \
        "https://$azure_region.api.cognitive.microsoft.com/sts/v1.0/issuetoken" \
        -o /dev/null 2>/dev/null || echo "000")
    
    case $response in
        "200")
            log_success "Azure: Speech Services connectivity OK"
            AZURE_FAILURES=0
            ;;
        "401")
            log_error "Azure: Authentication failed (invalid key)"
            ((AZURE_FAILURES++))
            ;;
        "403")
            log_error "Azure: Access forbidden (check subscription)"
            ((AZURE_FAILURES++))
            ;;
        "000")
            log_warning "Azure: Network timeout or connectivity issue"
            ((AZURE_FAILURES++))
            ;;
        *)
            log_warning "Azure: Unexpected response code $response"
            ((AZURE_FAILURES++))
            ;;
    esac
    
    # Alert on consecutive failures
    if [ $AZURE_FAILURES -ge 3 ]; then
        log_alert "Azure: $AZURE_FAILURES consecutive connectivity failures"
    fi
}

# Monitor configuration files
monitor_configuration() {
    local config_file="$INSTALL_DIR/config/voice_bridge_config.ini"
    
    if [ -f "$config_file" ]; then
        # Check file permissions
        local perms=$(stat -c%a "$config_file")
        if [ "$perms" != "600" ]; then
            log_warning "Config: Insecure file permissions ($perms, should be 600)"
        fi
        
        # Check file modification time
        local mod_time=$(stat -c%Y "$config_file")
        local current_time=$(date +%s)
        local age=$((current_time - mod_time))
        
        if [ $age -lt 300 ]; then  # Modified in last 5 minutes
            log_info "Config: Recently modified (${age}s ago)"
        fi
        
        log_success "Config: File accessible and valid"
    else
        log_error "Config: Configuration file missing"
    fi
    
    # Check medical dictionaries
    local dict_dir="$INSTALL_DIR/config/diccionarios"
    if [ -d "$dict_dir" ]; then
        local dict_count=0
        local total_terms=0
        
        for dict_file in "$dict_dir"/*.txt; do
            if [ -f "$dict_file" ]; then
                local terms=$(grep -v '^#' "$dict_file" | grep -v '^$' | wc -l)
                total_terms=$((total_terms + terms))
                ((dict_count++))
            fi
        done
        
        if [ $dict_count -gt 0 ]; then
            log_success "Medical Dicts: $dict_count files, $total_terms total terms"
        else
            log_warning "Medical Dicts: No dictionary files found"
        fi
    else
        log_error "Medical Dicts: Directory missing"
    fi
}

# Monitor log files
monitor_logs() {
    local log_dir="$INSTALL_DIR/logs"
    
    if [ -d "$log_dir" ]; then
        # Check current log file
        local today_log="$log_dir/voice_bridge_$(date +%Y%m%d).log"
        if [ -f "$today_log" ]; then
            # Count recent errors and warnings
            local recent_errors=$(tail -100 "$today_log" | grep -c "ERROR" || echo 0)
            local recent_warnings=$(tail -100 "$today_log" | grep -c "WARNING" || echo 0)
            
            if [ $recent_errors -gt 0 ]; then
                log_warning "Logs: $recent_errors recent errors in application log"
            fi
            
            if [ $recent_warnings -gt 5 ]; then
                log_warning "Logs: $recent_warnings recent warnings in application log"
            fi
            
            # Check log file size
            local log_size=$(stat -c%s "$today_log" 2>/dev/null || echo 0)
            local log_size_mb=$((log_size / 1024 / 1024))
            
            if [ $log_size_mb -gt 100 ]; then
                log_warning "Logs: Today's log file is large (${log_size_mb}MB)"
            fi
            
            log_metric "Logs: Recent errors: $recent_errors, warnings: $recent_warnings"
        else
            log_info "Logs: No application log for today"
        fi
        
        # Check disk space for logs
        local log_disk_usage=$(du -sm "$log_dir" 2>/dev/null | cut -f1 || echo 0)
        if [ $log_disk_usage -gt 1000 ]; then  # More than 1GB
            log_warning "Logs: Directory size is large (${log_disk_usage}MB)"
        fi
        
    else
        log_warning "Logs: Log directory not found"
    fi
}

# Monitor network connectivity
monitor_network() {
    # Check general internet connectivity
    if ping -c 1 -W 5 8.8.8.8 &> /dev/null; then
        log_success "Network: Internet connectivity OK"
    else
        log_error "Network: No internet connectivity"
    fi
    
    # Check DNS resolution
    if nslookup azure.microsoft.com &> /dev/null; then
        log_success "Network: DNS resolution OK"
    else
        log_warning "Network: DNS resolution issues"
    fi
}

# Generate monitoring summary
generate_summary() {
    echo ""
    echo "=============================================="
    echo "   Monitoring Summary"
    echo "=============================================="
    echo "Monitor duration: $(($(date +%s) - $(date -d "$(head -1 "$LOG_FILE" | cut -d']' -f1 | tr -d '[')" +%s) 2>/dev/null || echo 0))s"
    echo "System alerts: $SYSTEM_ALERTS"
    echo "Azure failures: $AZURE_FAILURES"
    echo "Log file: $LOG_FILE"
    echo ""
}

# Display real-time dashboard
display_dashboard() {
    # Clear screen and show header
    printf "\033[H\033[2J"  # Clear screen
    echo "=============================================="
    echo "   Voice Bridge Pathology - Live Monitor"
    echo "=============================================="
    echo "Time: $(date)"
    echo "Alerts: $SYSTEM_ALERTS | Azure Failures: $AZURE_FAILURES"
    echo "Press Ctrl+C to stop"
    echo "=============================================="
    echo ""
}

# Main monitoring loop
main_monitor_loop() {
    local cycle=0
    
    while $MONITORING; do
        ((cycle++))
        
        # Display dashboard every cycle
        display_dashboard
        
        # Core monitoring checks
        log_info "=== Monitoring Cycle $cycle ==="
        
        monitor_voice_bridge
        monitor_system_resources
        monitor_audio_system
        monitor_configuration
        monitor_logs
        
        # Extended checks (less frequent)
        if [ $((cycle % 5)) -eq 0 ]; then  # Every 5th cycle
            monitor_azure_connectivity
            monitor_network
        fi
        
        echo ""
        log_info "Cycle $cycle completed - waiting ${MONITOR_INTERVAL}s"
        echo ""
        
        # Wait for next cycle
        sleep $MONITOR_INTERVAL
    done
}

# Help function
show_help() {
    echo "Voice Bridge Pathology - Real-time Monitor"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -i, --interval SECONDS   Monitor interval (default: 30)"
    echo "  -d, --directory PATH      Installation directory"
    echo "  -q, --quiet               Reduce output verbosity"
    echo "  -h, --help                Show this help"
    echo ""
    echo "Examples:"
    echo "  $0                        Start monitoring with defaults"
    echo "  $0 -i 60                  Monitor every 60 seconds"
    echo "  $0 -d /custom/path        Use custom installation path"
    echo ""
    echo "Monitor checks:"
    echo "  - Voice Bridge process status"
    echo "  - System resources (CPU, Memory, Disk)"
    echo "  - Audio system functionality"
    echo "  - Azure Speech Services connectivity"
    echo "  - Configuration file integrity"
    echo "  - Log file monitoring"
    echo "  - Network connectivity"
    echo ""
    echo "Alerts are generated for:"
    echo "  - High resource usage"
    echo "  - Process failures"
    echo "  - Azure connectivity issues"
    echo "  - Configuration problems"
    echo "  - Security concerns"
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -i|--interval)
                MONITOR_INTERVAL="$2"
                shift 2
                ;;
            -d|--directory)
                INSTALL_DIR="$2"
                shift 2
                ;;
            -q|--quiet)
                # Could implement quiet mode
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Validate monitor interval
    if ! [[ "$MONITOR_INTERVAL" =~ ^[0-9]+$ ]] || [ "$MONITOR_INTERVAL" -lt 10 ]; then
        echo "Error: Monitor interval must be a number >= 10 seconds"
        exit 1
    fi
}

# Main function
main() {
    parse_arguments "$@"
    init_monitor
    
    # Validate installation
    if [ ! -d "$INSTALL_DIR" ]; then
        log_error "Installation directory not found: $INSTALL_DIR"
        exit 1
    fi
    
    # Start monitoring
    main_monitor_loop
    
    # Show summary when stopped
    generate_summary
}

# Run main function with all arguments
main "$@"
