from typing import List, Dict, Any
import logging
from app.services.kag_solver_service import kag_solver
from app.core.config import settings

logger = logging.getLogger(__name__)

class SearchService:
    """
    Search Service using KAG Solver for hybrid retrieval.
    Replaces mock retrieval with real KAG hybrid search (vector + graph).
    """
    
    def __init__(self):
        """Initialize with KAG Solver."""
        self.solver = kag_solver
        logger.info("SearchService initialized with KAG Solver")
    
    async def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search using KAG hybrid retrieval.
        
        Args:
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of search results with scores
        """
        try:
            # Use KAG Solver for retrieval
            result = await self.solver.solve_query(
                query=query,
                context={"top_k": top_k}
            )
            
            if result['status'] == 'success':
                # Extract sources from solver result
                sources = result.get('sources', [])
                
                # Format as search results
                search_results = []
                for idx, source in enumerate(sources[:top_k]):
                    search_results.append({
                        "id": source.get("id", f"result_{idx}"),
                        "content": source.get("content", ""),
                        "score": source.get("score", 1.0 - (idx * 0.1)),
                        "metadata": source.get("metadata", {}),
                        "type": source.get("type", "document")
                    })
                
                logger.info(f"Search completed: {len(search_results)} results")
                return search_results
            else:
                logger.error(f"Search failed: {result.get('message')}")
                return []
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    async def semantic_search(self, query: str, filters: Dict[str, Any] = None, top_k: int = 10) -> List[Dict]:
        """
        Semantic search with optional filters.
        """
        try:
            context = {"top_k": top_k}
            if filters:
                context.update(filters)
            
            result = await self.solver.solve_query(query=query, context=context)
            
            if result['status'] == 'success':
                sources = result.get('sources', [])
                return sources[:top_k]
            else:
                return []
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []
    
    async def graph_search(self, entity_id: str, relation_type: str = None, depth: int = 2) -> Dict[str, Any]:
        """
        Graph-based search starting from an entity.
        Uses KAG's graph retrieval capabilities.
        """
        try:
            # Construct graph query
            query = f"查找与 {entity_id} 相关的信息"
            if relation_type:
                query += f",关系类型: {relation_type}"
            
            result = await self.solver.solve_query(
                query=query,
                context={"entity_id": entity_id, "depth": depth}
            )
            
            if result['status'] == 'success':
                return {
                    "entity": entity_id,
                    "related": result.get('sources', []),
                    "reasoning": result.get('reasoning_trace', [])
                }
            else:
                return {"entity": entity_id, "related": [], "reasoning": []}
                
        except Exception as e:
            logger.error(f"Graph search error: {e}")
            return {"entity": entity_id, "related": [], "error": str(e)}

# Singleton instance
search_service = SearchService()
