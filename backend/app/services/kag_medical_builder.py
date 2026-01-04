# backend/app/services/kag_medical_builder.py
import os
import logging
from kag.builder.runner import BuilderChainRunner
from kag.common.conf import KAG_CONFIG
from app.core.config import settings

logger = logging.getLogger(__name__)

class KAGMedicalBuilder:
    def __init__(self):
        self.config_path = os.path.join(settings.PROJECT_ROOT, "config/kag_config.yaml")
        # Ensure configuration is initialized
        # Note: KAG_CONFIG might be initialized multiple times, catch warning
        try:
            if not KAG_CONFIG._is_initialized:
                 KAG_CONFIG.initialize(prod=False, config_file=self.config_path)
            logger.info("KAGMedicalBuilder initialized with config: %s", self.config_path)
        except Exception as e:
            logger.error(f"Failed to initialize KAG config: {e}")

    def build_document(self, file_path: str):
        """
        Ingest a medical document (PDF/TXT) into the Knowledge Graph.
        
        Args:
            file_path: Absolute path to the file.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document not found: {file_path}")

        try:
            # 1. Retrieve the specific runner config for unstructured data
            # Key 'unstructured_builder' must match config/kag_config.yaml
            runner_config = KAG_CONFIG.all_config.get("unstructured_builder")
            if not runner_config:
                raise ValueError("Config key 'unstructured_builder' not found in config/kag_config.yaml")

            # 2. Initialize the Runner
            logger.info(f"Starting KAG build for: {file_path}")
            runner = BuilderChainRunner.from_config(runner_config)
            
            # 3. Invoke Pipeline
            # invoke() returns a list of results, usually artifacts or status
            result = runner.invoke(file_path)
            
            logger.info(f"Successfully finished build for: {file_path}")
            return {"status": "success", "file": file_path, "details": str(result)}
            
        except Exception as e:
            logger.error(f"Error building document {file_path}: {e}")
            raise e

# Singleton instance
kag_builder = KAGMedicalBuilder()
