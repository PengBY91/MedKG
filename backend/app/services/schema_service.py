from typing import List, Dict, Any, Optional
import os
import logging

logger = logging.getLogger(__name__)

# Import from knext (openspg-kag)
try:
    from knext.schema.client import SchemaClient
    from knext.schema.model.spg_type import EntityType, SpgTypeEnum
    from knext.schema.model.property import Property
    from knext.schema.model.relation import Relation
    HAS_OPENSPG = True
except ImportError as e:
    HAS_OPENSPG = False
    logger.warning(f"OpenSPG SDK (knext) not found: {e}. Using Mock Client.")

    # Mock classes
    class SchemaClient:
        def __init__(self, **kwargs): pass
    class EntityType:
        pass
    class Property:
        pass
    class Relation:
        pass

class SchemaService:
    """
    Bridge to OpenSPG Schema Server using knext SDK.
    """

    def __init__(self):
        from app.core.config import settings
        self.endpoint = settings.KAG_HOST
        self.project_id = settings.KAG_PROJECT_ID
        if HAS_OPENSPG:
            self.client = SchemaClient(host_addr=self.endpoint, project_id=self.project_id)
        else:
            self.client = None

    async def create_subject_model(self, model_def: Dict[str, Any], user: str = "system") -> Dict:
        """
        Define a Subject (EntityType) in OpenSPG.
        """
        if not HAS_OPENSPG or not self.client:
            return {"status": "mock_created", "model": model_def}
        
        try:
            # Convert properties dict to List[Property]
            properties = []
            for k, v in model_def.get("properties", {}).items():
                # Basic mapping for now, assuming Text if not specified
                obj_type = v if isinstance(v, str) else "Text"
                properties.append(Property(
                    name=k, 
                    object_type_name=obj_type,
                    name_zh=k  # Use property name as Chinese name if not specified
                ))

            entity_type = EntityType(
                name=model_def["name"],
                name_zh=model_def.get("name_zh", model_def["name"]),
                properties=properties,
                desc=model_def.get("description")
            )
            
            session = self.client.create_session()
            session.create_type(entity_type)
            session.commit()
            
            return {"status": "success", "name": model_def["name"]}
        except Exception as e:
            logger.error(f"Failed to create subject model: {e}")
            return {"status": "error", "message": str(e)}

    async def create_predicate_model(self, relation_def: Dict[str, Any], user: str = "system") -> Dict:
        """
        Define a Predicate (Relation) in OpenSPG.
        In OpenSPG, relations are attached to the Subject EntityType.
        """
        if not HAS_OPENSPG or not self.client:
             return {"status": "mock_created", "relation": relation_def}
             
        try:
            subject_name = relation_def["subject"]
            object_name = relation_def["object"]
            edge_name = relation_def["edge_name"]
            
            session = self.client.create_session()
            
            # Get existing subject type
            try:
                subject_type = session.get(subject_name)
            except ValueError:
                return {"status": "error", "message": f"Subject type {subject_name} not found"}

            # Define relation
            # Note: relations are usually passed in constructor or appended to .relations
            # But knext might expect them as part of update
            
            new_relation = Relation(
                name=edge_name,
                object_type_name=object_name,
                desc=relation_def.get("description")
            )
            
            # Add to subject type's relations
            # If relations is None or dict, handle it
            if subject_type.relations is None:
                subject_type.relations = {}
            
            subject_type.relations[edge_name] = new_relation
            
            # Update type
            session.update_type(subject_type)
            session.commit()

            return {"status": "success", "relation": edge_name}
        except Exception as e:
            logger.error(f"Failed to create predicate model: {e}")
            return {"status": "error", "message": str(e)}

    async def get_schema_snapshot(self) -> Dict[str, Any]:
        if not HAS_OPENSPG or not self.client:
            return {"mock": True, "subjects": [], "predicates": []}
            
        return self.client.load()

# Singleton
schema_service = SchemaService()
