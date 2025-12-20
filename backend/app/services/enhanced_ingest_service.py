from typing import List, Dict, Any, Optional
from fastapi import UploadFile
import io
import os
from pypdf import PdfReader
import uuid
from datetime import datetime

# DeepKE Mock Imports
try:
    from deepke.name_entity_re.few_shot import FewShotNER
    from deepke.relation_extraction.document import DocRE
    HAS_DEEPKE = True
except ImportError:
    HAS_DEEPKE = False
    print("DeepKE SDK not found. Using Mock Extractor.")
    class FewShotNER:
        def __init__(self, *args, **kwargs): pass
        def predict(self, text): return [{"entity": "MockEntity", "type": "Disease", "offset": [0, 10]}]
    class DocRE:
        def __init__(self, *args, **kwargs): pass
        def predict(self, text): return [{"head": "Drug", "tail": "Disease", "relation": "Treats"}]

import logging

logger = logging.getLogger(__name__)

class UploadRecord:
    """Upload record model."""
    def __init__(self, filename: str, user: str):
        self.id = str(uuid.uuid4())
        self.filename = filename
        self.status = "processing"
        self.user = user
        self.created_at = datetime.utcnow().isoformat()
        self.completed_at = None
        self.error_message = None
        self.extraction_result = {}

class EnhancedIngestionService:
    """
    Intelligent Ingestion Service Integration with DeepKE.
    Features:
    1. Few-Shot Entity Extraction (for low-resource domains).
    2. Document-Level Relation Extraction (for cross-sentence context).
    """
    
    def __init__(self):
        self.upload_history: Dict[str, UploadRecord] = {}
        
        # Initialize DeepKE Models
        # In production, models would be loaded from pre-trained paths
        if HAS_DEEPKE:
            logger.info("Initializing DeepKE NER and RE models...")
            self.ner_model = FewShotNER(load_path=os.getenv("DEEPKE_NER_PATH", "./models/deepke_ner"))
            self.re_model = DocRE(load_path=os.getenv("DEEPKE_RE_PATH", "./models/deepke_re"))
        else:
            logger.warning("DeepKE SDK not found. Initializing Mock Extractor.")
            self.ner_model = FewShotNER()
            self.re_model = DocRE()
    
    async def process_document(self, file: UploadFile, user: str = "system") -> dict:
        """Process document: Text -> DeepKE Extraction -> Structured Data."""
        record = UploadRecord(file.filename, user)
        self.upload_history[record.id] = record
        
        try:
            content = await file.read()
            text = self._extract_text(file.filename, content)
            
            if not text:
                raise ValueError("Empty or unsupported document.")

            logger.info(f"Triggering DeepKE entity extraction for {file.filename} (Length: {len(text)})")
            # 1. Entity Extraction (Few-Shot)
            entities = self.ner_model.predict(text)
            
            logger.info(f"Triggering DeepKE relation extraction for {file.filename}")
            # 2. Relation Extraction (Document-Level)
            # DeepKE DocRE typically handles long text with cross-sentence reasoning
            relations = self.re_model.predict(text)
            
            # 3. Structure Result
            result = {
                "text_first_500": text[:500],
                "entities": entities,
                "relations": relations
            }
            
            record.status = "completed"
            record.completed_at = datetime.utcnow().isoformat()
            record.extraction_result = result
            
            logger.info(f"DeepKE processing completed for {file.filename}. Entities: {len(entities)}, Relations: {len(relations)}")
            
            # Phase 7: Trigger Automated Governance Workflow
            try:
                from app.services.workflow_engine import workflow_engine
                gov_def = next((d for d in workflow_engine.definitions.values() if d.type == "governance_pipeline"), None)
                if gov_def:
                    await workflow_engine.start_workflow(
                        definition_id=gov_def.id,
                        tenant_id="default",
                        context={
                            "document_name": file.filename,
                            "document_content": text,
                            "upload_id": record.id,
                            "entities": [e.get("entity") for e in entities if e.get("entity")],
                            "entities_count": len(entities)
                        },
                        initiator=user
                    )
                    logger.info(f"Triggered governance_pipeline for document: {file.filename}")
            except Exception as we:
                logger.error(f"Failed to trigger workflow: {str(we)}")

            return {
                "upload_id": record.id,
                "status": "completed",
                "entities_count": len(entities),
                "relations_count": len(relations)
            }
            
        except Exception as e:
            record.status = "failed"
            record.error_message = str(e)
            return {"upload_id": record.id, "error": str(e)}

    def _extract_text(self, filename: str, content: bytes) -> str:
        if filename.lower().endswith(".pdf"):
            try:
                reader = PdfReader(io.BytesIO(content))
                return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
            except:
                return ""
        elif filename.lower().endswith(".txt"):
            return content.decode("utf-8")
        return ""

    async def get_upload_history(self) -> List[Dict]:
        return [vars(r) for r in self.upload_history.values()]

# Singleton
enhanced_ingest_service = EnhancedIngestionService()
