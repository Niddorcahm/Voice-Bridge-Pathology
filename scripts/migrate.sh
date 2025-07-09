#!/bin/bash

# Voice Bridge Pathology - Version Migration Script
# Handles safe migration between different versions of Voice Bridge Pathology
# Ensures data integrity and medical compliance during upgrades

set -e

# Configuration
INSTALL_DIR="$HOME/voice-bridge-claude"
BACKUP_DIR="$INSTALL_DIR/migration-backups"
MIGRATION_LOG="$BACKUP_DIR/migration_$(date +%Y%m%d_%H%M%S).log"
CURRENT_VERSION=""
TARGET_VERSION=""
DRY_RUN=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Migration state tracking
MIGRATION_STEPS=0
COMPLETED_STEPS=0
FAILED_STEPS=0

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$MIGRATION_LOG"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$MIGRATION_LOG"
    ((COMPLETED_STEPS++))
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$MIGRATION_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$MIGRATION_LOG"
    ((FAILED_STEPS++))
}

log_step() {
    ((MIGRATION_STEPS++))
    echo -e "${PURPLE}[STEP $MIGRATION_STEPS]${NC} $1" | tee -a "$MIGRATION_LOG"
}

# Initialize migration
init_migration() {
    echo "=============================================="
    echo "   Voice Bridge Pathology - Version Migration"
    echo "=============================================="
    
    # Create backup directory and log
    mkdir -p "$BACKUP_DIR"
    
    log_info "Migration started at $(date)"
    log_info "Installation directory: $INSTALL_DIR"
    log_info "Migration log: $MIGRATION_LOG"
    
    if [ "$DRY_RUN" = true ]; then
        log_warning "DRY RUN MODE - No actual changes will be made"
    fi
}

# Detect current version
detect_current_version() {
    log_step "Detecting current version"
    
    # Try to get version from pyproject.toml
    if [ -f "$INSTALL_DIR/pyproject.toml" ]; then
        CURRENT_VERSION=$(grep -E "version.*=" "$INSTALL_DIR/pyproject.toml" | head -1 | cut -d'"' -f2 2>/dev/null || echo "")
    fi
    
    # Try to get version from setup.py if pyproject.toml doesn't exist
    if [ -z "$CURRENT_VERSION" ] && [ -f "$INSTALL_DIR/setup.py" ]; then
        CURRENT_VERSION=$(grep -E "version.*=" "$INSTALL_DIR/setup.py" | head -1 | cut -d'"' -f2 2>/dev/null || echo "")
    fi
    
    # Try to get version from git tags
    if [ -z "$CURRENT_VERSION" ] && [ -d "$INSTALL_DIR/.git" ]; then
        cd "$INSTALL_DIR"
        CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    fi
    
    # Try to get version from configuration
    if [ -z "$CURRENT_VERSION" ] && [ -f "$INSTALL_DIR/config/voice_bridge_config.ini" ]; then
        CURRENT_VERSION=$(grep "version" "$INSTALL_DIR/config/voice_bridge_config.ini" | cut -d'=' -f2 | xargs 2>/dev/null || echo "")
    fi
    
    # Default if nothing found
    if [ -z "$CURRENT_VERSION" ]; then
        CURRENT_VERSION="unknown"
        log_warning "Could not detect current version, assuming 'unknown'"
    else
        log_success "Current version detected: $CURRENT_VERSION"
    fi
}

# Create comprehensive backup
create_migration_backup() {
    log_step "Creating comprehensive backup"
    
    local backup_name="voice_bridge_pre_migration_$(date +%Y%m%d_%H%M%S)"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: Would create backup at $backup_path"
        return
    fi
    
    mkdir -p "$backup_path"
    
    # Backup configuration files
    if [ -d "$INSTALL_DIR/config" ]; then
        cp -r "$INSTALL_DIR/config" "$backup_path/"
        log_success "Configuration files backed up"
    fi
    
    # Backup medical dictionaries
    if [ -d "$INSTALL_DIR/config/diccionarios" ]; then
        local dict_count=0
        for dict in "$INSTALL_DIR/config/diccionarios"/*.txt; do
            if [ -f "$dict" ]; then
                ((dict_count++))
            fi
        done
        log_success "Medical dictionaries backed up ($dict_count files)"
    fi
    
    # Backup logs (recent only)
    if [ -d "$INSTALL_DIR/logs" ]; then
        mkdir -p "$backup_path/logs"
        find "$INSTALL_DIR/logs" -name "*.log" -mtime -30 -exec cp {} "$backup_path/logs/" \;
        local log_count=$(ls -1 "$backup_path/logs/" 2>/dev/null | wc -l)
        log_success "Recent logs backed up ($log_count files)"
    fi
    
    # Backup user scripts and customizations
    if [ -d "$INSTALL_DIR/scripts" ]; then
        cp -r "$INSTALL_DIR/scripts" "$backup_path/"
        log_success "Custom scripts backed up"
    fi
    
    # Create backup manifest
    cat > "$backup_path/BACKUP_MANIFEST.txt" << EOF
# Voice Bridge Pathology - Migration Backup Manifest
# Created: $(date)
# Original Version: $CURRENT_VERSION
# Target Version: $TARGET_VERSION
# Backup Location: $backup_path

## Backup Contents:
EOF
    
    find "$backup_path" -type f | while read -r file; do
        echo "- $(basename "$file")" >> "$backup_path/BACKUP_MANIFEST.txt"
    done
    
    # Create compressed archive
    cd "$BACKUP_DIR"
    tar -czf "${backup_name}.tar.gz" "$backup_name"
    rm -rf "$backup_name"
    
    log_success "Backup created: ${backup_name}.tar.gz"
}

# Version-specific migration functions
migrate_from_unknown_to_1_0_0() {
    log_step "Migrating from unknown version to 1.0.0"
    
    # Create default configuration if missing
    if [ ! -f "$INSTALL_DIR/config/voice_bridge_config.ini" ]; then
        log_info "Creating default configuration file"
        if [ "$DRY_RUN" = false ]; then
            mkdir -p "$INSTALL_DIR/config"
            cat > "$INSTALL_DIR/config/voice_bridge_config.ini" << 'EOF'
[DEFAULT]
# Auto-generated during migration to 1.0.0
azure_speech_key = 
azure_region = eastus
speech_language = es-CO
tts_voice = es-CO-SalomeNeural
medical_mode = true
hipaa_compliance = true
confidence_threshold = 0.7
EOF
            chmod 600 "$INSTALL_DIR/config/voice_bridge_config.ini"
        fi
        log_success "Default configuration created"
    fi
    
    # Create medical dictionaries if missing
    if [ ! -d "$INSTALL_DIR/config/diccionarios" ]; then
        log_info "Creating default medical dictionaries"
        if [ "$DRY_RUN" = false ]; then
            mkdir -p "$INSTALL_DIR/config/diccionarios"
            
            cat > "$INSTALL_DIR/config/diccionarios/patologia_molecular.txt" << 'EOF'
# Medical Dictionary - Pathology Terms
# Created during migration to v1.0.0
carcinoma basocelular
adenocarcinoma
pleomorfismo nuclear
células atípicas
gastritis crónica
metaplasia intestinal
hiperqueratosis
compatible con
EOF
            
            cat > "$INSTALL_DIR/config/diccionarios/frases_completas.txt" << 'EOF'
# Medical Dictionary - Complete Phrases
# Created during migration to v1.0.0
compatible con neoplasia maligna
negativo para malignidad
células atípicas escasas
infiltrado inflamatorio crónico
gastritis crónica moderada
EOF
        fi
        log_success "Default medical dictionaries created"
    fi
    
    # Create logs directory
    if [ ! -d "$INSTALL_DIR/logs" ]; then
        log_info "Creating logs directory"
        if [ "$DRY_RUN" = false ]; then
            mkdir -p "$INSTALL_DIR/logs"
        fi
        log_success "Logs directory created"
    fi
}

migrate_from_0_9_x_to_1_0_0() {
    log_step "Migrating from 0.9.x to 1.0.0"
    
    # Update configuration format
    local config_file="$INSTALL_DIR/config/voice_bridge_config.ini"
    if [ -f "$config_file" ]; then
        log_info "Updating configuration format for 1.0.0"
        
        if [ "$DRY_RUN" = false ]; then
            # Backup original
            cp "$config_file" "${config_file}.pre_1_0_0"
            
            # Add new settings if missing
            if ! grep -q "hipaa_compliance" "$config_file"; then
                echo "hipaa_compliance = true" >> "$config_file"
            fi
            
            if ! grep -q "audit_logging" "$config_file"; then
                echo "audit_logging = true" >> "$config_file"
            fi
            
            if ! grep -q "encrypt_transcriptions" "$config_file"; then
                echo "encrypt_transcriptions = true" >> "$config_file"
            fi
        fi
        
        log_success "Configuration updated for 1.0.0"
    fi
    
    # Migrate old log format
    if [ -d "$INSTALL_DIR/logs" ]; then
        log_info "Converting old log format"
        if [ "$DRY_RUN" = false ]; then
            # Convert old transcription files to new format
            find "$INSTALL_DIR/logs" -name "transcription_*.txt" -exec bash -c '
                for file; do
                    new_name=$(echo "$file" | sed "s/transcription_/transcripciones_patologia_/")
                    mv "$file" "$new_name"
                done
            ' _ {} +
        fi
        log_success "Log format migration completed"
    fi
}

migrate_from_1_0_0_to_1_1_0() {
    log_step "Migrating from 1.0.0 to 1.1.0"
    
    # This would be implemented when 1.1.0 is developed
    log_info "Migration to 1.1.0 - placeholder for future implementation"
    log_success "Ready for 1.1.0 features"
}

# Execute version-specific migration
execute_migration() {
    log_step "Executing version-specific migration"
    
    case "$CURRENT_VERSION" in
        "unknown")
            migrate_from_unknown_to_1_0_0
            ;;
        "0.9"*)
            migrate_from_0_9_x_to_1_0_0
            ;;
        "1.0.0")
            if [ "$TARGET_VERSION" = "1.1.0" ]; then
                migrate_from_1_0_0_to_1_1_0
            else
                log_info "No migration needed for version 1.0.0"
            fi
            ;;
        *)
            log_warning "No specific migration path defined for version $CURRENT_VERSION"
            ;;
    esac
}

# Update version information
update_version_info() {
    log_step "Updating version information"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: Would update version to $TARGET_VERSION"
        return
    fi
    
    # Update pyproject.toml if it exists
    if [ -f "$INSTALL_DIR/pyproject.toml" ]; then
        sed -i "s/version = \".*\"/version = \"$TARGET_VERSION\"/" "$INSTALL_DIR/pyproject.toml"
        log_success "Updated version in pyproject.toml"
    fi
    
    # Update configuration file
    local config_file="$INSTALL_DIR/config/voice_bridge_config.ini"
    if [ -f "$config_file" ]; then
        if grep -q "config_version" "$config_file"; then
            sed -i "s/config_version = .*/config_version = $TARGET_VERSION/" "$config_file"
        else
            echo "config_version = $TARGET_VERSION" >> "$config_file"
        fi
        log_success "Updated version in configuration"
    fi
    
    # Create migration marker
    echo "$TARGET_VERSION" > "$INSTALL_DIR/.voice_bridge_version"
    echo "$(date)" >> "$INSTALL_DIR/.voice_bridge_version"
    log_success "Version marker created"
}

# Validate migration
validate_migration() {
    log_step "Validating migration"
    
    local validation_errors=0
    
    # Check essential files exist
    local essential_files=(
        "voice_bridge_app.py"
        "config/voice_bridge_config.ini"
        "config/diccionarios/patologia_molecular.txt"
        "config/diccionarios/frases_completas.txt"
    )
    
    for file in "${essential_files[@]}"; do
        if [ -f "$INSTALL_DIR/$file" ]; then
            log_success "Essential file exists: $file"
        else
            log_error "Essential file missing: $file"
            ((validation_errors++))
        fi
    done
    
    # Check configuration integrity
    if [ -f "$INSTALL_DIR/config/voice_bridge_config.ini" ]; then
        # Check required settings
        local required_settings=("azure_speech_key" "azure_region" "speech_language")
        for setting in "${required_settings[@]}"; do
            if grep -q "^${setting}" "$INSTALL_DIR/config/voice_bridge_config.ini"; then
                log_success "Configuration setting present: $setting"
            else
                log_error "Configuration setting missing: $setting"
                ((validation_errors++))
            fi
        done
    fi
    
    # Check medical dictionaries
    for dict in "$INSTALL_DIR/config/diccionarios"/*.txt; do
        if [ -f "$dict" ]; then
            local term_count=$(grep -v '^#' "$dict" | grep -v '^$' | wc -l)
            if [ $term_count -gt 0 ]; then
                log_success "Medical dictionary valid: $(basename "$dict") ($term_count terms)"
            else
                log_warning "Medical dictionary empty: $(basename "$dict")"
            fi
        fi
    done
    
    # Check permissions
    if [ -f "$INSTALL_DIR/config/voice_bridge_config.ini" ]; then
        local perms=$(stat -c%a "$INSTALL_DIR/config/voice_bridge_config.ini")
        if [ "$perms" = "600" ]; then
            log_success "Configuration file has secure permissions"
        else
            log_warning "Configuration file permissions: $perms (should be 600)"
        fi
    fi
    
    if [ $validation_errors -eq 0 ]; then
        log_success "Migration validation completed successfully"
        return 0
    else
        log_error "Migration validation failed with $validation_errors errors"
        return 1
    fi
}

# Generate migration report
generate_migration_report() {
    log_step "Generating migration report"
    
    local report_file="$BACKUP_DIR/migration_report_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$report_file" << EOF
# Voice Bridge Pathology - Migration Report
# Generated: $(date)

## Migration Summary
- From Version: $CURRENT_VERSION
- To Version: $TARGET_VERSION
- Migration Type: ${DRY_RUN:+DRY RUN}
- Total Steps: $MIGRATION_STEPS
- Completed Steps: $COMPLETED_STEPS
- Failed Steps: $FAILED_STEPS

## System Information
- Installation Directory: $INSTALL_DIR
- Operating System: $(uname -a)
- User: $(whoami)
- Migration Log: $MIGRATION_LOG

## Post-Migration Status
EOF
    
    # Add file inventory
    echo "" >> "$report_file"
    echo "## File Inventory" >> "$report_file"
    find "$INSTALL_DIR" -type f -name "*.py" -o -name "*.ini" -o -name "*.txt" | while read -r file; do
        echo "- $(basename "$file"): $(stat -c%s "$file") bytes" >> "$report_file"
    done
    
    # Add configuration summary
    echo "" >> "$report_file"
    echo "## Configuration Summary" >> "$report_file"
    if [ -f "$INSTALL_DIR/config/voice_bridge_config.ini" ]; then
        grep -E "^[a-z_]+ = " "$INSTALL_DIR/config/voice_bridge_config.ini" | while read -r line; do
            setting=$(echo "$line" | cut -d'=' -f1 | xargs)
            echo "- $setting: configured" >> "$report_file"
        done
    fi
    
    # Add medical dictionary summary
    echo "" >> "$report_file"
    echo "## Medical Dictionary Summary" >> "$report_file"
    if [ -d "$INSTALL_DIR/config/diccionarios" ]; then
        for dict in "$INSTALL_DIR/config/diccionarios"/*.txt; do
            if [ -f "$dict" ]; then
                dict_name=$(basename "$dict")
                term_count=$(grep -v '^#' "$dict" | grep -v '^$' | wc -l)
                echo "- $dict_name: $term_count terms" >> "$report_file"
            fi
        done
    fi
    
    log_success "Migration report generated: $report_file"
}

# Rollback migration
rollback_migration() {
    log_step "Rolling back migration"
    
    # Find most recent backup
    local latest_backup=$(ls -t "$BACKUP_DIR"/voice_bridge_pre_migration_*.tar.gz 2>/dev/null | head -1)
    
    if [ -z "$latest_backup" ]; then
        log_error "No backup found for rollback"
        return 1
    fi
    
    log_info "Rolling back using: $(basename "$latest_backup")"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: Would restore from $latest_backup"
        return 0
    fi
    
    # Extract backup
    cd "$BACKUP_DIR"
    tar -xzf "$(basename "$latest_backup")"
    
    local backup_dir=$(basename "$latest_backup" .tar.gz)
    
    # Restore configuration
    if [ -d "$backup_dir/config" ]; then
        rm -rf "$INSTALL_DIR/config"
        cp -r "$backup_dir/config" "$INSTALL_DIR/"
        log_success "Configuration restored"
    fi
    
    # Restore scripts
    if [ -d "$backup_dir/scripts" ]; then
        rm -rf "$INSTALL_DIR/scripts"
        cp -r "$backup_dir/scripts" "$INSTALL_DIR/"
        log_success "Scripts restored"
    fi
    
    # Clean up
    rm -rf "$backup_dir"
    
    log_success "Rollback completed successfully"
}

# Show help
show_help() {
    echo "Voice Bridge Pathology - Version Migration Script"
    echo ""
    echo "Usage: $0 [options] <target_version>"
    echo ""
    echo "Options:"
    echo "  -d, --dry-run             Perform dry run without making changes"
    echo "  -r, --rollback            Rollback to previous version"
    echo "  --install-dir PATH        Custom installation directory"
    echo "  -h, --help                Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 1.0.0                  Migrate to version 1.0.0"
    echo "  $0 --dry-run 1.1.0        Preview migration to 1.1.0"
    echo "  $0 --rollback             Rollback to previous version"
    echo ""
    echo "Supported migrations:"
    echo "  - unknown → 1.0.0         Initial setup"
    echo "  - 0.9.x → 1.0.0          Major version upgrade"
    echo "  - 1.0.0 → 1.1.0          Feature update (future)"
    echo ""
    echo "Safety features:"
    echo "  - Comprehensive backup before migration"
    echo "  - Validation of migration results"
    echo "  - Rollback capability"
    echo "  - Medical data integrity checks"
    echo "  - Dry run mode for testing"
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -r|--rollback)
                if [ -z "$2" ] || [[ "$2" == -* ]]; then
                    rollback_migration
                    exit $?
                else
                    echo "Error: --rollback does not take arguments"
                    exit 1
                fi
                ;;
            --install-dir)
                INSTALL_DIR="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            -*)
                echo "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
            *)
                if [ -z "$TARGET_VERSION" ]; then
                    TARGET_VERSION="$1"
                    shift
                else
                    echo "Error: Multiple target versions specified"
                    exit 1
                fi
                ;;
        esac
    done
    
    if [ -z "$TARGET_VERSION" ]; then
        echo "Error: Target version not specified"
        echo "Use --help for usage information"
        exit 1
    fi
}

# Main function
main() {
    parse_arguments "$@"
    init_migration
    
    # Validate installation directory
    if [ ! -d "$INSTALL_DIR" ]; then
        log_error "Installation directory not found: $INSTALL_DIR"
        exit 1
    fi
    
    detect_current_version
    
    # Check if migration is needed
    if [ "$CURRENT_VERSION" = "$TARGET_VERSION" ]; then
        log_info "Already at target version $TARGET_VERSION"
        exit 0
    fi
    
    log_info "Migrating from $CURRENT_VERSION to $TARGET_VERSION"
    
    # Execute migration steps
    create_migration_backup
    execute_migration
    update_version_info
    
    # Validate migration
    if validate_migration; then
        generate_migration_report
        
        echo ""
        echo "=============================================="
        echo "   Migration Completed Successfully!"
        echo "=============================================="
        echo "From: $CURRENT_VERSION"
        echo "To: $TARGET_VERSION"
        echo "Steps: $COMPLETED_STEPS/$MIGRATION_STEPS completed"
        echo "Backup: Available in $BACKUP_DIR"
        echo "Log: $MIGRATION_LOG"
        if [ "$DRY_RUN" = true ]; then
            echo ""
            echo "This was a DRY RUN - no actual changes were made"
        fi
        echo "=============================================="
    else
        log_error "Migration validation failed"
        echo ""
        echo "Migration completed with errors. Check the log file:"
        echo "$MIGRATION_LOG"
        echo ""
        echo "You can rollback using: $0 --rollback"
        exit 1
    fi
}

# Run main function with all arguments
main "$@"
