from typing import List, Dict, Any
import logging
import math

logger = logging.getLogger(__name__)

class KGRankService:
    """
    Search Service implementing the KG-Rank Pipeline.
    Steps:
    1. Retrieval (Graph + Vector)
    2. Ranking (UmlsBERT or similar)
    3. Re-ranking (MMR for diversity)
    4. Factuality Scorer
    """

    def __init__(self, graph_service=None, vector_store=None):
        self.graph = graph_service
        self.vector_store = vector_store

    async def search(self, query: str, top_k: int = 10, **kwargs) -> List[Dict[str, Any]]:
        # Handle search_type if provided
        search_type = kwargs.get("search_type", "hybrid")
        logger.info(f"KGRankService.search initiated with query='{query}', type='{search_type}'")
        # 1. Retrieval Phase
        # Mock retrieval of candidates from Graph & Vector DB
        candidates = self._retrieve_candidates(query)

        # 2. Ranking Phase
        # Initial scoring based on similarity
        ranked_candidates = self._rank_candidates(query, candidates)

        # 3. Re-ranking Phase (MMR)
        final_results = self._mmr_rerank(query, ranked_candidates, limit=top_k)
        
        # 4. Factuality Check (Optional annotation)
        for res in final_results:
            res["factuality_score"] = self._calculate_factuality(res, query)

        return final_results

    def _retrieve_candidates(self, query: str) -> List[Dict]:
        """Mock Retrieval."""
        return [
            {"id": "1", "text": "Metformin treats Diabetes.", "embedding": [0.1, 0.2]},
            {"id": "2", "text": "Diabetes is a chronic disease.", "embedding": [0.1, 0.21]},
            {"id": "3", "text": "Aspirin is for pain.", "embedding": [0.9, 0.1]},
            # Redundant candidate to test MMR
            {"id": "4", "text": "Metformin is used for Diabetes Type 2.", "embedding": [0.1, 0.205]},
        ]

    def _rank_candidates(self, query: str, candidates: List[Dict]) -> List[Dict]:
        """Simple Cosine Sim ranking."""
        # For mock, we assign dummy scores
        for c in candidates:
            c["score"] = 0.9 if "Diabetes" in c["text"] else 0.5
        
        return sorted(candidates, key=lambda x: x["score"], reverse=True)

    def _mmr_rerank(self, query: str, candidates: List[Dict], limit: int, lambda_param: float = 0.7) -> List[Dict]:
        """
        Maximal Marginal Relevance (MMR)
        Score = lambda * Sim(query, doc) - (1-lambda) * Max_Sim(doc, selected_docs)
        """
        selected = []
        pool = candidates[:]
        
        while len(selected) < limit and pool:
            best_doc = None
            best_mmr = -float("inf")
            
            for doc in pool:
                # Sim(query, doc) -> already in doc['score']
                relevance = doc["score"]
                
                # Max_Sim(doc, selected)
                if not selected:
                    diversity_penalty = 0
                else:
                    # Mock similarity betwen docs (using simple check or embedding dot product)
                    diversity_penalty = max([self._sim(doc, s) for s in selected])
                
                mmr_score = lambda_param * relevance - (1 - lambda_param) * diversity_penalty
                
                if mmr_score > best_mmr:
                    best_mmr = mmr_score
                    best_doc = doc
            
            if best_doc:
                selected.append(best_doc)
                pool.remove(best_doc)
                
        return selected

    def _sim(self, doc_a, doc_b):
        """Mock Similarity between two docs."""
        # In real impl, compute cosine sim of embeddings
        # Here: return high sim if text overlaps significantly
        set_a = set(doc_a["text"].split())
        set_b = set(doc_b["text"].split())
        intersection = len(set_a.intersection(set_b))
        union = len(set_a.union(set_b))
        return intersection / union if union > 0 else 0

    def _calculate_factuality(self, doc: Dict, query: str) -> float:
        """Score if the document contradicts known facts (Mock)."""
        return 0.95

# Singleton
search_service = KGRankService()
