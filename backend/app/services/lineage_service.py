from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
from app.services.graph_service import graph_service

class LineageService:
    """Service for tracking and querying Data Provenance (Lineage)."""
    
    async def log_lineage(self, 
        src_id: str, 
        dst_id: str, 
        relation_type: str, 
        properties: Optional[Dict] = None
    ):
        """
        Log a lineage relationship in the graph.
        Relation types: 'CONSUME', 'PRODUCED_BY', 'DERIVED_FROM', 'VALIDATED_BY'
        """
        props = properties or {}
        props["timestamp"] = datetime.utcnow().isoformat()
        
        await graph_service.add_edge({
            "src_id": src_id,
            "dst_id": dst_id,
            "type": relation_type,
            "properties": props
        })

    async def register_asset_node(self, asset_id: str, name: str, asset_type: str):
        """Register a data asset as a node in the lineage graph."""
        await graph_service.add_node({
            "id": asset_id,
            "type": "DataAsset",
            "properties": {
                "name": name,
                "asset_type": asset_type
            }
        })

    async def get_lineage_graph(self, asset_id: str) -> Dict[str, Any]:
        """
        Fetch the lineage neighborhood for visualization.
        In a real app, this would be a Cypher query.
        """
        # For MVP, we return a mock graph structure compatible with frontend libraries
        return {
            "nodes": [
                {"id": asset_id, "label": "Target Asset", "type": "asset"},
                {"id": "doc_001", "label": "Policy.pdf", "type": "document"},
                {"id": "wf_001", "label": "Ingest Pipeline", "type": "workflow"}
            ],
            "edges": [
                {"from": "doc_001", "to": "wf_001", "label": "INPUT"},
                {"from": "wf_001", "to": asset_id, "label": "OUTPUT"}
            ]
        }

lineage_service = LineageService()
