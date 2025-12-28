from typing import List, Dict, Any, Optional, Tuple
import os
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import torch

class VectorTerminologyService:
    """
    Terminology Service using Vector Search for fuzzy matching.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.standard_terms: List[str] = []
        self.standard_codes: List[str] = []
        self.embeddings = None
        self.initialized = False
        self.metadata: Dict[str, Dict] = {} # code -> {name, category, parent_code}
        self.search_index_terms: List[str] = [] # name or synonym
        self.search_index_codes: List[str] = [] # maps 1-to-1 with search_index_terms
        self.llm = None

    def initialize(self, resource_path: str):
        """
        Load standard terms from CSV and build index.
        """
        print(f"Initializing VectorTerminologyService with resources from {resource_path}")
        try:
            self.model = SentenceTransformer(self.model_name)
        except Exception as e:
            print(f"Failed to load SentenceTransformer: {e}")
            return

        try:
            df = pd.read_csv(resource_path)
            self.search_index_terms = []
            self.search_index_codes = []
            
            # Store metadata and expand synonyms for search index
            for _, row in df.iterrows():
                code = str(row['code'])
                name = str(row['name'])
                synonyms = str(row.get('synonyms', ""))
                
                self.metadata[code] = {
                    "name": name,
                    "category": row.get('category', "Unknown"),
                    "parent_code": row.get('parent_code', "")
                }
                
                # Main name in index
                self.search_index_terms.append(name)
                self.search_index_codes.append(code)
                
                # Synonyms in index
                if synonyms and synonyms != "nan":
                    for syn in synonyms.split(","):
                        syn = syn.strip()
                        if syn:
                            self.search_index_terms.append(syn)
                            self.search_index_codes.append(code)

            print(f"Encoding {len(self.search_index_terms)} searchable terms (including synonyms)...")
            self.embeddings = self.model.encode(self.search_index_terms, convert_to_tensor=True)
            self.initialized = True
            
            # Setup optional LLM for disambiguation
            from app.adapters.mock_adapters import MockLLMProvider
            self.llm = MockLLMProvider() 
            
            print("Vector Index Initialized with Synonyms.")

            
        except Exception as e:
            print(f"Error loading resources: {e}")

    async def normalize(self, terms: List[str], threshold: float = 0.6) -> List[Dict[str, Any]]:
        """
        Normalize terms using vector similarity.
        """
        if not self.initialized:
            return [{"term": t, "status": "SERVICE_NOT_READY"} for t in terms]

        results = []
        
        # Batch encode input terms
        input_embeddings = self.model.encode(terms, convert_to_tensor=True)

        # Compute cosine similarities
        # Output is [len(terms), len(standard_terms)]
        cosine_scores = util.cos_sim(input_embeddings, self.embeddings)

        for i, term in enumerate(terms):
            # Get top 3 candidates
            top_scores, top_indices = torch.topk(cosine_scores[i], k=min(3, len(self.search_index_terms)))
            best_score = top_scores[0].item()
            best_idx = top_indices[0].item()
            
            if best_score >= threshold:
                code = self.search_index_codes[best_idx]
                meta = self.metadata.get(code, {})
                results.append({
                    "term": term,
                    "match_found": True,
                    "code": code,
                    "standard_name": meta.get("name"),
                    "category": meta.get("category"),
                    "parent_code": meta.get("parent_code"),
                    "matched_alias": self.search_index_terms[best_idx],
                    "confidence": round(best_score, 4),
                    "method": "vector_search"
                })
            elif best_score >= 0.35 and self.llm:
                # LLM-Assisted Disambiguation
                candidates = []
                for idx_tensor in top_indices:
                    idx = idx_tensor.item()
                    candidates.append({
                        "code": self.search_index_codes[idx],
                        "name": self.search_index_terms[idx]
                    })
                
                llm_code = await self._llm_disambiguate(term, candidates)
                if llm_code:
                     meta = self.metadata.get(llm_code, {})
                     results.append({
                        "term": term,
                        "match_found": True,
                        "code": llm_code,
                        "standard_name": meta.get("name"),
                        "confidence": 0.9, # Boost confidence if LLM confirms
                        "method": "llm_disambiguation"
                    })
                else:
                    results.append({
                        "term": term,
                        "match_found": False,
                        "confidence": round(best_score, 4),
                        "best_guess": self.search_index_terms[best_idx],
                        "method": "vector_search"
                    })
            else:
                 results.append({
                    "term": term,
                    "match_found": False,
                    "confidence": round(best_score, 4),
                    "best_guess": self.search_index_terms[best_idx],
                    "method": "vector_search"
                })
                
        return results

    async def _llm_disambiguate(self, term: str, candidates: List[Dict]) -> Optional[str]:
        """Ask LLM to choose the best medical code from candidates."""
        candidate_str = "\n".join([f"- {c['code']}: {c['name']}" for c in candidates])
        prompt = f"""
        Which of the following medical standardized terms best matches the clinical description: "{term}"?
        
        Candidates:
        {candidate_str}
        
        If none are a good match, respond with 'NONE'.
        Otherwise, respond ONLY with the code (e.g., 'I21.9').
        """
        response = await self.llm.generate(prompt)
        response = response.strip()
        if response == "NONE":
            return None
        # Basic validation: check if it's one of the candidate codes
        candidate_codes = [c['code'] for c in candidates]
        if response in candidate_codes:
            return response
        return None


    def add_term(self, code: str, name: str, category: str = "Custom"):
        """
        Dynamic addition of terms (re-indexing required or naive append).
        For MVP, we just append and re-encode single item (inefficient but works).
        """
        if not self.initialized:
            return

        self.standard_codes.append(code)
        self.standard_terms.append(name)
        self.metadata[code] = {"name": name, "category": category}
        
        new_emb = self.model.encode(name, convert_to_tensor=True)
        self.embeddings = torch.cat((self.embeddings, new_emb.unsqueeze(0)), 0)

# Singleton Instance (Lazy init)
vector_terminology_service = VectorTerminologyService()
