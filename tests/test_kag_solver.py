"""
Unit tests for KAG Solver Service
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.app.services.kag_solver_service import KAGSolverService

class TestKAGSolverService:
    
    def setup_method(self):
        """Setup test fixtures"""
        self.solver_service = KAGSolverService()
    
    def test_solver_initialization(self):
        """Test that solver initializes correctly"""
        assert self.solver_service is not None
        assert self.solver_service.solver is not None
    
    @pytest.mark.asyncio
    async def test_solve_query_basic(self):
        """Test basic query solving"""
        query = "什么是糖尿病?"
        result = await self.solver_service.solve_query(query)
        
        assert result is not None
        assert 'status' in result
        assert 'answer' in result
    
    @pytest.mark.asyncio
    async def test_solve_query_with_context(self):
        """Test query solving with context"""
        query = "糖尿病的治疗方法"
        context = {"patient_age": 45, "disease_type": "type2"}
        
        result = await self.solver_service.solve_query(query, context)
        
        assert result is not None
        assert 'status' in result
    
    def test_get_reasoning_explanation_empty(self):
        """Test reasoning explanation with empty trace"""
        explanation = self.solver_service.get_reasoning_explanation([])
        assert "No reasoning steps" in explanation
    
    def test_get_reasoning_explanation_with_steps(self):
        """Test reasoning explanation with steps"""
        trace = [
            {"type": "retrieval", "description": "检索相关文档"},
            {"type": "reasoning", "description": "推理分析"}
        ]
        explanation = self.solver_service.get_reasoning_explanation(trace)
        
        assert "推理过程" in explanation
        assert "retrieval" in explanation
        assert "reasoning" in explanation

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
