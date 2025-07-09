#!/bin/bash

# Voice Bridge Pathology - Backup Configuration Script
# Creates backups of all configuration files and medical dictionaries

set -e

# Configuration
INSTALL_DIR="$HOME/voice-bridge-claude"
BACKUP_DIR="$INSTALL_DIR/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="voice_bridge_backup_$TIMESTAMP"

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
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create backup directory
create_backup_directory() {
    print_status "Creating backup directory..."
    mkdir -p "$BACKUP_DIR/$BACKUP_NAME"
    print_success "Backup directory created: $BACKUP_DIR/$BACKUP_NAME"
}

# Backup configuration files
backup_configuration() {
    print_status "Backing up configuration files..."
    
    if [ -d "$INSTALL_DIR/config" ]; then
        cp -r "$INSTALL_DIR/config" "$BACKUP_DIR/$BACKUP_NAME/"
        print_success "Configuration files backed up"
    else
        print_warning "Configuration directory not found"
    fi
}

# Backup medical dictionaries
backup_dictionaries() {
    print_status "Backing up medical dictionaries..."
    
    if [ -d "$INSTALL_DIR/config/diccionarios" ]; then
        # Count terms in each dictionary
        for dict_file in "$INSTALL_DIR/config/diccionarios"/*.txt; do
            if [ -f "$dict_file" ]; then
                term_count=$(wc -l < "$dict_file")
                dict_name=$(basename "$dict_file")
                print_status "  $dict_name: $term_count terms"
            fi
        done
        print_success "Medical dictionaries backed up"
    else
        print_warning "Medical dictionaries not found"
    fi
}

# Backup logs (recent only)
backup_recent_logs() {
    print_status "Backing up recent logs..."
    
    if [ -d "$INSTALL_DIR/logs" ]; then
        mkdir -p "$BACKUP_DIR/$BACKUP_NAME/logs"
        
        # Backup logs from last 7 days
        find "$INSTALL_DIR/logs" -name "*.log" -mtime -7 -exec cp {} "$BACKUP_DIR/$BACKUP_NAME/logs/" \;
        find "$INSTALL_DIR/logs" -name "transcripciones_*.txt" -mtime -7 -exec cp {} "$BACKUP_DIR/$BACKUP_NAME/logs/" \;
        
        log_count=$(ls -1 "$BACKUP_DIR/$BACKUP_NAME/logs/" 2>/dev/null | wc -l)
        print_success "Recent logs backed up ($log_count files)"
    else
        print_warning "Logs directory not found"
    fi
}

# Backup environment configuration
backup_environment() {
    print_status "Backing up environment configuration..."
    
    # Create environment info file
    cat > "$BACKUP_DIR/$BACKUP_NAME/environment_info.txt" << EOF
# Voice Bridge Pathology - Environment Backup
# Created: $(date)
# System: $(uname -a)
# Python: $(python3 --version 2>/dev/null || echo "Not found")
# Azure Region: ${AZURE_SPEECH_REGION:-"Not set"}
# Speech Language: ${SPEECH_LANGUAGE:-"Not set"}

# Environment Variables
AZURE_SPEECH_KEY=${AZURE_SPEECH_KEY:+Set (hidden)}
AZURE_SPEECH_REGION=$AZURE_SPEECH_REGION
SPEECH_LANGUAGE=$SPEECH_LANGUAGE
TTS_VOICE=$TTS_VOICE

# Installed Packages
EOF
    
    # Add Python package info if virtual environment exists
    if [ -f "$INSTALL_DIR/voice-bridge-project/.venv/bin/activate" ]; then
        source "$INSTALL_DIR/voice-bridge-project/.venv/bin/activate"
        pip list >> "$BACKUP_DIR/$BACKUP_NAME/environment_info.txt" 2>/dev/null || echo "Could not list packages" >> "$BACKUP_DIR/$BACKUP_NAME/environment_info.txt"
    fi
    
    print_success "Environment configuration backed up"
}

# Create backup archive
create_archive() {
    print_status "Creating backup archive..."
    
    cd "$BACKUP_DIR"
    tar -czf "$BACKUP_NAME.tar.gz" "$BACKUP_NAME"
    
    if [ -f "$BACKUP_NAME.tar.gz" ]; then
        # Get archive size
        archive_size=$(du -h "$BACKUP_NAME.tar.gz" | cut -f1)
        print_success "Backup archive created: $BACKUP_NAME.tar.gz ($archive_size)"
        
        # Remove uncompressed backup
        rm -rf "$BACKUP_NAME"
        print_status "Temporary files cleaned up"
    else
        print_error "Failed to create backup archive"
        return 1
    fi
}

# Cleanup old backups
cleanup_old_backups() {
    print_status "Cleaning up old backups..."
    
    # Keep only last 10 backups
    cd "$BACKUP_DIR"
    backup_count=$(ls -1 voice_bridge_backup_*.tar.gz 2>/dev/null | wc -l)
    
    if [ "$backup_count" -gt 10 ]; then
        # Remove oldest backups
        ls -1t voice_bridge_backup_*.tar.gz | tail -n +11 | xargs rm -f
        removed_count=$((backup_count - 10))
        print_success "Removed $removed_count old backup(s)"
    else
        print_status "No old backups to remove (total: $backup_count)"
    fi
}

# Generate backup report
generate_report() {
    print_status "Generating backup report..."
    
    cat > "$BACKUP_DIR/backup_report_$TIMESTAMP.txt" << EOF
# Voice Bridge Pathology - Backup Report
# Generated: $(date)

## Backup Information
- Backup Name: $BACKUP_NAME
- Backup Date: $(date)
- Archive Size: $(du -h "$BACKUP_DIR/$BACKUP_NAME.tar.gz" 2>/dev/null | cut -f1 || echo "Unknown")

## Backup Contents
- Configuration files: $([ -d "$INSTALL_DIR/config" ] && echo "✓" || echo "✗")
- Medical dictionaries: $([ -d "$INSTALL_DIR/config/diccionarios" ] && echo "✓" || echo "✗")
- Recent logs: $([ -d "$INSTALL_DIR/logs" ] && echo "✓" || echo "✗")
- Environment info: ✓

## Medical Dictionary Statistics
EOF

    # Add dictionary statistics
    if [ -d "$INSTALL_DIR/config/diccionarios" ]; then
        for dict_file in "$INSTALL_DIR/config/diccionarios"/*.txt; do
            if [ -f "$dict_file" ]; then
                term_count=$(wc -l < "$dict_file")
                dict_name=$(basename "$dict_file")
                echo "- $dict_name: $term_count terms" >> "$BACKUP_DIR/backup_report_$TIMESTAMP.txt"
            fi
        done
    fi
    
    echo "" >> "$BACKUP_DIR/backup_report_$TIMESTAMP.txt"
    echo "## System Information" >> "$BACKUP_DIR/backup_report_$TIMESTAMP.txt"
    echo "- System: $(uname -a)" >> "$BACKUP_DIR/backup_report_$TIMESTAMP.txt"
    echo "- Python: $(python3 --version 2>/dev/null || echo "Not found")" >> "$BACKUP_DIR/backup_report_$TIMESTAMP.txt"
    echo "- Available backups: $(ls -1 "$BACKUP_DIR"/voice_bridge_backup_*.tar.gz 2>/dev/null | wc -l)" >> "$BACKUP_DIR/backup_report_$TIMESTAMP.txt"
    
    print_success "Backup report generated: backup_report_$TIMESTAMP.txt"
}

# Main backup function
main() {
    echo "=============================================="
    echo "   Voice Bridge Pathology - Backup System   "
    echo "=============================================="
    echo ""
    
    # Check if installation directory exists
    if [ ! -d "$INSTALL_DIR" ]; then
        print_error "Voice Bridge installation not found at $INSTALL_DIR"
        exit 1
    fi
    
    print_status "Starting backup process..."
    
    create_backup_directory
    backup_configuration
    backup_dictionaries
    backup_recent_logs
    backup_environment
    create_archive
    cleanup_old_backups
    generate_report
    
    echo ""
    echo "=============================================="
    echo "   Backup Completed Successfully!            "
    echo "=============================================="
    echo ""
    echo "📁 Backup location: $BACKUP_DIR/$BACKUP_NAME.tar.gz"
    echo "📊 Report: $BACKUP_DIR/backup_report_$TIMESTAMP.txt"
    echo ""
    echo "To restore from this backup:"
    echo "  tar -xzf $BACKUP_DIR/$BACKUP_NAME.tar.gz"
    echo "  cp -r $BACKUP_NAME/config/* $INSTALL_DIR/config/"
    echo ""
    
    print_success "Backup process completed!"
}

# Run main function
main "$@"
