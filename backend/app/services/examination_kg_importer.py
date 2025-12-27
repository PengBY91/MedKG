"""
Examination Knowledge Graph Data Importer
Imports tree-structured examination ontology data into Neo4j.
"""

from typing import List, Dict, Any
import pandas as pd
import logging
from neo4j import AsyncGraphDatabase
import os

logger = logging.getLogger(__name__)


class ExaminationKGImporter:
    """
    Importer for examination ontology data.
    
    Expected CSV format:
    一级部位,二级部位,检查方法,检查模态
    上肢,双腕关节,正位,DR
    上肢,双腕关节,侧位,DR
    ...
    """
    
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
    
    async def import_from_csv(self, file_path: str, clear_existing: bool = False) -> Dict[str, Any]:
        """
        Import examination ontology from CSV file.
        
        Args:
            file_path: Path to CSV file
            clear_existing: Whether to clear existing data first
            
        Returns:
            Import statistics
        """
        try:
            # Read CSV
            df = pd.read_csv(file_path)
            
            # Validate columns
            required_cols = ["一级部位", "二级部位", "检查方法", "检查模态"]
            if not all(col in df.columns for col in required_cols):
                raise ValueError(f"CSV must contain columns: {required_cols}")
            
            logger.info(f"Loaded {len(df)} records from {file_path}")
            
            # Connect to Neo4j
            driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            
            try:
                await driver.verify_connectivity()
                
                # Clear existing data if requested
                if clear_existing:
                    await self._clear_graph(driver)
                
                # Import data
                stats = await self._import_data(driver, df)
                
                logger.info(f"Import completed: {stats}")
                return stats
                
            finally:
                await driver.close()
                
        except Exception as e:
            logger.error(f"Import failed: {str(e)}")
            raise
    
    async def _clear_graph(self, driver):
        """Clear all examination ontology data."""
        logger.warning("Clearing existing examination ontology data...")
        
        query = """
        MATCH (n)
        WHERE n:BodyPartLevel1 OR n:BodyPartLevel2 OR 
              n:ExaminationMethod OR n:Modality
        DETACH DELETE n
        """
        
        async with driver.session() as session:
            await session.run(query)
        
        logger.info("Existing data cleared")
    
    async def _import_data(self, driver, df: pd.DataFrame) -> Dict[str, Any]:
        """Import data into Neo4j."""
        
        # Extract unique entities
        level1_parts = df["一级部位"].unique().tolist()
        level2_parts = df["二级部位"].unique().tolist()
        methods = df["检查方法"].unique().tolist()
        modalities = df["检查模态"].unique().tolist()
        
        logger.info(f"Unique entities - L1: {len(level1_parts)}, L2: {len(level2_parts)}, "
                   f"Methods: {len(methods)}, Modalities: {len(modalities)}")
        
        async with driver.session() as session:
            # Create nodes
            await self._create_level1_nodes(session, level1_parts)
            await self._create_level2_nodes(session, level2_parts)
            await self._create_method_nodes(session, methods)
            await self._create_modality_nodes(session, modalities)
            
            # Create relationships
            rel_stats = await self._create_relationships(session, df)
        
        return {
            "level1_nodes": len(level1_parts),
            "level2_nodes": len(level2_parts),
            "method_nodes": len(methods),
            "modality_nodes": len(modalities),
            **rel_stats
        }
    
    async def _create_level1_nodes(self, session, parts: List[str]):
        """Create BodyPartLevel1 nodes."""
        query = """
        UNWIND $parts as part
        MERGE (n:BodyPartLevel1 {name: part})
        SET n.code = 'BP1_' + part
        """
        await session.run(query, {"parts": parts})
        logger.info(f"Created {len(parts)} BodyPartLevel1 nodes")
    
    async def _create_level2_nodes(self, session, parts: List[str]):
        """Create BodyPartLevel2 nodes."""
        query = """
        UNWIND $parts as part
        MERGE (n:BodyPartLevel2 {name: part})
        SET n.code = 'BP2_' + part
        """
        await session.run(query, {"parts": parts})
        logger.info(f"Created {len(parts)} BodyPartLevel2 nodes")
    
    async def _create_method_nodes(self, session, methods: List[str]):
        """Create ExaminationMethod nodes."""
        query = """
        UNWIND $methods as method
        MERGE (n:ExaminationMethod {name: method})
        SET n.code = 'EM_' + method
        """
        await session.run(query, {"methods": methods})
        logger.info(f"Created {len(methods)} ExaminationMethod nodes")
    
    async def _create_modality_nodes(self, session, modalities: List[str]):
        """Create Modality nodes."""
        query = """
        UNWIND $modalities as modality
        MERGE (n:Modality {name: modality})
        SET n.code = 'MOD_' + modality
        """
        await session.run(query, {"modalities": modalities})
        logger.info(f"Created {len(modalities)} Modality nodes")
    
    async def _create_relationships(self, session, df: pd.DataFrame) -> Dict[str, int]:
        """Create relationships between nodes."""
        
        # Prepare relationship data
        level1_level2_pairs = df[["一级部位", "二级部位"]].drop_duplicates()
        level2_method_pairs = df[["二级部位", "检查方法"]].drop_duplicates()
        method_modality_pairs = df[["检查方法", "检查模态"]].drop_duplicates()
        
        # Create HAS_SUBPART relationships
        query1 = """
        UNWIND $pairs as pair
        MATCH (l1:BodyPartLevel1 {name: pair.level1})
        MATCH (l2:BodyPartLevel2 {name: pair.level2})
        MERGE (l1)-[:HAS_SUBPART]->(l2)
        """
        result1 = await session.run(query1, {
            "pairs": level1_level2_pairs.rename(columns={
                "一级部位": "level1",
                "二级部位": "level2"
            }).to_dict('records')
        })
        summary1 = await result1.consume()
        
        # Create SUPPORTS_METHOD relationships
        query2 = """
        UNWIND $pairs as pair
        MATCH (l2:BodyPartLevel2 {name: pair.level2})
        MATCH (m:ExaminationMethod {name: pair.method})
        MERGE (l2)-[:SUPPORTS_METHOD]->(m)
        """
        result2 = await session.run(query2, {
            "pairs": level2_method_pairs.rename(columns={
                "二级部位": "level2",
                "检查方法": "method"
            }).to_dict('records')
        })
        summary2 = await result2.consume()
        
        # Create USES_MODALITY relationships
        query3 = """
        UNWIND $pairs as pair
        MATCH (m:ExaminationMethod {name: pair.method})
        MATCH (mod:Modality {name: pair.modality})
        MERGE (m)-[:USES_MODALITY]->(mod)
        """
        result3 = await session.run(query3, {
            "pairs": method_modality_pairs.rename(columns={
                "检查方法": "method",
                "检查模态": "modality"
            }).to_dict('records')
        })
        summary3 = await result3.consume()
        
        has_subpart_count = summary1.counters.relationships_created
        supports_method_count = summary2.counters.relationships_created
        uses_modality_count = summary3.counters.relationships_created
        
        logger.info(f"Created relationships - HAS_SUBPART: {has_subpart_count}, "
                   f"SUPPORTS_METHOD: {supports_method_count}, "
                   f"USES_MODALITY: {uses_modality_count}")
        
        return {
            "has_subpart_rels": has_subpart_count,
            "supports_method_rels": supports_method_count,
            "uses_modality_rels": uses_modality_count
        }


# Singleton instance
examination_kg_importer = ExaminationKGImporter()
