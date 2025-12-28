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
        self.metadata: Dict[str, Dict] = {} # code -> {name, category}

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
            # Expected columns: code, name, category
            self.standard_codes = df['code'].astype(str).tolist()
            self.standard_terms = df['name'].astype(str).tolist()
            
            # Store metadata
            for _, row in df.iterrows():
                self.metadata[str(row['code'])] = {
                    "name": row['name'],
                    "category": row.get('category', "Unknown")
                }

            print(f"Encoding {len(self.standard_terms)} terms...")
            self.embeddings = self.model.encode(self.standard_terms, convert_to_tensor=True)
            self.initialized = True
            print("Vector Index Initialized.")
            
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
            # Find best match
            best_score = torch.max(cosine_scores[i])
            best_idx = torch.argmax(cosine_scores[i]).item()
            
            score = best_score.item()
            
            if score >= threshold:
                code = self.standard_codes[best_idx]
                meta = self.metadata.get(code, {})
                results.append({
                    "term": term,
                    "match_found": True,
                    "code": code,
                    "standard_name": meta.get("name"),
                    "category": meta.get("category"),
                    "confidence": round(score, 4),
                    "method": "vector_search"
                })
            else:
                 results.append({
                    "term": term,
                    "match_found": False,
                    "confidence": round(score, 4),
                    "best_guess": self.standard_terms[best_idx],
                    "method": "vector_search"
                })
                
        return results

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
