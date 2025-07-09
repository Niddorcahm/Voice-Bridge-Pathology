# Voice Bridge Pathology - Test Suite

This directory contains tests for the Voice Bridge Pathology system.

## Test Structure

```
tests/
├── unit/                   # Unit tests
│   ├── test_config.py     # Configuration management tests
│   ├── test_medical_terms.py  # Medical dictionary tests
│   └── test_voice_commands.py # Voice command processing tests
├── integration/           # Integration tests
│   ├── test_azure_speech.py  # Azure Speech Services integration
│   └── test_claude_integration.py  # Claude Desktop integration
├── medical/              # Medical-specific tests
│   ├── test_pathology_terms.py  # Pathology terminology tests
│   └── test_medical_dictionaries.py  # Medical dictionary validation
├── fixtures/             # Test data and fixtures
│   ├── sample_audio/     # Sample audio files for testing
│   ├── sample_configs/   # Sample configuration files
│   └── medical_terms/    # Test medical terminology
└── conftest.py          # Pytest configuration and fixtures
```

## Running Tests

### All Tests
```bash
pytest
```

### Unit Tests Only
```bash
pytest tests/unit/
```

### Integration Tests (requires Azure credentials)
```bash
AZURE_SPEECH_KEY=your_key pytest tests/integration/
```

### Medical Tests
```bash
pytest tests/medical/ -m medical
```

### With Coverage
```bash
pytest --cov=voice_bridge_app --cov-report=html
```

## Test Categories

- **unit**: Fast tests that don't require external services
- **integration**: Tests requiring Azure Speech Services
- **medical**: Tests specific to medical functionality
- **slow**: Tests that take more than 10 seconds
- **ui**: Tests requiring GUI components

## Test Configuration

Set these environment variables for testing:

```bash
export AZURE_SPEECH_KEY_TEST="test_key_here"
export AZURE_SPEECH_REGION_TEST="eastus"
export TEST_MODE="true"
```

## Mocking

Tests use mocking for:
- Azure Speech Services (when credentials not available)
- GUI components (for headless testing)
- File system operations
- Network requests

## Medical Test Data

Medical tests use anonymized, fictional pathology terms and phrases that don't contain any real patient information.

## Contributing

When adding new tests:
1. Follow the existing naming conventions
2. Add appropriate markers for test categorization
3. Include docstrings explaining the test purpose
4. Mock external dependencies appropriately
5. Ensure medical tests use only fictional data

## Security

- Never include real patient data in tests
- Use environment variables for sensitive test credentials
- Ensure test data is properly anonymized
- Review test outputs for sensitive information leaks
