from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.core.kg import neo4j_service

router = APIRouter()

class SearchRequest(BaseModel):
    database: str = "neo4j"
    label: Optional[str] = None
    query: Optional[str] = None # Text to search in string properties
    limit: int = 50

class NodeExpandRequest(BaseModel):
    database: str = "neo4j"
    node_id: int # Neo4j ID

from app.core.config import settings

@router.get("/databases")
async def get_databases():
    dbs = await neo4j_service.list_databases()
    return {"success": True, "databases": dbs}

@router.get("/labels")
async def get_labels(database: str = "neo4j"):
    """Get all labels in the database."""
    query = "CALL db.labels()"
    results = await neo4j_service.execute_query(query, database=database)
    labels = [r["label"] for r in results]
    return {"success": True, "labels": labels}

@router.post("/search")
async def search_graph(req: SearchRequest):
    """
    Search nodes. 
    """
    params = {"limit": req.limit}
    
    # Base match
    if req.label:
        cypher = f"MATCH (n:`{req.label}`) "
    else:
        cypher = "MATCH (n) "
        
    # Filter
    if req.query:
        cypher += "WHERE any(key in keys(n) WHERE toString(n[key]) CONTAINS $q) "
        params["q"] = req.query
    
    # Return info for graph (ID, Labels, Props)
    # Explicitly return labels(n) because result.data() converts Node to dict and loses labels
    # Return info for graph (ID, Labels, Props)
    cypher += "RETURN n, id(n) as id, labels(n) as labels LIMIT $limit"
    
    try:
        # 1. Get Nodes
        results = await neo4j_service.execute_query(cypher, params, database=req.database)
        
        nodes = []
        node_ids = []
        for r in results:
            n = r['n']
            nid = r['id']
            nodes.append({
                "id": nid, 
                "labels": r['labels'], 
                "properties": dict(n)
            })
            node_ids.append(nid)
            
        # 2. Get Edges between these nodes (Induced Subgraph)
        links = []
        if node_ids:
            # Cypher to find all rels where both start and end are in our node list
            # Note: id(n) is integer.
            rel_query = """
            MATCH (n)-[r]->(m)
            WHERE id(n) IN $ids AND id(m) IN $ids
            RETURN id(n) as source, id(m) as target, type(r) as type, r
            """
            rel_params = {"ids": node_ids}
            rel_results = await neo4j_service.execute_query(rel_query, rel_params, database=req.database)
            
            for rr in rel_results:
                 r_props = rr['r']
                 if not isinstance(r_props, dict): r_props = {}
                 links.append({
                     "source": rr['source'],
                     "target": rr['target'],
                     "type": rr['type'],
                     "properties": dict(r_props)
                 })

        return {"success": True, "nodes": nodes, "links": links}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@router.post("/expand")
async def expand_node(req: NodeExpandRequest):
    """
    Get 1-hop relationships for a node.
    """
    try:
        query = """
        MATCH (n)-[r]-(m)
        WHERE id(n) = $node_id
        RETURN n, r, m, id(n) as source_id, id(m) as target_id, type(r) as type, labels(n) as source_labels, labels(m) as target_labels
        LIMIT 50
        """
        params = {"node_id": req.node_id}
        
        results = await neo4j_service.execute_query(query, params, database=req.database)
        
        nodes = []
        links = []
        seen_nodes = set()
        
        for row in results:
            # Process Source (n)
            if row['source_id'] not in seen_nodes:
                n = row['n']
                nodes.append({
                    "id": row['source_id'],
                    "labels": row['source_labels'],
                    "properties": dict(n)
                })
                seen_nodes.add(row['source_id'])
                
            # Process Target (m)
            if row['target_id'] not in seen_nodes:
                m = row['m']
                nodes.append({
                    "id": row['target_id'],
                    "labels": row['target_labels'],
                    "properties": dict(m)
                })
                seen_nodes.add(row['target_id'])
                
            # Process Link
            r_props = row['r']
            if not isinstance(r_props, dict):
                 r_props = {}
            
            links.append({
                "source": row['source_id'],
                "target": row['target_id'],
                 "type": row['type'],
                 "properties": r_props
            })
            
        return {"success": True, "nodes": nodes, "links": links}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@router.get("/stats")
async def get_graph_stats(database: str = "neo4j"):
    """
    Get graph statistics (Label counts, Relationship counts).
    """
    # Get Label counts
    # This query uses internal stats which is fast
    query_labels = """
    CALL db.labels() YIELD label
    CALL {
        WITH label
        MATCH (n) WHERE label IN labels(n)
        RETURN count(n) as count
    }
    RETURN label, count
    ORDER BY count DESC
    """
    
    # Get Rel counts
    query_rels = """
    CALL db.relationshipTypes() YIELD relationshipType
    CALL {
        WITH relationshipType
        MATCH ()-[r]->() WHERE type(r) = relationshipType
        RETURN count(r) as count
    }
    RETURN relationshipType as type, count
    ORDER BY count DESC
    """
    
    try:
        labels_res = await neo4j_service.execute_query(query_labels, database=database)
        rels_res = await neo4j_service.execute_query(query_rels, database=database)
        
        return {
            "success": True, 
            "labels": [{"label": r['label'], "count": r['count']} for r in labels_res],
            "relationships": [{"type": r['type'], "count": r['count']} for r in rels_res]
        }
    except Exception as e:
        # Fallback if DB is empty or error
        return {"success": False, "error": str(e), "labels": [], "relationships": []}
