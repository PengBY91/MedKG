from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import json
from fastapi import UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.db.base import SessionLocal
from app.db.models import PolicyDocument as PolicyDocumentModel
from app.services.file_storage_service import file_storage
from app.services.cache_service import cache_service, cached

class PolicyService:
    """Enhanced policy document service with database persistence."""
    
    def __init__(self):
        # We'll use database sessions instead of this local dictionary
        pass
    
    async def upload_document(
        self,
        file: UploadFile,
        tenant_id: str,
        user_id: str,
        extracted_rules: Optional[List[Dict]] = None,
        extracted_entities: Optional[List[Dict]] = None,
        preview_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save document to storage and database.
        """
        db = SessionLocal()
        try:
            doc_id = str(uuid.uuid4())
            
            # Save physical file
            file_path = await file_storage.save_file(
                file=file,
                category="policies",
                tenant_id=tenant_id,
                prefix=doc_id
            )
            
            # Create database record
            new_doc = PolicyDocumentModel(
                id=doc_id,
                tenant_id=tenant_id,
                filename=file.filename,
                file_size=0, # Will be set after seeking or from file object if available
                file_path=file_path,
                uploaded_by=user_id,
                status="completed",
                extracted_rules_count=len(extracted_rules) if extracted_rules else 0,
                extracted_rules=json.dumps(extracted_rules) if extracted_rules else "[]",
                extracted_entities=json.dumps(extracted_entities) if extracted_entities else "[]",
                preview_text=preview_text or ""
            )
            
            db.add(new_doc)
            db.commit()
            db.refresh(new_doc)
            
            # Invalidate cache
            await cache_service.clear_pattern(f"policy_stats:{tenant_id}*")
            await cache_service.clear_pattern(f"policy_list:{tenant_id}*")
            
            return self._document_to_dict(new_doc)
        finally:
            db.close()
    
    @cached("policy_list", expire=300)
    async def get_documents(
        self,
        tenant_id: str,
        category: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get policy documents with filtering from database."""
        db = SessionLocal()
        try:
            query = db.query(PolicyDocumentModel).filter(PolicyDocumentModel.tenant_id == tenant_id)
            
            if category:
                query = query.filter(PolicyDocumentModel.category == category)
            if status:
                query = query.filter(PolicyDocumentModel.status == status)
            
            query = query.order_by(desc(PolicyDocumentModel.created_at))
            docs = query.offset(skip).limit(limit).all()
            
            return [self._document_to_dict(d) for d in docs]
        finally:
            db.close()
    
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID from database."""
        db = SessionLocal()
        try:
            doc = db.query(PolicyDocumentModel).filter(PolicyDocumentModel.id == document_id).first()
            if not doc:
                return None
            return self._document_to_dict(doc)
        finally:
            db.close()
    
    async def update_document(
        self,
        document_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update document metadata in database."""
        db = SessionLocal()
        try:
            doc = db.query(PolicyDocumentModel).filter(PolicyDocumentModel.id == document_id).first()
            if not doc:
                return None
            
            if "category" in update_data:
                doc.category = update_data["category"]
            if "tags" in update_data:
                doc.tags = json.dumps(update_data["tags"])
            
            doc.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(doc)
            
            # Invalidate cache
            await cache_service.clear_pattern(f"policy_list:{doc.tenant_id}*")
            
            return self._document_to_dict(doc)
        finally:
            db.close()
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete document record and physical file.
        """
        db = SessionLocal()
        try:
            doc = db.query(PolicyDocumentModel).filter(PolicyDocumentModel.id == document_id).first()
            if not doc:
                return False
            
            # Delete physical file
            if doc.file_path:
                file_storage.delete_file(doc.file_path)
            
            tenant_id = doc.tenant_id
            db.delete(doc)
            db.commit()
            
            # Invalidate cache
            await cache_service.clear_pattern(f"policy_stats:{tenant_id}*")
            await cache_service.clear_pattern(f"policy_list:{tenant_id}*")
            
            return True
        finally:
            db.close()
    
    @cached("policy_stats", expire=600)
    async def get_statistics(self, tenant_id: str) -> Dict[str, Any]:
        """Get policy statistics from database."""
        db = SessionLocal()
        try:
            base_query = db.query(PolicyDocumentModel).filter(PolicyDocumentModel.tenant_id == tenant_id)
            
            total_docs = base_query.count()
            completed_docs = base_query.filter(PolicyDocumentModel.status == "completed").count()
            processing_docs = base_query.filter(PolicyDocumentModel.status == "processing").count()
            failed_docs = base_query.filter(PolicyDocumentModel.status == "failed").count()
            
            total_rules = db.query(func.sum(PolicyDocumentModel.extracted_rules_count)).filter(
                PolicyDocumentModel.tenant_id == tenant_id
            ).scalar() or 0
            
            # Category distribution
            categories_result = db.query(
                PolicyDocumentModel.category, 
                func.count(PolicyDocumentModel.id)
            ).filter(
                PolicyDocumentModel.tenant_id == tenant_id
            ).group_by(PolicyDocumentModel.category).all()
            
            categories = {cat: count for cat, count in categories_result}
            
            return {
                "total_documents": total_docs,
                "completed": completed_docs,
                "processing": processing_docs,
                "failed": failed_docs,
                "total_extracted_rules": int(total_rules),
                "categories": categories
            }
        finally:
            db.close()
    
    def _document_to_dict(self, doc: PolicyDocumentModel) -> Dict[str, Any]:
        """Convert SQLAlchemy document model to dict."""
        return {
            "id": doc.id,
            "tenant_id": doc.tenant_id,
            "filename": doc.filename,
            "file_size": doc.file_size,
            "file_path": doc.file_path,
            "uploaded_by": doc.uploaded_by,
            "status": doc.status,
            "version": 1, # hardcoded for now as it's not in DB yet
            "category": doc.category or "未分类",
            "tags": json.loads(doc.tags) if doc.tags else [],
            "total_chars": doc.total_chars,
            "chunks_count": doc.chunks_count,
            "extracted_rules_count": doc.extracted_rules_count,
            "extracted_rules": json.loads(doc.extracted_rules) if doc.extracted_rules else [],
            "extracted_entities": json.loads(doc.extracted_entities) if doc.extracted_entities else [],
            "preview_text": doc.preview_text,
            "error_message": doc.error_message,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
            "completed_at": doc.completed_at.isoformat() if doc.completed_at else None
        }

