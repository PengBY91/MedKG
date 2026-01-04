from typing import List, Dict, Any
import logging
from rdflib import Graph, Namespace
from pyshacl import validate
import os

logger = logging.getLogger(__name__)

class SandboxService:
    """
    Sandbox Service for data validation using SHACL.
    Provides real SHACL validation instead of mock.
    """
    
    def __init__(self):
        """Initialize SHACL validator."""
        self.shacl_shapes = Graph()
        # Load SHACL shapes if available
        shapes_file = os.getenv("SHACL_SHAPES_FILE", "shacl_shapes.ttl")
        if os.path.exists(shapes_file):
            self.shacl_shapes.parse(shapes_file, format="turtle")
            logger.info(f"Loaded SHACL shapes from {shapes_file}")
        else:
            logger.warning(f"SHACL shapes file not found: {shapes_file}. Validation will use empty shapes.")
    
    async def validate_data(self, data_graph: str, format: str = "turtle") -> Dict[str, Any]:
        """
        Validate RDF data against SHACL shapes.
        
        Args:
            data_graph: RDF data as string
            format: RDF format (turtle, xml, json-ld, etc.)
        
        Returns:
            Validation result with conforms status and violations
        """
        try:
            # Parse data graph
            data = Graph()
            data.parse(data=data_graph, format=format)
            
            # Validate using pySHACL
            conforms, results_graph, results_text = validate(
                data,
                shacl_graph=self.shacl_shapes,
                inference='rdfs',
                abort_on_first=False
            )
            
            # Extract violations
            violations = []
            if not conforms:
                # Parse validation results
                for result in results_graph.subjects(predicate=None, object=None):
                    violation = {
                        "message": str(results_graph.value(result, Namespace("http://www.w3.org/ns/shacl#")["resultMessage"])),
                        "path": str(results_graph.value(result, Namespace("http://www.w3.org/ns/shacl#")["resultPath"])),
                        "severity": str(results_graph.value(result, Namespace("http://www.w3.org/ns/shacl#")["resultSeverity"]))
                    }
                    violations.append(violation)
            
            return {
                "conforms": conforms,
                "violations": violations,
                "results_text": results_text
            }
        except Exception as e:
            logger.error(f"SHACL validation error: {e}")
            return {
                "conforms": False,
                "violations": [{"message": f"Validation error: {str(e)}"}],
                "error": str(e)
            }
    
    async def get_patient_data(self, patient_id: str) -> Dict[str, Any]:
        """
        Get patient data for validation.
        
        NOTE: This requires connection to HIS system.
        Configure HIS_API_URL and HIS_API_KEY environment variables.
        """
        his_url = os.getenv("HIS_API_URL")
        his_key = os.getenv("HIS_API_KEY")
        
        if not his_url or not his_key:
            raise RuntimeError(
                "HIS system not configured. Set HIS_API_URL and HIS_API_KEY environment variables."
            )
        
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{his_url}/patients/{patient_id}",
                    headers={"Authorization": f"Bearer {his_key}"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"HIS API error: {e}")
            raise
    
    async def compare_with_baseline(self, current_data: Dict, baseline_data: Dict) -> Dict[str, Any]:
        """
        Compare current data with baseline.
        Returns differences and quality metrics.
        """
        try:
            differences = []
            
            # Compare keys
            current_keys = set(current_data.keys())
            baseline_keys = set(baseline_data.keys())
            
            missing_keys = baseline_keys - current_keys
            extra_keys = current_keys - baseline_keys
            
            if missing_keys:
                differences.append({
                    "type": "missing_fields",
                    "fields": list(missing_keys)
                })
            
            if extra_keys:
                differences.append({
                    "type": "extra_fields",
                    "fields": list(extra_keys)
                })
            
            # Compare values for common keys
            for key in current_keys & baseline_keys:
                if current_data[key] != baseline_data[key]:
                    differences.append({
                        "type": "value_change",
                        "field": key,
                        "current": current_data[key],
                        "baseline": baseline_data[key]
                    })
            
            return {
                "has_differences": len(differences) > 0,
                "differences": differences,
                "quality_score": 1.0 - (len(differences) / max(len(baseline_keys), 1))
            }
        except Exception as e:
            logger.error(f"Baseline comparison error: {e}")
            return {
                "has_differences": True,
                "differences": [],
                "error": str(e)
            }

# Singleton instance
sandbox_service = SandboxService()
