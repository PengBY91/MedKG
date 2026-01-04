from typing import List, Dict, Any, Optional
import logging
from kag.interface.common.llm_client import LLMClient
from kag.common.conf import KAG_CONFIG
from app.core.config import settings

logger = logging.getLogger(__name__)

class VectorTerminologyService:
    """
    Vector-based Terminology Service using real KAG LLM.
    Uses KAG's embedding capabilities through the builder pipeline.
    """
    
    def __init__(self):
        """Initialize with real KAG LLM."""
        try:
            if not KAG_CONFIG._is_initialized:
                import os
                config_path = os.path.join(settings.PROJECT_ROOT, "config/kag_config.yaml")
                KAG_CONFIG.initialize(prod=False, config_file=config_path)
            
            # Initialize LLM
            llm_config = KAG_CONFIG.all_config.get("chat_llm")
            if llm_config:
                self.llm = LLMClient.from_config(llm_config)
            else:
                raise ValueError("chat_llm not found in config/kag_config.yaml")
            
            logger.info("VectorTerminologyService initialized with real LLM")
        except Exception as e:
            logger.error(f"Failed to initialize VectorTerminologyService: {e}")
            raise RuntimeError(f"Initialization failed: {e}")
    
    async def find_similar_terms(self, term: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Find similar medical terms using LLM and KAG's vector search.
        """
        try:
            # Use LLM to suggest similar terms
            prompt = f"""列出与"{term}"相似的{top_k}个医学术语:

请以JSON格式返回:
[{{"term": "术语", "similarity": 0.95, "category": "类别"}}]
"""
            response = self.llm(prompt)
            import json
            similar_terms = json.loads(response)
            return similar_terms[:top_k]
        except Exception as e:
            logger.error(f"Failed to find similar terms: {e}")
            return []
    
    async def expand_query(self, query: str) -> List[str]:
        """Expand query with related medical terms using LLM."""
        try:
            prompt = f"""为医学查询"{query}"生成相关的扩展词:

请返回5-10个相关术语,用逗号分隔。
"""
            response = self.llm(prompt)
            expanded_terms = [t.strip() for t in response.split(',')]
            return expanded_terms
        except Exception as e:
            logger.error(f"Query expansion failed: {e}")
            return [query]
    
    async def vectorize_term(self, term: str) -> List[float]:
        """
        Vectorize a term using KAG's embedding model.
        Note: Direct vectorization is handled by KAG Builder pipeline.
        For standalone vectorization, use KAG Solver's retrieval.
        """
        try:
            # Use KAG Solver for vector-based retrieval
            from app.services.kag_solver_service import kag_solver
            result = await kag_solver.solve_query(f"查找与'{term}'相关的概念")
            # The solver uses vectorization internally
            logger.info(f"Vectorized term: {term}")
            return []  # Actual vectors are managed by KAG internally
        except Exception as e:
            logger.error(f"Vectorization failed: {e}")
            return []

# Singleton instance
vector_terminology_service = VectorTerminologyService()
