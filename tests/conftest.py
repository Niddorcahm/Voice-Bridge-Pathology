"""
Voice Bridge Pathology - Test Configuration
Pytest configuration and shared fixtures for the test suite
"""
import os
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Test configuration
TEST_DATA_DIR = Path(__file__).parent / "fixtures"
SAMPLE_AUDIO_DIR = TEST_DATA_DIR / "sample_audio"
SAMPLE_CONFIGS_DIR = TEST_DATA_DIR / "sample_configs"

@pytest.fixture(scope="session")
def test_data_dir():
    """Fixture providing path to test data directory."""
    return TEST_DATA_DIR

@pytest.fixture(scope="session")
def sample_audio_dir():
    """Fixture providing path to sample audio files."""
    return SAMPLE_AUDIO_DIR

@pytest.fixture(scope="function")
def temp_config_dir():
    """Fixture providing temporary configuration directory."""
    temp_dir = tempfile.mkdtemp(prefix="voice_bridge_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture(scope="function")
def sample_config_file(temp_config_dir):
    """Fixture providing sample configuration file."""
    config_content = """[DEFAULT]
azure_speech_key = test_key_12345
azure_region = eastus
speech_language = es-CO
tts_voice = es-CO-SalomeNeural
hotkey_start = ctrl+shift+v
hotkey_stop = ctrl+shift+s
auto_send_to_claude = true
medical_mode = true
confidence_threshold = 0.7
tts_enabled = false
"""
    config_file = temp_config_dir / "test_config.ini"
    config_file.write_text(config_content)
    return config_file

@pytest.fixture(scope="function")
def sample_medical_dictionary(temp_config_dir):
    """Fixture providing sample medical dictionary."""
    dict_dir = temp_config_dir / "diccionarios"
    dict_dir.mkdir()
    
    # Primary dictionary
    primary_dict = dict_dir / "patologia_molecular.txt"
    primary_dict.write_text("""# Test medical dictionary
carcinoma basocelular
adenocarcinoma
pleomorfismo nuclear
células atípicas
gastritis crónica
metaplasia intestinal
hiperqueratosis
compatible con
""")
    
    # Phrases dictionary
    phrases_dict = dict_dir / "frases_completas.txt"
    phrases_dict.write_text("""# Test phrases dictionary
compatible con neoplasia maligna
negativo para malignidad
células atípicas escasas
infiltrado inflamatorio crónico
gastritis crónica moderada
""")
    
    return dict_dir

@pytest.fixture(scope="function")
def mock_azure_speech_config():
    """Fixture providing mocked Azure Speech configuration."""
    mock_config = Mock()
    mock_config.speech_recognition_language = "es-CO"
    mock_config.speech_synthesis_voice_name = "es-CO-SalomeNeural"
    mock_config.set_property = Mock()
    return mock_config

@pytest.fixture(scope="function")
def mock_speech_recognizer():
    """Fixture providing mocked Azure Speech recognizer."""
    mock_recognizer = Mock()
    mock_recognizer.start_continuous_recognition_async = Mock()
    mock_recognizer.stop_continuous_recognition_async = Mock()
    mock_recognizer.recognized = Mock()
    mock_recognizer.recognizing = Mock()
    mock_recognizer.canceled = Mock()
    return mock_recognizer

@pytest.fixture(scope="function")
def mock_speech_synthesizer():
    """Fixture providing mocked Azure Speech synthesizer."""
    mock_synthesizer = Mock()
    mock_result = Mock()
    mock_result.reason = "SynthesizingAudioCompleted"
    mock_synthesizer.speak_text_async.return_value.get.return_value = mock_result
    return mock_synthesizer

@pytest.fixture(scope="function")
def mock_gui_components():
    """Fixture providing mocked GUI components."""
    mock_root = Mock()
    mock_frame = Mock()
    mock_button = Mock()
    mock_text = Mock()
    mock_label = Mock()
    
    # Setup mock hierarchy
    mock_root.title = Mock()
    mock_root.geometry = Mock()
    mock_root.protocol = Mock()
    mock_root.after = Mock()
    mock_root.mainloop = Mock()
    
    return {
        'root': mock_root,
        'frame': mock_frame,
        'button': mock_button,
        'text': mock_text,
        'label': mock_label
    }

@pytest.fixture(scope="function") 
def mock_environment_variables():
    """Fixture providing mocked environment variables."""
    original_env = os.environ.copy()
    
    # Set test environment variables
    os.environ.update({
        'AZURE_SPEECH_KEY': 'test_key_12345',
        'AZURE_SPEECH_REGION': 'eastus',
        'SPEECH_LANGUAGE': 'es-CO',
        'TTS_VOICE': 'es-CO-SalomeNeural',
        'TEST_MODE': 'true'
    })
    
    yield os.environ
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)

@pytest.fixture(scope="function")
def mock_system_commands():
    """Fixture providing mocked system commands."""
    import subprocess
    
    original_run = subprocess.run
    
    def mock_run(cmd, *args, **kwargs):
        # Mock common system commands
        if 'wmctrl' in cmd:
            if '-l' in cmd:
                # Mock window list
                mock_result = Mock()
                mock_result.stdout = "0x12345 0 hostname Claude\n0x67890 0 hostname Firefox"
                mock_result.returncode = 0
                return mock_result
            else:
                # Mock window activation
                mock_result = Mock()
                mock_result.returncode = 0
                return mock_result
        elif 'xdotool' in cmd:
            # Mock xdotool commands
            mock_result = Mock()
            mock_result.returncode = 0
            return mock_result
        elif 'curl' in cmd:
            # Mock Azure connectivity test
            mock_result = Mock()
            mock_result.stdout = "200"
            mock_result.returncode = 0
            return mock_result
        else:
            # Use original for other commands
            return original_run(cmd, *args, **kwargs)
    
    subprocess.run = mock_run
    yield subprocess.run
    subprocess.run = original_run

@pytest.fixture(scope="function")
def sample_transcription_data():
    """Fixture providing sample transcription data."""
    return [
        {
            'type': 'final',
            'text': 'Carcinoma basocelular con pleomorfismo nuclear',
            'confidence': 0.85,
            'timestamp': '2025-07-07 10:30:15'
        },
        {
            'type': 'final', 
            'text': 'Compatible con gastritis crónica moderada',
            'confidence': 0.92,
            'timestamp': '2025-07-07 10:31:22'
        },
        {
            'type': 'final',
            'text': 'Células atípicas escasas en dermis papilar',
            'confidence': 0.78,
            'timestamp': '2025-07-07 10:32:45'
        }
    ]

@pytest.fixture(scope="function")
def sample_medical_terms():
    """Fixture providing sample medical terms for testing."""
    return {
        'pathology_terms': [
            'carcinoma basocelular',
            'adenocarcinoma',
            'pleomorfismo nuclear',
            'células atípicas',
            'invasión focal',
            'dermis papilar',
            'hiperqueratosis',
            'paraqueratosis'
        ],
        'complete_phrases': [
            'compatible con neoplasia maligna',
            'negativo para malignidad',
            'células atípicas escasas',
            'infiltrado inflamatorio crónico',
            'gastritis crónica moderada',
            'metaplasia intestinal incompleta'
        ],
        'common_terms': [
            'compatible con',
            'negativo para',
            'positivo para',
            'sugestivo de',
            'consistente con'
        ]
    }

# Pytest markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests that don't require external services"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests that require Azure services"
    )
    config.addinivalue_line(
        "markers", "medical: Tests specific to medical functionality"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests that take more than 10 seconds"
    )
    config.addinivalue_line(
        "markers", "ui: Tests that require GUI components"
    )

# Skip integration tests if Azure credentials not available
def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip integration tests without credentials."""
    skip_integration = pytest.mark.skip(reason="Azure credentials not available")
    
    azure_key = os.environ.get('AZURE_SPEECH_KEY') or os.environ.get('AZURE_SPEECH_KEY_TEST')
    
    if not azure_key:
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)

# Cleanup after tests
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_files():
    """Cleanup any test files created during testing."""
    yield
    
    # Clean up any temporary test files
    temp_files = [
        "test_transcription.txt",
        "test_config.ini",
        "test_log.log"
    ]
    
    for file in temp_files:
        if os.path.exists(file):
            os.remove(file)

# Logging configuration for tests
@pytest.fixture(scope="session", autouse=True)
def configure_test_logging():
    """Configure logging for tests."""
    import logging
    
    # Reduce logging noise during tests
    logging.getLogger('azure').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # Configure test logger
    test_logger = logging.getLogger('voice_bridge_test')
    test_logger.setLevel(logging.DEBUG)
    
    # Add console handler for test output
    if not test_logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        test_logger.addHandler(handler)
    
    yield test_logger
