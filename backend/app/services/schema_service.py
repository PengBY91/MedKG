from typing import List, Dict, Any, Optional
import os

# Try importing OpenSPG SDK, else use mocks for now (to avoid immediate crashing if not installed)
try:
    from openspg.api import OpenSPGClient
    from openspg.schema import SPGSchema, Property, Relation, ConceptType, EntityType, EventType
    HAS_OPENSPG = True
except ImportError:
    HAS_OPENSPG = False
    print("OpenSPG SDK not found. Using Mock Client.")

    class SPGSchema:
        pass
    class Property:
        pass
    class Relation:
        pass

class SchemaService:
    """
    Bridge to OpenSPG Schema Server.
    Uses native OpenSPG SDK if available to define ontology.
    """

    def __init__(self):
        from app.core.config import settings
        self.endpoint = settings.KAG_HOST
        self.project_id = settings.KAG_PROJECT_ID
        if HAS_OPENSPG:
            self.client = OpenSPGClient(endpoint=self.endpoint, project_id=self.project_id)
        else:
            self.client = None

    async def create_subject_model(self, model_def: Dict[str, Any], user: str = "system") -> Dict:
        """
        Define a Subject (EntityType) in OpenSPG.
        model_def example:
        {
            "name": "Disease",
            "properties": {"code": "Text", "description": "Text"}
        }
        """
        if not HAS_OPENSPG:
            # Mock behavior
            return {"status": "mock_created", "model": model_def}
        
        # Convert dict to OpenSPG EntityType
        properties = [
            Property(name=k, object_type_name=v) 
            for k, v in model_def.get("properties", {}).items()
        ]
        
        entity_type = EntityType(
            name=model_def["name"],
            properties=properties,
            description=model_def.get("description")
        )
        
        try:
            self.client.schema.upsert(entity_type)
            return {"status": "success", "name": model_def["name"]}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def create_predicate_model(self, relation_def: Dict[str, Any], user: str = "system") -> Dict:
        """
        Define a Predicate (Relation) in OpenSPG.
        relation_def example:
        {
            "subject": "Drug",
            "object": "Disease",
            "edge_name": "Treats",
            "properties": {"dosage": "Text"}
        }
        """
        if not HAS_OPENSPG:
             return {"status": "mock_created", "relation": relation_def}
             
        properties = [
            Property(name=k, object_type_name=v) 
            for k, v in relation_def.get("properties", {}).items()
        ]
        
        relation = Relation(
            subject_type_name=relation_def["subject"],
            object_type_name=relation_def["object"],
            name=relation_def["edge_name"],
            properties=properties,
            inverse_name=relation_def.get("inverse_name")
        )

        try:
            self.client.schema.upsert(relation)
            return {"status": "success", "relation": relation.name}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def get_schema_snapshot(self) -> Dict[str, Any]:
        if not HAS_OPENSPG:
            return {"mock": True, "subjects": [], "predicates": []}
            
        # Retrieve logical schema from OpenSPG
        return self.client.schema.list()

    async def ensure_standardization_schema(self):
        """
        Define Schema for Standardized Examination Terms.
        Subject: StdTerm
        Properties: original_name, modality, standard_json, status
        """
        model_def = {
            "name": "StdTerm",
            "properties": {
                "original_name": "Text",
                "modality": "Text",
                "standard_json": "Text",
                "status": "Text"
            },
            "description": "Standardized Examination Term Record"
        }
        return await self.create_subject_model(model_def)

# Singleton
schema_service = SchemaService()
