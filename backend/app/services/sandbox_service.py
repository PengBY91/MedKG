from typing import Dict, Any, List
from app.adapters.neo4j_adapter import Neo4jAdapter
import asyncio

class SandboxRunner:
    """
    Run rules in an isolated sandbox environment against test data.
    """
    def __init__(self, graph_db: Neo4jAdapter):
        self.graph_db = graph_db
    
    async def run_test(self, shacl_content: str, test_query: str = "last_month_patients") -> Dict[str, Any]:
        """
        Run a SHACL rule against test dataset.
        
        Args:
            shacl_content: The SHACL rule to test
            test_query: Query to select test dataset (e.g., "last_month_patients")
        
        Returns:
            Validation report with metrics
        """
        # Step 1: Load test data
        test_data = await self._load_test_data(test_query)
        
        # Step 2: Apply SHACL validation (mock)
        violations = await self._validate_with_shacl(test_data, shacl_content)
        
        # Step 3: Calculate metrics
        metrics = self._calculate_metrics(test_data, violations)
        
        return {
            "status": "completed",
            "test_dataset": test_query,
            "total_cases": len(test_data),
            "violations_found": len(violations),
            "rejection_rate": metrics["rejection_rate"],
            "delta_from_baseline": metrics.get("delta", 0),
            "violations": violations[:5]  # Sample violations
        }
    
    async def _load_test_data(self, query: str) -> List[Dict[str, Any]]:
        """Load test dataset from graph."""
        await asyncio.sleep(0.1)
        # Mock: Return sample patient data
        return [
            {"patient_id": "P001", "treatment_cost": 450},
            {"patient_id": "P002", "treatment_cost": 380},
            {"patient_id": "P003", "treatment_cost": 420},
        ]
    
    async def _validate_with_shacl(self, data: List[Dict], shacl: str) -> List[Dict[str, Any]]:
        """Apply SHACL validation."""
        await asyncio.sleep(0.2)
        # Mock: Simulate violations
        violations = []
        for item in data:
            if item["treatment_cost"] > 400:
                violations.append({
                    "patient_id": item["patient_id"],
                    "violation": "Cost exceeds limit",
                    "actual": item["treatment_cost"],
                    "expected": 400
                })
        return violations
    
    def _calculate_metrics(self, data: List[Dict], violations: List[Dict]) -> Dict[str, float]:
        """Calculate validation metrics."""
        total = len(data)
        rejected = len(violations)
        rejection_rate = (rejected / total * 100) if total > 0 else 0
        
        # Mock baseline comparison
        baseline_rate = 25.0  # Historical rejection rate
        delta = rejection_rate - baseline_rate
        
        return {
            "rejection_rate": round(rejection_rate, 2),
            "delta": round(delta, 2)
        }
