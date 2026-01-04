import io
import tempfile
import os
from typing import List
from pypdf import PdfReader
from fastapi import UploadFile
from app.services.kag_medical_builder import kag_builder
import logging

logger = logging.getLogger(__name__)

class IngestionService:
    """
    Document Ingestion Service using KAG Builder.
    Processes documents and extracts knowledge using KAG pipeline.
    """
    
    def __init__(self):
        self.builder = kag_builder
    
    async def process_document(self, file: UploadFile) -> dict:
        """
        Process an uploaded file using KAG Builder pipeline.
        """
        try:
            content = await file.read()
            filename = file.filename
            
            # Save to temporary file for KAG processing
            suffix = os.path.splitext(filename)[1]
            with tempfile.NamedTemporaryFile(mode='wb', suffix=suffix, delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            try:
                # Process with KAG Builder
                result = self.builder.build_document(temp_path)
                
                if result['status'] == 'success':
                    # Also extract text for preview
                    text = ""
                    if filename.lower().endswith(".pdf"):
                        text = self._parse_pdf(content)
                    elif filename.lower().endswith(".txt"):
                        text = content.decode("utf-8")
                    
                    return {
                        "filename": filename,
                        "status": "processed",
                        "total_chars": len(text),
                        "message": "Document processed and knowledge extracted to graph",
                        "kag_result": result
                    }
                else:
                    return {
                        "filename": filename,
                        "status": "error",
                        "error": result.get("details", "Processing failed")
                    }
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            logger.error(f"Document processing error: {e}")
            return {
                "filename": file.filename,
                "status": "error",
                "error": str(e)
            }

    def _parse_pdf(self, content: bytes) -> str:
        """Extract text from PDF bytes."""
        try:
            reader = PdfReader(io.BytesIO(content))
            text = []
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text.append(extracted)
            return "\n".join(text)
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            return ""

# Singleton instance
ingest_service = IngestionService()
