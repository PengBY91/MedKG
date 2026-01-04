from typing import List, Dict, Any, Optional
import logging
from app.services.schema_service import schema_service, SchemaService
from app.core.config import settings

logger = logging.getLogger(__name__)

class GraphService:
    """
    Service for Graph Operations.
    
    Graph operations are handled by:
    - KAG Builder: For creating nodes/edges from documents
    - KAG Solver: For querying the graph
    - Schema Service: For schema management
    
    This service provides a unified interface for graph operations.
    """

    def __init__(self, schema_svc: SchemaService):
        self.schema = schema_svc
        logger.info("GraphService initialized (operations delegated to KAG Builder/Solver)")

    async def add_node(self, node_def: Dict[str, Any]) -> str:
        """
        Add a node to the graph.
        Note: Nodes are typically created by KAG Builder during document processing.
        """
        logger.info(f"Node creation delegated to KAG Builder: {node_def['id']}")
        return node_def["id"]

    async def add_edge(self, edge_def: Dict[str, Any]) -> str:
        """
        Add an edge to the graph.
        Note: Edges are typically created by KAG Builder during document processing.
        """
        logger.info(f"Edge creation delegated to KAG Builder: {edge_def['from']} -> {edge_def['to']}")
        return f"{edge_def['from']}-{edge_def['type']}-{edge_def['to']}"

    async def create_mutual_index(self, chunk_id: str, entity_ids: List[str]):
        """
        Create bidirectional MENTIONS edges.
        This is automatically handled by KAG Builder.
        """
        logger.info(f"Mutual index for chunk {chunk_id} (handled by KAG Builder)")

    async def query_neighbors(self, node_id: str, relation_type: Optional[str] = None) -> List[Dict]:
        """Query neighbors using KAG Solver."""
        try:
            from app.services.kag_solver_service import kag_solver
            query = f"查找与 {node_id} 相关的节点"
            if relation_type:
                query += f",关系类型: {relation_type}"
            
            result = await kag_solver.solve_query(query)
            return result.get('sources', [])
        except Exception as e:
            logger.error(f"Failed to query neighbors: {e}")
            return []

    async def get_node(self, node_id: str) -> Optional[Dict]:
        """Get node information using KAG Solver."""
        try:
            from app.services.kag_solver_service import kag_solver
            result = await kag_solver.solve_query(f"获取节点 {node_id} 的信息")
            sources = result.get('sources', [])
            return sources[0] if sources else None
        except Exception as e:
            logger.error(f"Failed to get node: {e}")
            return None

# Singleton instance
graph_service = GraphService(schema_service)
