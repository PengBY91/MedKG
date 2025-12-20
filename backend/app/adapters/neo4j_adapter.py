from typing import List, Dict, Any
import asyncio

class Neo4jAdapter:
    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "password"):
        self.uri = uri
        self.user = user
        self.password = password
        # In production, use neo4j.AsyncGraphDatabase
        from app.services.knowledge_store_service import knowledge_store
        self.store = knowledge_store
        self._mock_data = self._init_mock_data()
    
    def _init_mock_data(self):
        """Initialize graph data, merging persistent store with basic patient structure."""
        return {
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
            "rules": self.store.get_all_rules(),
            "terminology_hierarchy": {t["term"]: t for t in self.store.get_all_terms()},
            "policy_hierarchy": []
        }

    async def search_policies(self, query: str) -> List[Dict[str, Any]]:
        """Search policy rules in Knowledge Store."""
        results = []
        rules = self.store.get_all_rules()
        query_lower = query.lower()
        for rule in rules:
            subject = (rule.get("subject") or "").lower()
            explanation = (rule.get("explanation") or "").lower()
            if subject in query_lower or query_lower in subject or query_lower in explanation:
                results.append({
                    "id": rule.get("id"),
                    "name": f"{rule.get('subject') or '未知'} {rule.get('rule_type') or ''} 规则",
                    "reference": "知识库持久化条目",
                    "parent_doc": "规则库",
                    "content": rule.get("explanation")
                })
        return results

    async def get_policy_context(self, rule_id: str) -> Dict[str, Any]:
        """Retrieve contextual information for a rule (parent, siblings)."""
        rule = next((r for r in self._mock_data["rules"] if r["id"] == rule_id), None)
        if not rule:
            return {}
        
        parent = next((p for p in self._mock_data["policy_hierarchy"] if rule_id in p["children"]), {})
        siblings = [r for r in self._mock_data["rules"] if r["id"] in parent.get("children", []) and r["id"] != rule_id]
        
        return {
            "rule": rule,
            "parent_doc": parent,
            "siblings": siblings
        }

    async def get_terminology_context(self, code: str) -> Dict[str, Any]:

        """Retrieve structural context for a terminology code."""
        await asyncio.sleep(0.05)
        # Mock: Return data from terminology_hierarchy
        return self._mock_data.get("terminology_hierarchy", {}).get(code, {})


    
    async def get_patient_subgraph(self, patient_id: str) -> Dict[str, Any]:
        """Retrieve patient's medical subgraph."""
        await asyncio.sleep(0.1)  # Simulate DB query
        
        # Mock: Build subgraph from mock data
        patient = next((p for p in self._mock_data["patients"] if p["id"] == patient_id), None)
        if not patient:
            return {}
        
        visits = [v for v in self._mock_data["visits"] if v["patient_id"] == patient_id]
        
        subgraph = {
            "patient": patient,
            "visits": [],
        }
        
        for visit in visits:
            diagnoses = [d for d in self._mock_data["diagnoses"] if d["visit_id"] == visit["id"]]
            treatments = [t for t in self._mock_data["treatments"] if t["visit_id"] == visit["id"]]
            
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
        
        rules = self.store.get_all_rules()
        
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
