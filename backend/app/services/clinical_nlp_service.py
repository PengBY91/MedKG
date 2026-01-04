from typing import List, Dict, Any
import logging
from kag.interface.common.llm_client import LLMClient
from kag.common.conf import KAG_CONFIG
from app.core.config import settings

logger = logging.getLogger(__name__)

class ClinicalNLPService:
    """
    Clinical NLP Service using KAG LLM for medical text processing.
    """
    
    def __init__(self):
        """Initialize with real KAG LLM client."""
        try:
            # Initialize KAG config if not already done
            if not KAG_CONFIG._is_initialized:
                import os
                config_path = os.path.join(settings.PROJECT_ROOT, "config/kag_config.yaml")
                KAG_CONFIG.initialize(prod=False, config_file=config_path)
            
            # Get LLM config from KAG
            llm_config = KAG_CONFIG.all_config.get("chat_llm")
            if not llm_config:
                raise ValueError("chat_llm not found in config/kag_config.yaml")
            
            self.llm = LLMClient.from_config(llm_config)
            logger.info("ClinicalNLPService initialized with real LLM")
        except Exception as e:
            logger.error(f"Failed to initialize ClinicalNLPService: {e}")
            raise RuntimeError(f"LLM initialization failed: {e}")
    
    async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract medical entities from text using LLM."""
        try:
            prompt = f"""从以下医学文本中提取实体(疾病、药物、症状等):

文本: {text}

请以JSON格式返回,格式如下:
[{{"entity": "实体名称", "type": "实体类型", "offset": [起始位置, 结束位置]}}]
"""
            response = self.llm(prompt)
            # Parse LLM response
            import json
            entities = json.loads(response)
            return entities
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return []
    
    async def extract_relations(self, text: str) -> List[Dict[str, Any]]:
        """Extract medical relations from text using LLM."""
        try:
            prompt = f"""从以下医学文本中提取实体关系:

文本: {text}

请以JSON格式返回,格式如下:
[{{"subject": "主体", "predicate": "关系", "object": "客体"}}]
"""
            response = self.llm(prompt)
            import json
            relations = json.loads(response)
            return relations
        except Exception as e:
            logger.error(f"Relation extraction failed: {e}")
            return []
    
    async def classify_text(self, text: str, categories: List[str]) -> str:
        """Classify medical text into categories using LLM."""
        try:
            categories_str = ", ".join(categories)
            prompt = f"""将以下医学文本分类到这些类别之一: {categories_str}

文本: {text}

请只返回类别名称。
"""
            response = self.llm(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"Text classification failed: {e}")
            return "未知"

# Singleton instance
clinical_nlp_service = ClinicalNLPService()
