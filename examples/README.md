# Voice Bridge Pathology - Example Files

This directory contains example files and templates to help you get started with Voice Bridge Pathology.

## Configuration Examples

### Azure Speech Services Configuration

The system supports multiple ways to configure Azure credentials:

1. **Environment Variables** (Recommended for development)
2. **Configuration File** (Recommended for production)
3. **Command Line Arguments** (For testing)

### Medical Dictionary Examples

Examples of how to structure your medical terminology files:

- **patologia_molecular.txt**: Individual medical terms
- **frases_completas.txt**: Complete medical phrases
- **custom_dictionaries/**: Specialty-specific vocabularies

## Scripts and Utilities

### Automation Scripts

- **start_voice_bridge.sh**: Main application launcher
- **test_azure_connection.sh**: Azure connectivity testing
- **add_medical_term.sh**: Easy term addition utility
- **backup_config.sh**: Configuration backup utility

### Development Scripts

- **run_tests.sh**: Execute test suite
- **format_code.sh**: Code formatting with black/isort
- **generate_docs.sh**: Documentation generation

## Desktop Integration

### Linux Desktop Entry

Example .desktop file for system integration:

- Application launcher integration
- System menu entry
- Custom icon support
- Proper categorization

### Service Configuration

Optional systemd service configuration for:

- Auto-start on login
- Background operation
- System-wide availability
- Logging integration

## Usage Examples

### Basic Usage Scenarios

1. **Single User Setup**: Personal pathology workstation
2. **Multi-User Environment**: Shared laboratory computer
3. **Clinical Integration**: Hospital information system
4. **Research Setup**: Academic research environment

### Advanced Configuration

- Custom hotkey mappings
- Audio device selection
- Claude Desktop integration settings
- Medical compliance configurations

## Troubleshooting Examples

Common configuration issues and their solutions:

- Azure authentication problems
- Audio device conflicts
- Linux permission issues
- Claude Desktop integration troubles

## Security Templates

Example security configurations for medical environments:

- HIPAA compliance guidelines
- Network security recommendations
- Access control templates
- Audit logging configurations

---

*Note: All example files are templates. Customize them according to your specific medical practice and compliance requirements.*
