from typing import List, Dict, Any
import logging
from app.services.kag_medical_builder import kag_builder
from app.core.config import settings

logger = logging.getLogger(__name__)

class EnhancedIngestService:
    """
    Enhanced Ingest Service using KAG Builder for document processing.
    Replaces DeepKE mock with real KAG extraction pipeline.
    """
    
    def __init__(self):
        """Initialize with KAG Builder."""
        self.builder = kag_builder
        logger.info("EnhancedIngestService initialized with KAG Builder")
    
    async def process_document(self, file_path: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process document using KAG Builder pipeline.
        
        Args:
            file_path: Path to document file
            metadata: Optional metadata for the document
        
        Returns:
            Processing result with extracted entities and relations
        """
        try:
            # Use KAG Builder to process document
            result = self.builder.build_document(file_path)
            
            if result['status'] == 'success':
                logger.info(f"Document processed successfully: {file_path}")
                return {
                    "status": "success",
                    "file": file_path,
                    "message": "Document processed and knowledge extracted",
                    "metadata": metadata or {}
                }
            else:
                logger.error(f"Document processing failed: {result}")
                return {
                    "status": "error",
                    "file": file_path,
                    "message": result.get("details", "Processing failed")
                }
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            return {
                "status": "error",
                "file": file_path,
                "message": str(e)
            }
    
    async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract entities from text using KAG extractor.
        For text-only extraction without full document processing.
        """
        try:
            import tempfile
            import os
            
            # Create temporary file for text
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(text)
                temp_file = f.name
            
            try:
                # Process with KAG Builder
                result = self.builder.build_document(temp_file)
                
                if result['status'] == 'success':
                    logger.info("Text entities extracted successfully")
                    return [{"status": "success", "message": "Entities extracted and stored in graph"}]
                else:
                    logger.error(f"Entity extraction failed: {result}")
                    return []
            finally:
                # Clean up temp file
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return []

# Singleton instance
enhanced_ingest_service = EnhancedIngestService()
