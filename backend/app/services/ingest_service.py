import io
from typing import List
from pypdf import PdfReader
from fastapi import UploadFile

class IngestionService:
    async def process_document(self, file: UploadFile) -> dict:
        """
        Process an uploaded file: Parse -> Chunk -> (Mock) Embedding
        """
        content = await file.read()
        filename = file.filename
        
        text = ""
        if filename.lower().endswith(".pdf"):
            text = self._parse_pdf(content)
        elif filename.lower().endswith(".txt"):
            text = content.decode("utf-8")
        else:
            return {"error": "Unsupported file format. Only .pdf and .txt are supported."}
            
        chunks = self._chunk_text(text)
        
        # TODO: Send event DocumentUploaded(chunk_ids)
        
        return {
            "filename": filename,
            "status": "processed",
            "total_chars": len(text),
            "chunks_count": len(chunks),
            "sample_chunk": chunks[0] if chunks else ""
        }

    def _parse_pdf(self, content: bytes) -> str:
        """
        Extract text from PDF bytes.
        """
        try:
            reader = PdfReader(io.BytesIO(content))
            text = []
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text.append(extracted)
            return "\n".join(text)
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            return ""

    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """
        Simple sliding window chunking.
        """
        if not text:
            return []
            
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + chunk_size
            chunks.append(text[start:end])
            start += (chunk_size - overlap)
            
        return chunks
