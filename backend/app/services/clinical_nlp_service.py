from typing import List, Dict, Any, Optional
import json
import logging
from app.core.interfaces import LLMProvider
from app.services.vector_terminology_service import vector_terminology_service

class ClinicalNLPService:
    """Service for Clinical Natural Language Processing (NER & Structuring)."""
    
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def extract_and_normalize(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract medical entities from unstructured text and auto-normalize them.
        """
        # Step 1: NER via LLM
        entities = await self._extract_entities(text)
        
        # Step 2: Normalize each extracted term
        results = []
        for entity in entities:
            term_name = entity.get("name")
            entity_type = entity.get("type")
            
            # Use terminology service to find standard code
            norm_results = await vector_terminology_service.normalize([term_name], threshold=0.5)
            
            match = norm_results[0] if norm_results else {}
            
            results.append({
                "original_term": term_name,
                "entity_type": entity_type,
                "context": entity.get("context", ""),
                "standard_match": match if match.get("match_found") else None,
                "best_guess": match.get("best_guess") if not match.get("match_found") else None,
                "confidence": match.get("confidence", 0)
            })
            
        return results

    async def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Use LLM to extract medical entities in JSON format."""
        prompt = f"""
        Extract medical entities from the following clinical text in Chinese.
        Categorize them into: 'Symptom' (症状), 'Disease' (疾病), 'BodyPart' (身体部位), 'Medication' (药物), 'Procedure' (手术/操作).
        
        Text: "{text}"
        
        Respond ONLY with a JSON list of objects:
        [{{"name": "entity name", "type": "category", "context": "brief surrounding text"}}]
        """
        
        try:
            response = await self.llm.generate(prompt)
            # Basic JSON extraction logic
            start_idx = response.find("[")
            end_idx = response.rfind("]") + 1
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            return []
        except Exception as e:
            logging.error(f"NLP Extraction Error: {e}")
            return []

# Singleton instance with Mock LLM for demo
from app.adapters.mock_adapters import MockLLMProvider
clinical_nlp_service = ClinicalNLPService(MockLLMProvider())
