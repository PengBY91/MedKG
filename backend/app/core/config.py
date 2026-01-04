from pydantic_settings import BaseSettings
from typing import Dict, Any
import yaml
from pathlib import Path
import os

def load_kag_config() -> Dict[str, Any]:
    """
    Load KAG configuration from kag_config.yaml in the project root.
    """
    try:
        # Resolve path relative to this file: backend/app/core/config.py
        # Root is 3 levels up: MedKG/
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent
        config_path = project_root / "kag_config.yaml"
        
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Warning: Failed to load kag_config.yaml: {e}")
    return {}

kag_cfg = load_kag_config()
kag_project_cfg = kag_cfg.get("project", {})

class Settings(BaseSettings):
    PROJECT_NAME: str = "Medical Governance Tool"
    PROJECT_ROOT: str = str(Path(__file__).parent.parent.parent.parent)
    API_V1_STR: str = "/api/v1"
    
    # Mock Database Config
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "medkg2024"
    
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: str = "19530"

    # KAG Configuration (Defaults -> YAML -> Env)
    KAG_PROJECT_ID: str = kag_project_cfg.get("id", "1")
    KAG_HOST: str = kag_project_cfg.get("host_addr", "http://127.0.0.1:8887")
    KAG_NAMESPACE: str = kag_project_cfg.get("namespace", "MedicalGovernance")

    class Config:
        case_sensitive = True

settings = Settings()
