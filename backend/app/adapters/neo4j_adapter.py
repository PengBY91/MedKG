from typing import List, Dict, Any
import asyncio
import logging

logger = logging.getLogger(__name__)

class Neo4jAdapter:
    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "password"):
        self.uri = uri
        self.user = user
        self.password = password
        # In production, use neo4j.AsyncGraphDatabase
        from app.services.knowledge_store_service import knowledge_store
        from app.adapters.mock_adapters import MockVectorStoreAdapter
        self.store = knowledge_store
        self.vector_store = MockVectorStoreAdapter()
        self._data_cache = None
    
    async def _get_data(self):
        """Lazy initialization of mock data with async store calls."""
        if self._data_cache:
            return self._data_cache
            
        data = {
            "patients": [
                {"id": "P001", "name": "张三", "age": 65, "gender": "男"}
            ],
            "visits": [
                {"id": "V001", "patient_id": "P001", "type": "Outpatient", "date": "2024-01-15"}
            ],
            "diagnoses": [
                {"id": "D001", "visit_id": "V001", "icd_code": "E11.9", "name": "2型糖尿病"}
            ],
            "treatments": [
                {"id": "T001", "visit_id": "V001", "code": "DIALYSIS", "name": "透析", "cost": 450}
            ],
            "rules": await self.store.get_all_rules(),
            "terminology_hierarchy": {t["term"]: t for t in await self.store.get_all_terms()},
            "policy_hierarchy": []
        }
        self._data_cache = data
        return data

    async def search_policies(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Enhanced multi-channel retrieval for policy rules.
        Combines: 1) Keyword matching 2) Vector similarity 3) Graph traversal
        """
        logger.info(f"Multi-channel search for: {query}")
        
        # Channel 1: Keyword-based retrieval (original logic)
        keyword_results = await self._keyword_search(query)
        
        # Channel 2: Vector similarity search
        vector_results = await self._vector_search(query, top_k=top_k)
        
        # Channel 3: Graph-based retrieval (find related rules via relationships)
        graph_results = await self._graph_search(query)
        
        # Merge and deduplicate results
        merged_results = self._merge_results(keyword_results, vector_results, graph_results, top_k)
        
        logger.info(f"Retrieved {len(merged_results)} policy rules")
        return merged_results
    
    async def _keyword_search(self, query: str) -> List[Dict[str, Any]]:
        """Original keyword-based search."""
        results = []
        rules = await self.store.get_all_rules()
        query_lower = query.lower()
        
        for rule in rules:
            subject = (rule.get("subject") or "").lower()
            explanation = (rule.get("explanation") or "").lower()
            
            # Calculate match score
            score = 0.0
            if subject in query_lower or query_lower in subject:
                score += 0.8
            if query_lower in explanation:
                score += 0.5
            
            if score > 0:
                results.append({
                    "id": rule.get("id"),
                    "name": f"{rule.get('subject') or '未知'} {rule.get('rule_type') or ''} 规则",
                    "reference": "知识库持久化条目",
                    "parent_doc": "规则库",
                    "content": rule.get("explanation"),
                    "score": score,
                    "source": "keyword",
                    "rule_type": rule.get("rule_type"),
                    "subject": rule.get("subject")
                })
        
        return sorted(results, key=lambda x: x["score"], reverse=True)
    
    async def _vector_search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Semantic vector-based search."""
        try:
            vector_results = await self.vector_store.search(query, top_k=top_k)
            rules = await self.store.get_all_rules()
            
            # Match vector results with rules
            results = []
            for vr in vector_results:
                # Try to find matching rule by subject
                for rule in rules:
                    subject = rule.get("subject", "")
                    if subject and subject in vr.get("text", ""):
                        results.append({
                            "id": rule.get("id"),
                            "name": f"{subject} {rule.get('rule_type', '')} 规则",
                            "reference": "知识库持久化条目",
                            "parent_doc": "规则库",
                            "content": rule.get("explanation"),
                            "score": vr.get("score", 0.0),
                            "source": "vector",
                            "rule_type": rule.get("rule_type"),
                            "subject": subject
                        })
                        break
            
            return results
        except Exception as e:
            logger.warning(f"Vector search failed: {e}")
            return []
    
    async def _graph_search(self, query: str) -> List[Dict[str, Any]]:
        """Graph traversal-based search (find related rules)."""
        # For now, return empty; in production, use Cypher to traverse relationships
        return []
    
    def _merge_results(self, *result_lists, top_k: int = 10) -> List[Dict[str, Any]]:
        """Merge and deduplicate results from multiple channels."""
        seen_ids = set()
        merged = []
        
        # Flatten all result lists
        all_results = []
        for results in result_lists:
            all_results.extend(results)
        
        # Sort by score
        all_results.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        
        # Deduplicate by ID
        for result in all_results:
            rule_id = result.get("id")
            if rule_id not in seen_ids:
                seen_ids.add(rule_id)
                merged.append(result)
                
            if len(merged) >= top_k:
                break
        
        return merged

    async def get_policy_context(self, rule_id: str) -> Dict[str, Any]:
        """Retrieve contextual information for a rule (parent, siblings)."""
        data = await self._get_data()
        rule = next((r for r in data["rules"] if r["id"] == rule_id), None)
        if not rule:
            return {}
        
        parent = next((p for p in data["policy_hierarchy"] if rule_id in p["children"]), {})
        siblings = [r for r in data["rules"] if r["id"] in parent.get("children", []) and r["id"] != rule_id]
        
        return {
            "rule": rule,
            "parent_doc": parent,
            "siblings": siblings
        }

    async def get_terminology_context(self, code: str) -> Dict[str, Any]:
        """Retrieve structural context for a terminology code."""
        await asyncio.sleep(0.05)
        data = await self._get_data()
        # Mock: Return data from terminology_hierarchy
        return data.get("terminology_hierarchy", {}).get(code, {})


    
    async def get_patient_subgraph(self, patient_id: str) -> Dict[str, Any]:
        """Retrieve patient's medical subgraph."""
        await asyncio.sleep(0.1)  # Simulate DB query
        data = await self._get_data()
        
        # Mock: Build subgraph from mock data
        patient = next((p for p in data["patients"] if p["id"] == patient_id), None)
        if not patient:
            return {}
        
        visits = [v for v in data["visits"] if v["patient_id"] == patient_id]
        
        subgraph = {
            "patient": patient,
            "visits": [],
        }
        
        for visit in visits:
            diagnoses = [d for d in data["diagnoses"] if d["visit_id"] == visit["id"]]
            treatments = [t for t in data["treatments"] if t["visit_id"] == visit["id"]]
            
            subgraph["visits"].append({
                "visit": visit,
                "diagnoses": diagnoses,
                "treatments": treatments
            })
        
        return subgraph
    
    async def find_violations(self, patient_id: str) -> List[Dict[str, Any]]:
        """Find rule violations for a patient using data from the local Knowledge Store."""
        await asyncio.sleep(0.1)
        
        violations = []
        subgraph = await self.get_patient_subgraph(patient_id)
        if not subgraph:
            return []

        patient_treatments = []
        for visit_data in subgraph.get("visits", []):
            patient_treatments.extend(visit_data.get("treatments", []))
        
        rules = await self.store.get_all_rules()
        
        for treatment in patient_treatments:
            for rule in rules:
                subject = rule.get("subject", "").lower()
                treatment_name = treatment.get("name", "").lower()
                
                # Check for subject match (e.g., "透析" in "血液透析")
                if subject and subject in treatment_name and rule.get("rule_type") == "limit":
                    limit = float(rule.get("object_value", 0))
                    actual = float(treatment.get("cost", 0))
                    
                    if actual > limit:
                        violations.append({
                            "treatment": treatment,
                            "rule": {
                                "id": rule.get("id"),
                                "name": f"{rule.get('subject')} 限额规则",
                                "policy_ref": "持久化规则库"
                            },
                            "violation_type": "COST_EXCEEDED",
                            "expected": limit,
                            "actual": actual,
                            "policy_reference": "规则库持久化条目"
                        })
        
        return violations

    
    async def execute_cypher(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a Cypher query (mock implementation)."""
        await asyncio.sleep(0.1)
        # In production: use driver.execute_query()
        return []
