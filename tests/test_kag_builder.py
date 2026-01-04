"""
Unit tests for KAG Medical Builder
"""
import pytest
import tempfile
import os
from unittest.mock import Mock, patch

# Mock the imports before importing the service
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.app.services.kag_medical_builder import KAGMedicalBuilder

class TestKAGMedicalBuilder:
    
    def setup_method(self):
        """Setup test fixtures"""
        self.builder = KAGMedicalBuilder()
    
    def test_builder_initialization(self):
        """Test that builder initializes correctly"""
        assert self.builder is not None
        assert self.builder.config_path.endswith('kag_config.yaml')
    
    def test_build_document_file_not_found(self):
        """Test error handling for non-existent file"""
        with pytest.raises(FileNotFoundError):
            self.builder.build_document('/nonexistent/file.txt')
    
    def test_build_document_success(self):
        """Test successful document building"""
        # Create temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("测试文档内容:糖尿病是一种慢性疾病。")
            temp_file = f.name
        
        try:
            result = self.builder.build_document(temp_file)
            assert result is not None
            assert result['status'] == 'success'
            assert result['file'] == temp_file
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_build_document_with_pdf(self):
        """Test PDF document handling"""
        # Create temporary PDF file (empty for testing)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_file = f.name
        
        try:
            # Should not raise error even with empty PDF
            result = self.builder.build_document(temp_file)
            assert result is not None
        except Exception as e:
            # Expected to fail with empty PDF, but should handle gracefully
            assert 'error' in str(e).lower() or result['status'] == 'error'
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
