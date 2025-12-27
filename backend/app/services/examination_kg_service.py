"""
Examination Knowledge Graph Service
Manages tree-structured examination ontology in Neo4j.
"""

from typing import List, Dict, Any, Optional
import logging
from app.core.kg import neo4j_service
import logging
# from neo4j import AsyncGraphDatabase, AsyncDriver # Removed direct dependency
import os
from dotenv import load_dotenv

# Load env immediately
load_dotenv()

logger = logging.getLogger(__name__)


class ExaminationKGService:
    """
    Service for managing examination ontology in Neo4j knowledge graph.
    
    Graph Schema:
    - BodyPartLevel1 (一级部位)
    - BodyPartLevel2 (二级部位)  
    - ExaminationMethod (检查方法)
    - Modality (检查模态)
    
    Relationships:
    - (:BodyPartLevel1)-[:HAS_SUBPART]->(:BodyPartLevel2)
    - (:BodyPartLevel2)-[:SUPPORTS_METHOD]->(:ExaminationMethod)
    - (:ExaminationMethod)-[:USES_MODALITY]->(:Modality)
    """
    
    def __init__(self):
        self.neo4j = neo4j_service
    
    async def initialize(self):
        """Initialize Neo4j connection."""
        await self.neo4j.initialize()
        # Create indexes
        await self._create_indexes()

    async def _create_indexes(self):
        """Create indexes on node properties."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS FOR (n:BodyPartLevel1) ON (n.name)",
            "CREATE INDEX IF NOT EXISTS FOR (n:BodyPartLevel2) ON (n.name)",
            "CREATE INDEX IF NOT EXISTS FOR (n:ExaminationMethod) ON (n.name)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Modality) ON (n.name)"
        ]
        
        for index_query in indexes:
            await self.neo4j.execute_query(index_query)

    async def close(self):
        """Close Neo4j connection."""
        await self.neo4j.close()
    
    # ==================== Query Methods ====================
    
    async def get_all_level1_parts(self) -> List[str]:
        """Get all level 1 body parts."""
    async def get_all_level1_parts(self) -> List[str]:
        """Get all level 1 body parts."""
        query = "MATCH (n:BodyPartLevel1) RETURN n.name as name ORDER BY name"
        records = await self.neo4j.execute_query(query)
        return [record["name"] for record in records]
    
    async def get_level2_parts(self, level1: Optional[str] = None) -> List[str]:
        """
        Get level 2 body parts.
        
        Args:
            level1: Optional filter by level 1 part
            
        Returns:
            List of level 2 part names
        """
    async def get_level2_parts(self, level1: Optional[str] = None) -> List[str]:
        """Get level 2 body parts."""
        if level1:
            query = """
            MATCH (l1:BodyPartLevel1 {name: $level1})
                  -[:HAS_SUBPART]->(l2:BodyPartLevel2)
            RETURN l2.name as name
            ORDER BY name
            """
            params = {"level1": level1}
        else:
            query = "MATCH (n:BodyPartLevel2) RETURN n.name as name ORDER BY name"
            params = {}
        
        records = await self.neo4j.execute_query(query, params)
        return [record["name"] for record in records]
    
    async def get_methods_for_part(self, level2: str) -> List[str]:
        """
        Get examination methods supported by a level 2 body part.
        
        Args:
            level2: Level 2 body part name
            
        Returns:
            List of method names
        """
    async def get_methods_for_part(self, level2: str) -> List[str]:
        """Get examination methods supported by a level 2 body part."""
        query = """
        MATCH (l2:BodyPartLevel2 {name: $level2})
              -[:SUPPORTS_METHOD]->(m:ExaminationMethod)
        RETURN m.name as name
        ORDER BY name
        """
        records = await self.neo4j.execute_query(query, {"level2": level2})
        return [record["name"] for record in records]
    
    async def get_all_methods(self) -> List[str]:
        """Get all examination methods."""
    async def get_all_methods(self) -> List[str]:
        """Get all examination methods."""
        query = "MATCH (n:ExaminationMethod) RETURN n.name as name ORDER BY name"
        records = await self.neo4j.execute_query(query)
        return [record["name"] for record in records]
    
    async def get_all_modalities(self) -> List[str]:
        """Get all modalities."""
    async def get_all_modalities(self) -> List[str]:
        """Get all modalities."""
        query = "MATCH (n:Modality) RETURN n.name as name ORDER BY name"
        records = await self.neo4j.execute_query(query)
        return [record["name"] for record in records]
    
    async def validate_path(self, level1: str, level2: str, method: str) -> bool:
        """
        Validate if a complete path exists in the graph.
        
        Args:
            level1: Level 1 body part
            level2: Level 2 body part
            method: Examination method
            
        Returns:
            True if path exists, False otherwise
        """
    async def validate_path(self, level1: str, level2: str, method: str) -> bool:
        """Validate if a complete path exists in the graph."""
        query = """
        MATCH (l1:BodyPartLevel1 {name: $level1})
              -[:HAS_SUBPART]->(l2:BodyPartLevel2 {name: $level2})
              -[:SUPPORTS_METHOD]->(m:ExaminationMethod {name: $method})
        RETURN count(*) > 0 as exists
        """
        
        records = await self.neo4j.execute_query(query, {
            "level1": level1,
            "level2": level2,
            "method": method
        })
        return records[0]["exists"] if records else False
    
    async def find_level1_by_level2(self, level2: str) -> Optional[str]:
        """
        Find level 1 body part by level 2 part.
        
        Args:
            level2: Level 2 body part name
            
        Returns:
            Level 1 body part name or None
        """
    async def find_level1_by_level2(self, level2: str) -> Optional[str]:
        """Find level 1 body part by level 2 part."""
        query = """
        MATCH (l1:BodyPartLevel1)-[:HAS_SUBPART]->
              (l2:BodyPartLevel2 {name: $level2})
        RETURN l1.name as name
        LIMIT 1
        """
        records = await self.neo4j.execute_query(query, {"level2": level2})
        return records[0]["name"] if records else None
    
    async def get_complete_tree(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Get complete tree structure.
        
        Returns:
            Nested dict: {level1: {level2: [methods]}}
        """
    async def get_complete_tree(self) -> Dict[str, Dict[str, List[str]]]:
        """Get complete tree structure."""
        query = """
        MATCH (l1:BodyPartLevel1)-[:HAS_SUBPART]->(l2:BodyPartLevel2)
              -[:SUPPORTS_METHOD]->(m:ExaminationMethod)
        WITH l1.name as level1, l2.name as level2, collect(DISTINCT m.name) as methods
        RETURN level1, level2, methods
        ORDER BY level1, level2
        """
        
        records = await self.neo4j.execute_query(query)
        
        tree = {}
        for record in records:
            level1 = record["level1"]
            level2 = record["level2"]
            methods = record["methods"]
            
            if level1 not in tree:
                tree[level1] = {}
            tree[level1][level2] = methods
        
        return tree
    
    async def get_sample_paths(self, limit: int = 5) -> List[Dict[str, str]]:
        """
        Get sample valid paths for Few-shot examples.
        
        Args:
            limit: Number of samples to return
            
        Returns:
            List of dicts with level1, level2, method
        """
    async def get_sample_paths(self, limit: int = 5) -> List[Dict[str, str]]:
        """Get sample valid paths for Few-shot examples."""
        query = """
        MATCH (l1:BodyPartLevel1)-[:HAS_SUBPART]->(l2:BodyPartLevel2)
              -[:SUPPORTS_METHOD]->(m:ExaminationMethod)
        RETURN l1.name as level1, l2.name as level2, m.name as method
        LIMIT $limit
        """
        return await self.neo4j.execute_query(query, {"limit": limit})
    
    async def get_graph_stats(self) -> Dict[str, int]:
        """
        Get graph statistics.
        
        Returns:
            Dict with counts of nodes and relationships
        """
    async def get_graph_stats(self) -> Dict[str, int]:
        """Get graph statistics."""
        query = """
        MATCH (l1:BodyPartLevel1)
        WITH count(l1) as level1_count
        MATCH (l2:BodyPartLevel2)
        WITH level1_count, count(l2) as level2_count
        MATCH (m:ExaminationMethod)
        WITH level1_count, level2_count, count(m) as method_count
        MATCH (mod:Modality)
        WITH level1_count, level2_count, method_count, count(mod) as modality_count
        MATCH (:BodyPartLevel1)-[:HAS_SUBPART]->(:BodyPartLevel2)
              -[:SUPPORTS_METHOD]->(:ExaminationMethod)
        RETURN level1_count, level2_count, method_count, modality_count, 
               count(*) as total_paths
        """
        
        records = await self.neo4j.execute_query(query)
        if records:
            record = records[0]
            return {
                "level1_count": record["level1_count"],
                "level2_count": record["level2_count"],
                "method_count": record["method_count"],
                "modality_count": record["modality_count"],
                "total_paths": record["total_paths"]
            }
        
        return {
            "level1_count": 0, "level2_count": 0, "method_count": 0,
            "modality_count": 0, "total_paths": 0
        }

    async def validate_standardization_path(self, level1: str, level2: str, method: str) -> bool:
        """
        Validate if a standardization path exists in the KG.
        
        Args:
            level1: Level 1 Body Part
            level2: Level 2 Body Part
            method: Examination Method
            
        Returns:
            True if path exists, False otherwise
        """
    async def validate_standardization_path(self, level1: str, level2: str, method: str) -> bool:
        """Validate if a standardization path exists in the KG."""
        query = """
        MATCH (l1:BodyPartLevel1 {name: $level1})
              -[:HAS_SUBPART]->(l2:BodyPartLevel2 {name: $level2})
              -[:SUPPORTS_METHOD]->(m:ExaminationMethod {name: $method})
        RETURN count(*) > 0 as exists
        """
        
        records = await self.neo4j.execute_query(query, {
            "level1": level1, "level2": level2, "method": method
        })
        return records[0]["exists"] if records else False

    async def get_methods_by_modality(self, modality: str) -> List[str]:
        """
        Get all examination methods supported by a specific modality.
        
        Args:
            modality: Modality name (e.g. "DR", "CT")
            
        Returns:
            List of method names
        """
    async def get_methods_by_modality(self, modality: str) -> List[str]:
        """Get all examination methods supported by a specific modality."""
        query = """
        MATCH (m:ExaminationMethod)-[:USES_MODALITY]->(mod:Modality {name: $modality})
        RETURN m.name
        ORDER BY m.name
        """
        
        records = await self.neo4j.execute_query(query, {"modality": modality})
        return [record["m.name"] for record in records]
        
# Singleton instance
examination_kg_service = ExaminationKGService()
