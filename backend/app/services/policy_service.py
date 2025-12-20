from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import os

class PolicyDocument:
    """Policy document model."""
    def __init__(
        self,
        filename: str,
        tenant_id: str,
        uploaded_by: str,
        file_size: int
    ):
        self.id = str(uuid.uuid4())
        self.tenant_id = tenant_id
        self.filename = filename
        self.file_size = file_size
        self.uploaded_by = uploaded_by
        self.status = "processing"  # processing, completed, failed
        self.version = 1
        self.category = "未分类"
        self.tags = []
        self.total_chars = 0
        self.chunks_count = 0
        self.extracted_rules_count = 0
        self.error_message = None
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()
        self.completed_at = None

class PolicyService:
    """Enhanced policy document service."""
    
    def __init__(self):
        self.documents: Dict[str, PolicyDocument] = {}
    
    def _create_sample_documents(self):
        """Create sample policy documents."""
        pass

    async def upload_document(
        self,
        filename: str,
        file_size: int,
        tenant_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Upload a new policy document."""
        doc = PolicyDocument(
            filename=filename,
            tenant_id=tenant_id,
            uploaded_by=user_id,
            file_size=file_size
        )
        
        # Simulate processing
        doc.status = "completed"
        doc.total_chars = file_size // 10  # Mock calculation
        doc.chunks_count = file_size // 10000  # Mock calculation
        doc.completed_at = datetime.utcnow().isoformat()
        
        self.documents[doc.id] = doc
        return self._document_to_dict(doc)
    
    async def get_documents(
        self,
        tenant_id: str,
        category: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get policy documents with filtering."""
        docs = [d for d in self.documents.values() if d.tenant_id == tenant_id]
        
        if category:
            docs = [d for d in docs if d.category == category]
        if status:
            docs = [d for d in docs if d.status == status]
        
        # Sort by created_at descending
        docs.sort(key=lambda x: x.created_at, reverse=True)
        
        # Pagination
        docs = docs[skip:skip + limit]
        
        return [self._document_to_dict(d) for d in docs]
    
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        doc = self.documents.get(document_id)
        if not doc:
            return None
        return self._document_to_dict(doc)
    
    async def update_document(
        self,
        document_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update document metadata."""
        doc = self.documents.get(document_id)
        if not doc:
            return None
        
        if "category" in update_data:
            doc.category = update_data["category"]
        if "tags" in update_data:
            doc.tags = update_data["tags"]
        
        doc.updated_at = datetime.utcnow().isoformat()
        
        return self._document_to_dict(doc)
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete a document."""
        if document_id in self.documents:
            del self.documents[document_id]
            return True
        return False
    
    async def get_statistics(self, tenant_id: str) -> Dict[str, Any]:
        """Get policy statistics."""
        docs = [d for d in self.documents.values() if d.tenant_id == tenant_id]
        
        total_docs = len(docs)
        completed_docs = len([d for d in docs if d.status == "completed"])
        processing_docs = len([d for d in docs if d.status == "processing"])
        failed_docs = len([d for d in docs if d.status == "failed"])
        total_rules = sum(d.extracted_rules_count for d in docs)
        
        # Category distribution
        categories = {}
        for doc in docs:
            categories[doc.category] = categories.get(doc.category, 0) + 1
        
        return {
            "total_documents": total_docs,
            "completed": completed_docs,
            "processing": processing_docs,
            "failed": failed_docs,
            "total_extracted_rules": total_rules,
            "categories": categories
        }
    
    def _document_to_dict(self, doc: PolicyDocument) -> Dict[str, Any]:
        """Convert document to dict."""
        return {
            "id": doc.id,
            "tenant_id": doc.tenant_id,
            "filename": doc.filename,
            "file_size": doc.file_size,
            "uploaded_by": doc.uploaded_by,
            "status": doc.status,
            "version": doc.version,
            "category": doc.category,
            "tags": doc.tags,
            "total_chars": doc.total_chars,
            "chunks_count": doc.chunks_count,
            "extracted_rules_count": doc.extracted_rules_count,
            "error_message": doc.error_message,
            "created_at": doc.created_at,
            "updated_at": doc.updated_at,
            "completed_at": doc.completed_at
        }
