from typing import List, Dict, Any, Optional
import os

# Mock import for MedCT/MedLink SDKs
try:
    from medct.client import MedCTClient
    from medlink.linker import MedLinkER
    HAS_MED_TOOLS = True
except ImportError:
    HAS_MED_TOOLS = False
    print("MedCT/MedLink SDKs not found. Using Mock Client.")
    class MedCTClient:
        def __init__(self, endpoint): pass
        def search(self, term): return []
        def get_concept(self, code): return {}
    class MedLinkER:
        def __init__(self, model_path): pass
        def link(self, text, context): return []

class TerminologyService:
    """
    Service for Medical Terminology Standardization.
    Integrates with MedCT for ontology and MedLink for entity linking.
    """

    def __init__(self):
        self.endpoint = os.getenv("MEDCT_ENDPOINT", "http://localhost:8080/fhir")
        
        if HAS_MED_TOOLS:
            self.medct = MedCTClient(endpoint=self.endpoint)
            # MedLink might load a local model or connect to a service
            self.medlink = MedLinkER(model_path=os.getenv("MEDLINK_MODEL_PATH", "./models/medlink"))
        else:
            self.medct = MedCTClient(self.endpoint)
            self.medlink = MedLinkER(None)

    async def normalize(self, terms: List[str]) -> List[Dict[str, Any]]:
        """
        Normalize raw terms to standard codes using MedCT and MedLink.
        """
        results = []
        for term in terms:
            if not HAS_MED_TOOLS:
                # Mock logic
                results.append({
                    "term": term,
                    "code": "MOCK-123",
                    "display": f"Standard {term}",
                    "system": "SNOMED-CT",
                    "confidence": 0.95
                })
                continue

            # 1. Try Entity Linking with Disambiguation (MedLink)
            # MedLink uses context to disambiguate (e.g., 'Ca' -> Calcium vs Cancer)
            # Here we provide dummy context; in real usage, pass full sentence/paragraph.
            linked_entities = self.medlink.link(term, context=term)
            
            if linked_entities:
                top_match = linked_entities[0]
                results.append({
                    "term": term,
                    "code": top_match.id,
                    "display": top_match.name,
                    "system": "SNOMED-CT", # Default to SNOMED
                    "confidence": top_match.score
                })
            else:
                # 2. Fallback to direct Search in MedCT
                candidates = self.medct.search(term)
                if candidates:
                    best = candidates[0]
                    results.append({
                        "term": term,
                        "code": best.code,
                        "display": best.display,
                        "system": best.system,
                        "confidence": 0.8  # Lower confidence for raw search
                    })
                else:
                    results.append({
                        "term": term,
                        "code": None,
                        "status": "UNKNOWN"
                    })
        return results

    async def get_related_concepts(self, code: str, relationship: str = "IS-A") -> List[Dict[str, Any]]:
        """
        Query MedCT for hierarchical or semantic relationships.
        e.g., "Find all children of 'Pneumonia'"
        """
        if not HAS_MED_TOOLS:
            return [{"code": "MOCK-CHILD", "display": "Mock Child Concept"}]
            
        # Use MedCT graph capabilities
        concept = self.medct.get_concept(code)
        if not concept:
            return []
            
        # Mocking the relationship traversal access pattern
        related = concept.get_related(relationship)
        return [{"code": r.code, "display": r.display} for r in related]

# Singleton
terminology_service = TerminologyService()
