#!/bin/bash

# Voice Bridge Pathology - Safe Uninstallation Script
# Safely removes Voice Bridge Pathology while preserving medical data
# Compliant with medical data retention and privacy requirements

set -e

# Configuration
INSTALL_DIR="$HOME/voice-bridge-claude"
BACKUP_DIR="$INSTALL_DIR/uninstall-backups"
UNINSTALL_LOG="$BACKUP_DIR/uninstall_$(date +%Y%m%d_%H%M%S).log"
PRESERVE_MEDICAL_DATA=true
PRESERVE_AUDIT_LOGS=true
PRESERVE_CONFIG=true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Uninstallation state
ITEMS_TO_REMOVE=0
ITEMS_REMOVED=0
ITEMS_PRESERVED=0
MEDICAL_DATA_FOUND=false
FORCE_REMOVAL=false

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$UNINSTALL_LOG"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$UNINSTALL_LOG"
    ((ITEMS_REMOVED++))
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$UNINSTALL_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$UNINSTALL_LOG"
}

log_preserved() {
    echo -e "${PURPLE}[PRESERVED]${NC} $1" | tee -a "$UNINSTALL_LOG"
    ((ITEMS_PRESERVED++))
}

# Initialize uninstallation
init_uninstall() {
    clear
    echo "=============================================="
    echo "   Voice Bridge Pathology - Safe Uninstallation"
    echo "=============================================="
    echo ""
    echo "⚠️  MEDICAL SOFTWARE UNINSTALLATION WARNING ⚠️"
    echo ""
    echo "This will remove Voice Bridge Pathology from your system."
    echo "Medical data and audit logs can be preserved for compliance."
    echo ""
    
    # Create backup directory and log
    mkdir -p "$BACKUP_DIR"
    
    log_info "Uninstallation started at $(date)"
    log_info "Installation directory: $INSTALL_DIR"
    log_info "Uninstall log: $UNINSTALL_LOG"
    
    # Check if installation exists
    if [ ! -d "$INSTALL_DIR" ]; then
        log_error "Voice Bridge installation not found at $INSTALL_DIR"
        echo "Nothing to uninstall."
        exit 0
    fi
}

# Show uninstallation options
show_uninstall_options() {
    echo "Uninstallation Options:"
    echo "======================"
    echo ""
    echo "1. Safe Uninstall (Recommended for Medical Environments)"
    echo "   - Removes application files"
    echo "   - Preserves medical data and configurations"
    echo "   - Maintains audit logs for compliance"
    echo "   - Creates comprehensive backup"
    echo ""
    echo "2. Complete Removal"
    echo "   - Removes ALL files including medical data"
    echo "   - ⚠️  WARNING: May violate data retention requirements"
    echo "   - Creates backup before deletion"
    echo ""
    echo "3. Preserve Everything + Disable"
    echo "   - Keeps all files but disables auto-start"
    echo "   - Renames installation for later removal"
    echo "   - Maintains full audit trail"
    echo ""
    echo "4. Cancel Uninstallation"
    echo ""
}

# Get user choice for uninstallation type
get_uninstall_choice() {
    while true; do
        read -p "Select uninstallation type (1-4): " choice
        case $choice in
            1)
                PRESERVE_MEDICAL_DATA=true
                PRESERVE_AUDIT_LOGS=true
                PRESERVE_CONFIG=true
                log_info "Selected: Safe Uninstall (Medical Environment)"
                break
                ;;
            2)
                echo ""
                echo "⚠️  COMPLETE REMOVAL WARNING ⚠️"
                echo "This will delete ALL medical data and audit logs."
                echo "This may violate medical data retention requirements."
                echo ""
                read -p "Are you sure you want to proceed? (type 'DELETE ALL'): " confirm
                if [ "$confirm" = "DELETE ALL" ]; then
                    PRESERVE_MEDICAL_DATA=false
                    PRESERVE_AUDIT_LOGS=false
                    PRESERVE_CONFIG=false
                    FORCE_REMOVAL=true
                    log_warning "Selected: Complete Removal (ALL DATA WILL BE DELETED)"
                    break
                else
                    echo "Complete removal cancelled."
                    continue
                fi
                ;;
            3)
                PRESERVE_MEDICAL_DATA=true
                PRESERVE_AUDIT_LOGS=true
                PRESERVE_CONFIG=true
                log_info "Selected: Preserve Everything + Disable"
                disable_and_preserve
                exit 0
                ;;
            4)
                echo "Uninstallation cancelled."
                exit 0
                ;;
            *)
                echo "Invalid choice. Please select 1-4."
                ;;
        esac
    done
}

# Disable and preserve installation
disable_and_preserve() {
    log_info "Disabling Voice Bridge while preserving all data..."
    
    # Stop any running processes
    stop_voice_bridge_processes
    
    # Rename installation directory
    local preserved_name="voice-bridge-claude-disabled-$(date +%Y%m%d_%H%M%S)"
    mv "$INSTALL_DIR" "$HOME/$preserved_name"
    
    # Create informational file
    cat > "$HOME/${preserved_name}/DISABLED_INSTALLATION.txt" << EOF
# Voice Bridge Pathology - Disabled Installation
# Disabled on: $(date)
# Original location: $INSTALL_DIR
# Current location: $HOME/$preserved_name

This installation has been disabled but all data preserved.
Medical data, audit logs, and configurations remain intact.

To re-enable:
1. Move this directory back to: $INSTALL_DIR
2. Run the installation verification script
3. Update any configuration paths as needed

To permanently remove:
1. Review medical data retention requirements
2. Backup any required audit logs
3. Run this uninstall script again with complete removal option
EOF

    log_success "Installation disabled and preserved at: $HOME/$preserved_name"
    log_info "All medical data and audit logs preserved for compliance"
}

# Stop Voice Bridge processes
stop_voice_bridge_processes() {
    log_info "Stopping Voice Bridge processes..."
    
    # Stop main application process
    if pgrep -f "voice_bridge_app.py" > /dev/null; then
        pkill -f "voice_bridge_app.py"
        sleep 2
        
        # Force kill if still running
        if pgrep -f "voice_bridge_app.py" > /dev/null; then
            pkill -9 -f "voice_bridge_app.py"
            log_warning "Force terminated Voice Bridge process"
        else
            log_success "Voice Bridge process stopped gracefully"
        fi
    else
        log_info "No Voice Bridge processes running"
    fi
    
    # Stop any monitoring processes
    if pgrep -f "monitor.sh" > /dev/null; then
        pkill -f "monitor.sh"
        log_success "Monitoring processes stopped"
    fi
    
    # Stop any Docker containers
    if command -v docker &> /dev/null; then
        if docker ps --format "table {{.Names}}" | grep -q voice-bridge; then
            docker stop voice-bridge-pathology 2>/dev/null || true
            log_success "Docker containers stopped"
        fi
    fi
}

# Scan for medical data
scan_medical_data() {
    log_info "Scanning for medical data..."
    
    local medical_files=0
    local transcription_files=0
    local audit_files=0
    
    # Check for transcription files
    if [ -d "$INSTALL_DIR/logs" ]; then
        transcription_files=$(find "$INSTALL_DIR/logs" -name "transcripciones_*.txt" -o -name "*transcription*.txt" | wc -l)
        if [ $transcription_files -gt 0 ]; then
            MEDICAL_DATA_FOUND=true
            log_warning "Found $transcription_files transcription files containing potential medical data"
        fi
    fi
    
    # Check for audit logs
    if [ -d "$INSTALL_DIR/audit-logs" ]; then
        audit_files=$(find "$INSTALL_DIR/audit-logs" -name "*.log" | wc -l)
        if [ $audit_files -gt 0 ]; then
            MEDICAL_DATA_FOUND=true
            log_warning "Found $audit_files audit log files required for compliance"
        fi
    fi
    
    # Check for medical dictionaries with custom terms
    if [ -d "$INSTALL_DIR/config/diccionarios" ]; then
        for dict_file in "$INSTALL_DIR/config/diccionarios"/*.txt; do
            if [ -f "$dict_file" ]; then
                ((medical_files++))
                local custom_terms=$(grep -v "^#" "$dict_file" | grep -v "^$" | wc -l)
                if [ $custom_terms -gt 10 ]; then  # Threshold for custom content
                    MEDICAL_DATA_FOUND=true
                    log_warning "Found medical dictionary with $custom_terms terms: $(basename "$dict_file")"
                fi
            fi
        done
    fi
    
    if [ "$MEDICAL_DATA_FOUND" = true ]; then
        echo ""
        echo "⚠️  MEDICAL DATA DETECTED ⚠️"
        echo "The system contains medical data that may be subject to retention requirements:"
        echo "- Transcription files: $transcription_files"
        echo "- Audit log files: $audit_files"
        echo "- Medical dictionary files: $medical_files"
        echo ""
        echo "Consider data retention policies before proceeding with removal."
        echo ""
    fi
}

# Create comprehensive backup
create_comprehensive_backup() {
    log_info "Creating comprehensive backup before uninstallation..."
    
    local backup_name="voice_bridge_complete_backup_$(date +%Y%m%d_%H%M%S)"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    mkdir -p "$backup_path"
    
    # Backup all configuration
    if [ -d "$INSTALL_DIR/config" ]; then
        cp -r "$INSTALL_DIR/config" "$backup_path/"
        log_success "Configuration files backed up"
    fi
    
    # Backup all logs and transcriptions
    if [ -d "$INSTALL_DIR/logs" ]; then
        cp -r "$INSTALL_DIR/logs" "$backup_path/"
        local log_count=$(find "$backup_path/logs" -type f | wc -l)
        log_success "Log files backed up ($log_count files)"
    fi
    
    # Backup audit logs
    if [ -d "$INSTALL_DIR/audit-logs" ]; then
        cp -r "$INSTALL_DIR/audit-logs" "$backup_path/"
        local audit_count=$(find "$backup_path/audit-logs" -type f | wc -l)
        log_success "Audit logs backed up ($audit_count files)"
    fi
    
    # Backup custom scripts
    if [ -d "$INSTALL_DIR/scripts" ]; then
        cp -r "$INSTALL_DIR/scripts" "$backup_path/"
        log_success "Custom scripts backed up"
    fi
    
    # Create backup manifest
    cat > "$backup_path/BACKUP_MANIFEST.txt" << EOF
# Voice Bridge Pathology - Complete Backup Manifest
# Created during uninstallation: $(date)
# Original installation: $INSTALL_DIR
# Backup type: Complete system backup

## System Information
- User: $(whoami)
- Hostname: $(hostname)
- OS: $(uname -a)

## Backup Contents
EOF
    
    find "$backup_path" -type f | while read -r file; do
        relative_path=${file#$backup_path/}
        file_size=$(stat -c%s "$file" 2>/dev/null || echo "0")
        echo "- $relative_path (${file_size} bytes)" >> "$backup_path/BACKUP_MANIFEST.txt"
    done
    
    # Create compressed archive
    cd "$BACKUP_DIR"
    tar -czf "${backup_name}.tar.gz" "$backup_name"
    rm -rf "$backup_name"
    
    log_success "Complete backup created: ${backup_name}.tar.gz"
    
    # Verify backup integrity
    if tar -tzf "${backup_name}.tar.gz" > /dev/null 2>&1; then
        log_success "Backup integrity verified"
    else
        log_error "Backup integrity check failed"
        exit 1
    fi
}

# Remove application files
remove_application_files() {
    log_info "Removing application files..."
    
    # Remove Python application
    if [ -f "$INSTALL_DIR/voice_bridge_app.py" ]; then
        rm "$INSTALL_DIR/voice_bridge_app.py"
        log_success "Main application file removed"
        ((ITEMS_TO_REMOVE++))
    fi
    
    # Remove virtual environment
    if [ -d "$INSTALL_DIR/voice-bridge-project/.venv" ]; then
        rm -rf "$INSTALL_DIR/voice-bridge-project/.venv"
        log_success "Virtual environment removed"
        ((ITEMS_TO_REMOVE++))
    fi
    
    # Remove Python cache files
    find "$INSTALL_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find "$INSTALL_DIR" -name "*.pyc" -delete 2>/dev/null || true
    find "$INSTALL_DIR" -name "*.pyo" -delete 2>/dev/null || true
    log_success "Python cache files removed"
    
    # Remove examples (if preserving config, keep examples)
    if [ "$PRESERVE_CONFIG" = false ] && [ -d "$INSTALL_DIR/examples" ]; then
        rm -rf "$INSTALL_DIR/examples"
        log_success "Example files removed"
        ((ITEMS_TO_REMOVE++))
    elif [ "$PRESERVE_CONFIG" = true ] && [ -d "$INSTALL_DIR/examples" ]; then
        log_preserved "Example files preserved"
    fi
    
    # Remove documentation
    local docs_files=("README.md" "LICENSE.md" "CHANGELOG.md" "API.md")
    for doc_file in "${docs_files[@]}"; do
        if [ -f "$INSTALL_DIR/$doc_file" ]; then
            rm "$INSTALL_DIR/$doc_file"
            log_success "Documentation removed: $doc_file"
            ((ITEMS_TO_REMOVE++))
        fi
    done
    
    # Remove Docker files
    local docker_files=("Dockerfile" "docker-compose.yml" ".dockerignore")
    for docker_file in "${docker_files[@]}"; do
        if [ -f "$INSTALL_DIR/$docker_file" ]; then
            rm "$INSTALL_DIR/$docker_file"
            log_success "Docker file removed: $docker_file"
            ((ITEMS_TO_REMOVE++))
        fi
    done
    
    # Remove development files
    if [ -d "$INSTALL_DIR/.vscode" ]; then
        rm -rf "$INSTALL_DIR/.vscode"
        log_success "VS Code configuration removed"
        ((ITEMS_TO_REMOVE++))
    fi
    
    if [ -f "$INSTALL_DIR/.gitignore" ]; then
        rm "$INSTALL_DIR/.gitignore"
        log_success "Git ignore file removed"
        ((ITEMS_TO_REMOVE++))
    fi
}

# Handle medical data according to preservation settings
handle_medical_data() {
    log_info "Processing medical data according to preservation settings..."
    
    # Handle transcription files
    if [ -d "$INSTALL_DIR/logs" ]; then
        if [ "$PRESERVE_MEDICAL_DATA" = true ]; then
            log_preserved "Medical transcription files preserved in logs/"
        else
            # Count files before removal for audit trail
            local transcription_count=$(find "$INSTALL_DIR/logs" -name "*.txt" -o -name "*.log" | wc -l)
            rm -rf "$INSTALL_DIR/logs"
            log_warning "Removed $transcription_count log/transcription files"
            ((ITEMS_TO_REMOVE++))
        fi
    fi
    
    # Handle audit logs
    if [ -d "$INSTALL_DIR/audit-logs" ]; then
        if [ "$PRESERVE_AUDIT_LOGS" = true ]; then
            log_preserved "Audit logs preserved for compliance"
        else
            local audit_count=$(find "$INSTALL_DIR/audit-logs" -name "*.log" | wc -l)
            rm -rf "$INSTALL_DIR/audit-logs"
            log_warning "Removed $audit_count audit log files"
            ((ITEMS_TO_REMOVE++))
        fi
    fi
    
    # Handle configuration and medical dictionaries
    if [ -d "$INSTALL_DIR/config" ]; then
        if [ "$PRESERVE_CONFIG" = true ]; then
            log_preserved "Configuration and medical dictionaries preserved"
            
            # Add preservation notice to config
            cat > "$INSTALL_DIR/config/PRESERVATION_NOTICE.txt" << EOF
# Voice Bridge Pathology - Preserved Configuration
# Preserved during uninstallation: $(date)

This configuration and medical dictionaries have been preserved.
Medical data retention requirements may apply.

To permanently remove:
1. Review your organization's data retention policies
2. Ensure compliance with medical regulations
3. Create additional backups if required
4. Manually delete this directory

Preserved contents:
- Medical dictionaries with custom terminology
- Application configuration settings
- User customizations and preferences
EOF
        else
            local dict_count=0
            if [ -d "$INSTALL_DIR/config/diccionarios" ]; then
                dict_count=$(find "$INSTALL_DIR/config/diccionarios" -name "*.txt" | wc -l)
            fi
            rm -rf "$INSTALL_DIR/config"
            log_warning "Removed configuration and $dict_count medical dictionary files"
            ((ITEMS_TO_REMOVE++))
        fi
    fi
}

# Remove system integration
remove_system_integration() {
    log_info "Removing system integration..."
    
    # Remove desktop entry
    local desktop_file="$HOME/.local/share/applications/voice-bridge-pathology.desktop"
    if [ -f "$desktop_file" ]; then
        rm "$desktop_file"
        log_success "Desktop entry removed"
        ((ITEMS_TO_REMOVE++))
    fi
    
    # Remove from PATH (if added)
    local bashrc_modified=false
    if [ -f "$HOME/.bashrc" ]; then
        if grep -q "voice-bridge-claude" "$HOME/.bashrc"; then
            # Create backup of bashrc
            cp "$HOME/.bashrc" "$HOME/.bashrc.voice-bridge-backup"
            
            # Remove Voice Bridge entries
            grep -v "voice-bridge-claude" "$HOME/.bashrc" > "$HOME/.bashrc.tmp"
            mv "$HOME/.bashrc.tmp" "$HOME/.bashrc"
            
            bashrc_modified=true
            log_success "Removed Voice Bridge entries from .bashrc"
            ((ITEMS_TO_REMOVE++))
        fi
    fi
    
    # Remove autostart entries
    local autostart_file="$HOME/.config/autostart/voice-bridge-pathology.desktop"
    if [ -f "$autostart_file" ]; then
        rm "$autostart_file"
        log_success "Autostart entry removed"
        ((ITEMS_TO_REMOVE++))
    fi
    
    if [ "$bashrc_modified" = true ]; then
        echo ""
        log_warning "Your .bashrc file has been modified."
        log_info "A backup was created at: $HOME/.bashrc.voice-bridge-backup"
        log_info "You may need to restart your terminal or run: source ~/.bashrc"
    fi
}

# Clean up remaining files
cleanup_remaining_files() {
    log_info "Cleaning up remaining files..."
    
    # Remove temporary files
    find "$INSTALL_DIR" -name "*.tmp" -delete 2>/dev/null || true
    find "$INSTALL_DIR" -name "*.backup" -delete 2>/dev/null || true
    log_success "Temporary files cleaned"
    
    # Remove empty directories (except preserved ones)
    if [ "$PRESERVE_MEDICAL_DATA" = false ] && [ "$PRESERVE_CONFIG" = false ]; then
        # Remove the entire installation directory
        rmdir "$INSTALL_DIR" 2>/dev/null || {
            log_warning "Installation directory not empty, some files may remain"
            ls -la "$INSTALL_DIR"
        }
        
        if [ ! -d "$INSTALL_DIR" ]; then
            log_success "Installation directory completely removed"
        fi
    else
        # Remove only empty subdirectories
        find "$INSTALL_DIR" -type d -empty -delete 2>/dev/null || true
        log_info "Empty directories removed, preserved data remains"
    fi
}

# Generate uninstallation report
generate_uninstall_report() {
    log_info "Generating uninstallation report..."
    
    local report_file="$BACKUP_DIR/uninstall_report_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$report_file" << EOF
# Voice Bridge Pathology - Uninstallation Report
# Generated: $(date)

## Uninstallation Summary
- Items scheduled for removal: $ITEMS_TO_REMOVE
- Items successfully removed: $ITEMS_REMOVED
- Items preserved: $ITEMS_PRESERVED
- Medical data found: $MEDICAL_DATA_FOUND
- Force removal mode: $FORCE_REMOVAL

## Preservation Settings
- Preserve medical data: $PRESERVE_MEDICAL_DATA
- Preserve audit logs: $PRESERVE_AUDIT_LOGS  
- Preserve configuration: $PRESERVE_CONFIG

## System Information
- User: $(whoami)
- Hostname: $(hostname)
- Uninstallation date: $(date)
- Original installation: $INSTALL_DIR

## Post-Uninstall Status
EOF

    # Check what remains
    if [ -d "$INSTALL_DIR" ]; then
        echo "- Installation directory: EXISTS (preserved data)" >> "$report_file"
        echo "- Remaining files:" >> "$report_file"
        find "$INSTALL_DIR" -type f | while read -r file; do
            echo "  - $(basename "$file")" >> "$report_file"
        done
    else
        echo "- Installation directory: REMOVED COMPLETELY" >> "$report_file"
    fi
    
    # Add medical compliance notes
    cat >> "$report_file" << EOF

## Medical Compliance Notes
$(date): Voice Bridge Pathology uninstalled
- Medical data handling: $([ "$PRESERVE_MEDICAL_DATA" = true ] && echo "Preserved per retention policy" || echo "Removed per user request")
- Audit trail: $([ "$PRESERVE_AUDIT_LOGS" = true ] && echo "Maintained for compliance" || echo "Removed per user request")
- Backup created: Available in $BACKUP_DIR

## Next Steps
$(if [ "$PRESERVE_MEDICAL_DATA" = true ] || [ "$PRESERVE_AUDIT_LOGS" = true ]; then
    echo "1. Review preserved data periodically per retention policy"
    echo "2. Secure backup location according to medical data protection requirements"
    echo "3. Document uninstallation in your medical software inventory"
else
    echo "1. Verify backup contains all required data"
    echo "2. Document complete removal in medical software inventory"
    echo "3. Update security and compliance documentation"
fi)

## Recovery Information
- Full backup available: Check $BACKUP_DIR for .tar.gz files
- Configuration backup: Available for system restoration
- Medical dictionaries: $([ "$PRESERVE_CONFIG" = true ] && echo "Preserved in place" || echo "Available in backup only")
EOF

    log_success "Uninstallation report generated: $report_file"
}

# Show uninstallation summary
show_summary() {
    echo ""
    echo "=============================================="
    echo "   Uninstallation Summary"
    echo "=============================================="
    echo ""
    echo "✅ Items removed: $ITEMS_REMOVED"
    echo "📋 Items preserved: $ITEMS_PRESERVED"
    echo "🗄️  Backup location: $BACKUP_DIR"
    echo "📄 Uninstall log: $UNINSTALL_LOG"
    echo ""
    
    if [ "$PRESERVE_MEDICAL_DATA" = true ] || [ "$PRESERVE_AUDIT_LOGS" = true ] || [ "$PRESERVE_CONFIG" = true ]; then
        echo "🏥 MEDICAL DATA PRESERVED"
        echo "========================"
        echo "Some data has been preserved for medical compliance:"
        
        if [ "$PRESERVE_MEDICAL_DATA" = true ]; then
            echo "• Medical transcriptions and patient data"
        fi
        if [ "$PRESERVE_AUDIT_LOGS" = true ]; then
            echo "• Audit logs for compliance reporting"
        fi
        if [ "$PRESERVE_CONFIG" = true ]; then
            echo "• Configuration and medical dictionaries"
        fi
        
        echo ""
        echo "📍 Preserved data location: $INSTALL_DIR"
        echo "⚠️  Review your data retention policy for permanent removal timeline"
    else
        echo "🗑️  COMPLETE REMOVAL"
        echo "=================="
        echo "All Voice Bridge files have been removed."
        echo "Medical data and audit logs have been deleted."
        echo "Complete backup available in: $BACKUP_DIR"
    fi
    
    echo ""
    echo "🔒 SECURITY REMINDER"
    echo "==================="
    echo "• Backup files may contain sensitive medical data"
    echo "• Secure backup location according to your policies"
    echo "• Consider encrypting backup files"
    echo "• Update your medical software inventory"
    echo ""
}

# Main uninstallation function
main() {
    init_uninstall
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force)
                FORCE_REMOVAL=true
                PRESERVE_MEDICAL_DATA=false
                PRESERVE_AUDIT_LOGS=false  
                PRESERVE_CONFIG=false
                shift
                ;;
            --preserve-all)
                disable_and_preserve
                exit 0
                ;;
            --help)
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
    
    scan_medical_data
    
    if [ "$FORCE_REMOVAL" = false ]; then
        show_uninstall_options
        get_uninstall_choice
    else
        log_warning "Force removal mode - all data will be deleted"
    fi
    
    # Confirm final action
    echo ""
    echo "⚠️  FINAL CONFIRMATION ⚠️"
    echo "About to uninstall Voice Bridge Pathology with these settings:"
    echo "• Preserve medical data: $PRESERVE_MEDICAL_DATA"
    echo "• Preserve audit logs: $PRESERVE_AUDIT_LOGS"
    echo "• Preserve configuration: $PRESERVE_CONFIG"
    echo ""
    read -p "Proceed with uninstallation? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Uninstallation cancelled."
        exit 0
    fi
    
    # Execute uninstallation steps
    stop_voice_bridge_processes
    create_comprehensive_backup
    remove_application_files
    handle_medical_data
    remove_system_integration
    cleanup_remaining_files
    generate_uninstall_report
    
    show_summary
    
    echo "=============================================="
    echo "   Voice Bridge Pathology Successfully Uninstalled"
    echo "=============================================="
}

# Show help
show_help() {
    echo "Voice Bridge Pathology - Safe Uninstallation Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --force           Force complete removal (all data deleted)"
    echo "  --preserve-all    Disable application but preserve all data"  
    echo "  --help            Show this help"
    echo ""
    echo "Interactive mode (default):"
    echo "  - Guided uninstallation with options"
    echo "  - Medical data preservation choices"
    echo "  - Compliance-aware removal"
    echo ""
    echo "Medical compliance features:"
    echo "  - Comprehensive backup before removal"
    echo "  - Selective preservation of medical data"
    echo "  - Audit trail maintenance"
    echo "  - HIPAA-aware data handling"
    echo ""
}

# Run main function with all arguments
main "$@"
