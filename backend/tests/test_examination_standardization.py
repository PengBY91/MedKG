"""
Unit tests for Examination Standardization Service
"""

import pytest
import asyncio
from app.services.examination_standardization_service import examination_service


class TestExaminationStandardization:
    """Test examination standardization service."""
    
    @pytest.mark.asyncio
    async def test_single_part_single_method(self):
        """Test: 手指正位片 → [['上肢', '手指', '正位']]"""
        result = await examination_service._standardize_single("手指正位片", "DR")
        
        assert result is not None
        assert len(result) == 1
        assert result[0] == ["上肢", "手指", "正位"]
    
    @pytest.mark.asyncio
    async def test_single_part_multiple_methods(self):
        """Test: 单手指正侧位片 → [['上肢', '手指', '正位'], ['上肢', '手指', '侧位']]"""
        result = await examination_service._standardize_single("单手指正侧位片", "DR")
        
        assert result is not None
        assert len(result) == 2
        assert ["上肢", "手指", "正位"] in result
        assert ["上肢", "手指", "侧位"] in result
    
    @pytest.mark.asyncio
    async def test_bilateral_examination(self):
        """Test: 双膝关节正位 → [['下肢', '膝关节', '正位']]"""
        result = await examination_service._standardize_single("双膝关节正位", "DR")
        
        assert result is not None
        assert len(result) == 1
        assert result[0] == ["下肢", "膝关节", "正位"]
    
    @pytest.mark.asyncio
    async def test_ct_modality(self):
        """Test: 腰椎CT平扫 → [['脊柱', '腰椎', '平扫']]"""
        result = await examination_service._standardize_single("腰椎CT平扫", "CT")
        
        assert result is not None
        assert len(result) >= 1
        # Should contain axial/sagittal views for CT
        assert any("平扫" in triple or "轴位" in triple for triple in result)
    
    @pytest.mark.asyncio
    async def test_mri_modality(self):
        """Test: 头颅MRI → should return valid MRI methods"""
        result = await examination_service._standardize_single("头颅MRI", "MRI")
        
        assert result is not None
        assert len(result) >= 1
        # MRI should have T1/T2 weighted or similar
    
    def test_parse_llm_response_valid_json(self):
        """Test parsing valid JSON response from LLM."""
        response = '[["上肢", "手指", "正位"], ["上肢", "手指", "侧位"]]'
        result = examination_service._parse_llm_response(response)
        
        assert len(result) == 2
        assert result[0] == ["上肢", "手指", "正位"]
        assert result[1] == ["上肢", "手指", "侧位"]
    
    def test_parse_llm_response_with_markdown(self):
        """Test parsing JSON wrapped in markdown code blocks."""
        response = '''```json
[["上肢", "手指", "正位"]]
```'''
        result = examination_service._parse_llm_response(response)
        
        assert len(result) == 1
        assert result[0] == ["上肢", "手指", "正位"]
    
    def test_parse_llm_response_invalid(self):
        """Test parsing invalid response."""
        response = "This is not JSON"
        result = examination_service._parse_llm_response(response)
        
        assert result == []
    
    def test_validate_result_valid_triple(self):
        """Test validation of valid triple."""
        result = [["上肢", "手指", "正位"]]
        validated = examination_service._validate_result(result)
        
        assert validated is not None
        assert len(validated) >= 1
    
    def test_validate_result_invalid_format(self):
        """Test validation rejects invalid format."""
        result = [["上肢", "手指"]]  # Missing method
        validated = examination_service._validate_result(result)
        
        # Should filter out invalid triples
        assert validated is None or len(validated) == 0
    
    def test_get_ontology_info(self):
        """Test getting ontology information."""
        ontology = examination_service.get_ontology_info()
        
        assert ontology is not None
        # Should contain basic ontology structure


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
