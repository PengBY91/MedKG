from typing import List, Dict, Any, Optional
import os
from app.services.schema_service import schema_service, SchemaService

# Mock import for KAG Client
try:
    from kag.storage import GraphStorage
    HAS_KAG = True
except ImportError:
    HAS_KAG = False
    print("KAG SDK not found. Using Mock Client.")
    class GraphStorage:
        def __init__(self, *args, **kwargs): pass

class GraphService:
    """
    Service for OpenSPG/KAG Graph Storage.
    Responsibilities:
    1. Delegate Graph Storage to KAG/OpenSPG Storage.
    2. Implement Mutual Indexing via Storage APIs.
    (Reasoning logic moved to KAGSolverService)
    """

    def __init__(self, schema_svc: SchemaService):
        self.schema = schema_svc
        
        if HAS_KAG:
            # Optimization: Load storage config from environment
            self.graph_store = GraphStorage(
                endpoint=os.getenv("GRAPH_ENDPOINT", "bolt://localhost:7687"),
                user=os.getenv("GRAPH_USER", "neo4j"),
                password=os.getenv("GRAPH_PASSWORD", "password")
            )
        else:
            self.graph_store = None

    async def add_node(self, node_def: Dict[str, Any]) -> str:
        """Add a node via KAG/OpenSPG Storage."""
        if not HAS_KAG:
            return "mock_node_id"
            
        try:
            self.graph_store.upsert_vertex(
                label=node_def["type"],
                properties=node_def.get("properties", {}),
                vertex_id=node_def["id"]
            )
            return node_def["id"]
        except Exception as e:
            print(f"Graph Write Error: {e}")
            raise e

    async def add_edge(self, edge_def: Dict[str, Any]) -> str:
        """Add an edge."""
        if not HAS_KAG: return "ok"

        try:
            self.graph_store.upsert_edge(
                src_id=edge_def["src_id"],
                dst_id=edge_def["dst_id"],
                label=edge_def["type"],
                properties=edge_def.get("properties", {})
            )
            return "ok"
        except Exception as e:
             raise e

    async def index_text_chunk_link(self, chunk_id: str, related_node_ids: List[str]):
        """Mutual Indexing: Link Document Chunk <-> Knowledge Node."""
        if not HAS_KAG: return
            
        for node_id in related_node_ids:
            # Upsert MENTIONS edge
            self.graph_store.upsert_edge(
                src_id=chunk_id,
                dst_id=node_id,
                label="MENTIONS",
                properties={}
            )

# Singleton
graph_service = GraphService(schema_service)
