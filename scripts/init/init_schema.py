import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.schema_service import schema_service

async def init_schema():
    print("Initializing MedKG Schema...")
    
    # Define all entity types
    entities = [
        {
            "name": "MedicalGovernance.Disease",
            "name_zh": "疾病",
            "description": "Medical disease entity",
            "properties": {
                "diseaseCode": "Text",
                "diseaseName": "Text"
            }
        },
        {
            "name": "MedicalGovernance.Drug",
            "name_zh": "药物",
            "description": "Medical drug entity",
            "properties": {
                "drugCode": "Text",
                "drugName": "Text",
                "dosage": "Text"
            }
        },
        {
            "name": "MedicalGovernance.Symptom",
            "name_zh": "症状",
            "description": "Medical symptom entity",
            "properties": {
                "symptomName": "Text",
                "severity": "Text"
            }
        }
    ]
    
    # Create entities one by one
    for entity_def in entities:
        print(f"\nCreating entity: {entity_def['name']}")
        result = await schema_service.create_subject_model(entity_def)
        if result['status'] == 'success':
            print(f"✅ {entity_def['name']} created successfully")
        else:
            # Check if it's a duplicate error
            if 'exist' in str(result.get('message', '')).lower():
                print(f"⚠️  {entity_def['name']} already exists, skipping")
            else:
                print(f"❌ Failed to create {entity_def['name']}: {result}")
    
    # Define relations
    relations = [
        {
            "subject": "MedicalGovernance.Drug",
            "object": "MedicalGovernance.Disease",
            "edge_name": "treats",
            "description": "Drug treats disease relationship"
        },
        {
            "subject": "MedicalGovernance.Disease",
            "object": "MedicalGovernance.Symptom",
            "edge_name": "hasSymptom",
            "description": "Disease has symptom relationship"
        }
    ]
    
    # Create relations one by one
    for relation_def in relations:
        print(f"\nCreating relation: {relation_def['subject']}-{relation_def['edge_name']}-{relation_def['object']}")
        result = await schema_service.create_predicate_model(relation_def)
        if result['status'] == 'success':
            print(f"✅ Relation created successfully")
        else:
            if 'exist' in str(result.get('message', '')).lower():
                print(f"⚠️  Relation already exists, skipping")
            else:
                print(f"❌ Failed to create relation: {result}")
    
    print("\n" + "="*60)
    print("Schema Initialization Complete!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(init_schema())
