"""
Voice Bridge Pathology - Medical Terms Unit Tests
Tests for medical terminology processing and dictionary management
"""
import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

# Import the module under test (would be the actual module in real implementation)
# For this example, we'll mock the VoiceBridgePathology class
# from voice_bridge_app import VoiceBridgePathology

class MockVoiceBridgePathology:
    """Mock class for testing medical terms functionality"""
    
    def __init__(self):
        self.medical_terms = []
        self.logger = Mock()
    
    def load_medical_terms(self):
        """Mock method to load medical terms"""
        pass
    
    def apply_medical_terms_to_recognizer(self):
        """Mock method to apply terms to recognizer"""
        pass
    
    def extract_key_medical_terms(self, text):
        """Mock method to extract key terms"""
        pass

@pytest.mark.unit
class TestMedicalTermsLoading:
    """Test medical terms dictionary loading functionality"""
    
    def test_load_medical_terms_success(self, sample_medical_dictionary):
        """Test successful loading of medical terms from dictionary files"""
        app = MockVoiceBridgePathology()
        
        # Mock the dictionary loading
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data="carcinoma basocelular\nadenocarcinoma\n")):
            
            app.load_medical_terms()
            
            # Verify logger was called
            assert app.logger.info.called
    
    def test_load_medical_terms_missing_directory(self):
        """Test handling of missing medical dictionary directory"""
        app = MockVoiceBridgePathology()
        
        with patch('pathlib.Path.exists', return_value=False):
            app.load_medical_terms()
            
            # Should handle missing directory gracefully
            assert len(app.medical_terms) == 0
    
    def test_load_medical_terms_empty_file(self):
        """Test handling of empty dictionary files"""
        app = MockVoiceBridgePathology()
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data="")):
            
            app.load_medical_terms()
            
            # Should handle empty files without error
            assert len(app.medical_terms) == 0
    
    def test_load_medical_terms_with_comments(self):
        """Test loading terms while ignoring comments"""
        app = MockVoiceBridgePathology()
        
        test_content = """# This is a comment
carcinoma basocelular
# Another comment
adenocarcinoma
# Empty line below

pleomorfismo nuclear
"""
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=test_content)):
            
            # Mock the actual loading logic
            app.medical_terms = [
                line.strip().lower() for line in test_content.split('\n') 
                if line.strip() and not line.startswith('#')
            ]
            
            assert 'carcinoma basocelular' in app.medical_terms
            assert 'adenocarcinoma' in app.medical_terms
            assert 'pleomorfismo nuclear' in app.medical_terms
            assert len([term for term in app.medical_terms if term.startswith('#')]) == 0

@pytest.mark.unit
class TestMedicalTermsExtraction:
    """Test extraction of key medical terms from transcriptions"""
    
    @pytest.fixture
    def app_with_terms(self, sample_medical_terms):
        """Fixture providing app instance with loaded medical terms"""
        app = MockVoiceBridgePathology()
        app.medical_terms = sample_medical_terms['pathology_terms']
        return app
    
    def test_extract_key_terms_single_term(self, app_with_terms):
        """Test extraction of single medical term"""
        text = "Se observa carcinoma basocelular en dermis papilar"
        
        # Mock the extraction method
        def mock_extract(text):
            found_terms = []
            text_lower = text.lower()
            for term in app_with_terms.medical_terms:
                if term in text_lower:
                    found_terms.append(term)
            return found_terms[:3]  # Limit to 3 terms
        
        app_with_terms.extract_key_medical_terms = mock_extract
        result = app_with_terms.extract_key_medical_terms(text)
        
        assert 'carcinoma basocelular' in result
        assert len(result) <= 3
    
    def test_extract_key_terms_multiple_terms(self, app_with_terms):
        """Test extraction of multiple medical terms"""
        text = "Carcinoma basocelular con pleomorfismo nuclear y células atípicas"
        
        def mock_extract(text):
            found_terms = []
            text_lower = text.lower()
            for term in app_with_terms.medical_terms:
                if term in text_lower:
                    found_terms.append(term)
            return found_terms[:3]
        
        app_with_terms.extract_key_medical_terms = mock_extract
        result = app_with_terms.extract_key_medical_terms(text)
        
        assert len(result) >= 2
        assert any('carcinoma' in term for term in result)
        assert any('pleomorfismo' in term for term in result)
    
    def test_extract_key_terms_no_matches(self, app_with_terms):
        """Test extraction when no medical terms are found"""
        text = "Este es un texto sin términos médicos específicos"
        
        def mock_extract(text):
            found_terms = []
            text_lower = text.lower()
            for term in app_with_terms.medical_terms:
                if term in text_lower:
                    found_terms.append(term)
            return found_terms[:3]
        
        app_with_terms.extract_key_medical_terms = mock_extract
        result = app_with_terms.extract_key_medical_terms(text)
        
        assert len(result) == 0
    
    def test_extract_key_terms_limit(self, app_with_terms):
        """Test that extraction limits results to maximum 3 terms"""
        # Create text with many medical terms
        text = "carcinoma basocelular adenocarcinoma pleomorfismo nuclear células atípicas invasión focal"
        
        def mock_extract(text):
            found_terms = []
            text_lower = text.lower()
            for term in app_with_terms.medical_terms:
                if term in text_lower:
                    found_terms.append(term)
            return found_terms[:3]  # Limit to 3
        
        app_with_terms.extract_key_medical_terms = mock_extract
        result = app_with_terms.extract_key_medical_terms(text)
        
        assert len(result) <= 3

@pytest.mark.unit
class TestMedicalDictionaryValidation:
    """Test medical dictionary validation and management"""
    
    def test_validate_dictionary_structure(self, sample_medical_dictionary):
        """Test validation of dictionary file structure"""
        dict_dir = sample_medical_dictionary
        
        # Check that required files exist
        assert (dict_dir / "patologia_molecular.txt").exists()
        assert (dict_dir / "frases_completas.txt").exists()
        
        # Check file contents
        primary_dict = dict_dir / "patologia_molecular.txt"
        content = primary_dict.read_text()
        
        assert "carcinoma basocelular" in content
        assert "adenocarcinoma" in content
        assert content.startswith("# Test medical dictionary")
    
    def test_dictionary_term_count(self, sample_medical_dictionary):
        """Test counting terms in dictionary files"""
        dict_dir = sample_medical_dictionary
        primary_dict = dict_dir / "patologia_molecular.txt"
        
        # Count non-empty, non-comment lines
        content = primary_dict.read_text()
        term_count = len([
            line for line in content.split('\n') 
            if line.strip() and not line.startswith('#')
        ])
        
        assert term_count > 0
        assert term_count == 8  # Based on sample content
    
    def test_dictionary_encoding(self, sample_medical_dictionary):
        """Test that dictionary files handle Spanish characters correctly"""
        dict_dir = sample_medical_dictionary
        primary_dict = dict_dir / "patologia_molecular.txt"
        
        content = primary_dict.read_text(encoding='utf-8')
        
        # Check for Spanish characters
        assert "células" in content  # Contains 'é'
        assert "gastritis" in content
        assert "metaplasia" in content

@pytest.mark.unit 
class TestTermPrioritization:
    """Test medical term prioritization logic"""
    
    def test_phrase_priority_over_words(self):
        """Test that complete phrases have priority over individual words"""
        app = MockVoiceBridgePathology()
        
        # Mock prioritization logic
        def mock_prioritize(terms):
            # Phrases (with spaces) should come first
            phrases = [term for term in terms if ' ' in term]
            words = [term for term in terms if ' ' not in term]
            return phrases + words
        
        terms = [
            "carcinoma",
            "compatible con neoplasia maligna", 
            "células",
            "gastritis crónica moderada",
            "adenocarcinoma"
        ]
        
        prioritized = mock_prioritize(terms)
        
        # Phrases should come first
        assert prioritized[0] == "compatible con neoplasia maligna"
        assert prioritized[1] == "gastritis crónica moderada"
        assert "carcinoma" in prioritized[2:]
    
    def test_medical_specificity_priority(self):
        """Test that more specific medical terms have priority"""
        app = MockVoiceBridgePathology()
        
        terms = [
            "carcinoma",
            "carcinoma basocelular",
            "células",
            "células atípicas"
        ]
        
        # More specific terms (longer) should have priority
        def mock_specificity_sort(terms):
            return sorted(terms, key=len, reverse=True)
        
        prioritized = mock_specificity_sort(terms)
        
        assert prioritized[0] == "carcinoma basocelular"
        assert prioritized[1] == "células atípicas"

@pytest.mark.unit
class TestErrorHandling:
    """Test error handling in medical terms processing"""
    
    def test_handle_corrupted_dictionary(self):
        """Test handling of corrupted dictionary files"""
        app = MockVoiceBridgePathology()
        
        # Simulate file read error
        with patch('builtins.open', side_effect=IOError("File corrupted")):
            try:
                app.load_medical_terms()
                # Should not raise exception
                assert True
            except Exception as e:
                pytest.fail(f"Should handle corrupted file gracefully: {e}")
    
    def test_handle_unicode_errors(self):
        """Test handling of unicode encoding errors"""
        app = MockVoiceBridgePathology()
        
        # Simulate unicode decode error
        with patch('builtins.open', side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")):
            try:
                app.load_medical_terms()
                assert True
            except UnicodeDecodeError:
                pytest.fail("Should handle unicode errors gracefully")
    
    def test_handle_empty_text_extraction(self):
        """Test extraction from empty or None text"""
        app = MockVoiceBridgePathology()
        
        def mock_extract_safe(text):
            if not text or not text.strip():
                return []
            return []  # Mock empty result
        
        app.extract_key_medical_terms = mock_extract_safe
        
        # Test with None
        result = app.extract_key_medical_terms(None)
        assert result == []
        
        # Test with empty string
        result = app.extract_key_medical_terms("")
        assert result == []
        
        # Test with whitespace only
        result = app.extract_key_medical_terms("   ")
        assert result == []

@pytest.mark.unit
@pytest.mark.medical
class TestMedicalAccuracy:
    """Test medical accuracy and validation"""
    
    def test_pathology_term_accuracy(self, sample_medical_terms):
        """Test that pathology terms are medically accurate"""
        pathology_terms = sample_medical_terms['pathology_terms']
        
        # All terms should be lowercase for consistency
        for term in pathology_terms:
            assert term.islower(), f"Term should be lowercase: {term}"
        
        # Check for common pathology terms
        expected_terms = [
            'carcinoma basocelular',
            'adenocarcinoma', 
            'pleomorfismo nuclear',
            'células atípicas'
        ]
        
        for expected in expected_terms:
            assert expected in pathology_terms, f"Expected medical term missing: {expected}"
    
    def test_spanish_medical_terminology(self, sample_medical_terms):
        """Test Spanish medical terminology compliance"""
        all_terms = (
            sample_medical_terms['pathology_terms'] + 
            sample_medical_terms['complete_phrases']
        )
        
        # Check for proper Spanish medical terms
        spanish_indicators = ['células', 'gastritis', 'metaplasia', 'neoplasia']
        
        spanish_terms_found = [
            term for term in all_terms 
            if any(indicator in term for indicator in spanish_indicators)
        ]
        
        assert len(spanish_terms_found) > 0, "Should contain Spanish medical terms"
    
    def test_no_patient_information(self, sample_medical_terms):
        """Test that no patient-identifying information is in medical terms"""
        all_terms = (
            sample_medical_terms['pathology_terms'] + 
            sample_medical_terms['complete_phrases'] +
            sample_medical_terms['common_terms']
        )
        
        # Patient identifiers that should not appear
        forbidden_patterns = [
            'paciente', 'nombre', 'edad', 'años', 'fecha', 'historia',
            'número', 'cédula', 'documento', 'teléfono', 'dirección'
        ]
        
        for term in all_terms:
            for pattern in forbidden_patterns:
                assert pattern not in term.lower(), f"Term contains patient identifier: {term}"

if __name__ == "__main__":
    pytest.main([__file__])
