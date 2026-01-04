import os
import sys
import json
from knext.project.client import ProjectClient

# Config from config/kag_config.yaml (simplified for project metdata)
PROJECT_CONFIG = {
    "project": {
        "namespace": "MedicalGovernance",
        "biz_scene": "medical",
        "language": "zh",
        "host_addr": "http://127.0.0.1:8887"
    },
    "vectorizer": {
        # Placeholders, will be overridden by local config/kag_config.yaml during runtime usually
        # But OpenSPG server might need some structure
        "type": "openai",
        "model": "text-embedding-3-small"
    }
}

def init_project():
    host_addr = "http://127.0.0.1:8887"
    client = ProjectClient(host_addr=host_addr)
    
    namespace = "MedicalGovernance"
    
    print(f"Checking for project {namespace}...")
    existing = client.get_by_namespace(namespace)
    
    if existing:
        print(f"Project already exists: ID={existing.id}, Namespace={existing.namespace}")
        return existing.id
    
    print("Creating new project...")
    try:
        project = client.create(
            name="Medical Governance Project",
            namespace=namespace,
            config=json.dumps(PROJECT_CONFIG),
            desc="MedKG Knowledge Graph Project"
        )
        print(f"Project created successfully: ID={project.id}")
        return project.id
    except Exception as e:
        print(f"Failed to create project: {e}")
        return None

if __name__ == "__main__":
    init_project()
