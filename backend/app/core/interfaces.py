from abc import ABC, abstractmethod
from typing import List, Dict, Any

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, schema: Dict[str, Any] = None) -> str:
        """
        Generate text from a prompt. 
        If schema is provided, the output should adhere to it (JSON mode).
        """
        pass

class VectorStoreAdapter(ABC):
    @abstractmethod
    async def search(self, query_text: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search for similar items. Returns list of dicts with 'text', 'score', 'metadata'.
        """
        pass
        
    @abstractmethod
    async def add_texts(self, texts: List[str], metadata: List[Dict[str, Any]]):
        """
        Embed and add texts to the store.
        """
        pass
