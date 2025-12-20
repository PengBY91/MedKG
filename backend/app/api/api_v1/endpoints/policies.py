from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse
import os
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from app.services.policy_service import PolicyService
from app.services.rule_service import rule_service
from app.services.governance_service import governance_service
from app.services.terminology_service import terminology_service
from app.core.auth import get_current_user

router = APIRouter()
policy_service = PolicyService()

# Pydantic models
class PolicyUpdate(BaseModel):
    category: Optional[str] = None
    tags: Optional[List[str]] = None

@router.post("/upload")

async def upload_policy(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a policy document.
    Triggers:
    1. Rule Compilation (Rule Service)
    2. Governance Review Task (Governance Service)
    """
    try:
        # Get file info
        filename = file.filename
        
        # Read file to get size (in production, save to storage)
        content = await file.read()
        file_size = len(content)
        
        # 2. Extract Text
        try:
            policy_text = content.decode("utf-8")
        except:
            policy_text = "Unsupported file encoding. Defaulting to mock for demo."
        
        # Extract preview text (first 500 chars)
        preview_text = policy_text[:500] if policy_text else ""
        
        # 3. Compile Rules
        compilation_result = await rule_service.compile(policy_text)
        
        # 4. Extract Entities
        clinical_entities = await _extract_clinical_entities(policy_text)
        
        # 5. Save Policy Metadata and physical file
        # Seek back to start before saving
        await file.seek(0)
        document = await policy_service.upload_document(
            file=file,
            tenant_id=current_user.get("tenant_id", "default"),
            user_id=current_user.get("username"),
            extracted_rules=[compilation_result] if compilation_result else [],
            extracted_entities=clinical_entities if clinical_entities else [],
            preview_text=preview_text
        )
        
        # 5. Create Governance Review Task for Rules
        rule_task_data = {
            "source_file": filename,
            "policy_id": document["id"],
            "rules": [compilation_result] # List of extracted rules
        }
        rule_task_id = await governance_service.create_review_task(
            doc_id=document["id"], 
            extraction_result=rule_task_data,
            task_type="rule_review"
        )

        # 6. Create Governance Review Task for Terms
        term_task_id = None
        if clinical_entities:
            term_task_data = {
                "source_file": filename, 
                "policy_id": document["id"], 
                "entities": clinical_entities
            }
            term_task_id = await governance_service.create_review_task(
                doc_id=document["id"],
                extraction_result=term_task_data,
                task_type="term_review"
            )
            print(f"[LINKED TASK] Terminology review task created: {term_task_id}")
        
        return {
             **document,
             "rule_review_task_id": rule_task_id,
             "term_review_task_id": term_task_id, # Include term review task ID
             "compilation_status": compilation_result.get("status") if compilation_result else "unknown"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def _extract_clinical_entities(text: str) -> List[Dict]:
    """Helper to extract clinical terms for standardization."""
    # Simplified regex-based extraction for common terms in policy
    keywords = ["透析", "糖尿病", "高血压", "腹透", "血透", "冠心病"]
    found = []
    
    # Identify terms in text
    for kw in keywords:
        if kw in text:
            # Pre-standardize to suggest codes
            results = await terminology_service.normalize([kw])
            if results:
                found.append({
                    "term": kw,
                    "suggestion": results[0].get("code"),
                    "confidence": results[0].get("confidence", 0.8)
                })
    return found

@router.get("")
async def get_policies(
    category: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get policy documents."""
    documents = await policy_service.get_documents(
        tenant_id=current_user.get("tenant_id", "default"),
        category=category,
        status=status,
        skip=skip,
        limit=limit
    )
    return {"items": documents}

@router.get("/statistics")
async def get_statistics(
    current_user: dict = Depends(get_current_user)
):
    """Get policy statistics."""
    stats = await policy_service.get_statistics(
        tenant_id=current_user.get("tenant_id", "default")
    )
    return stats

@router.get("/{document_id}")
async def get_policy(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get policy document by ID."""
    document = await policy_service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@router.get("/{document_id}/download")
async def download_policy(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Download the original policy document."""
    document = await policy_service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    file_path = document.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
    
    return FileResponse(
        path=file_path,
        filename=document.get("filename"),
        media_type='application/octet-stream'
    )

@router.put("/{document_id}")
async def update_policy(
    document_id: str,
    policy_data: PolicyUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update policy metadata."""
    document = await policy_service.update_document(
        document_id,
        policy_data.dict(exclude_unset=True)
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@router.delete("/{document_id}")
async def delete_policy(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a policy document."""
    success = await policy_service.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted successfully"}
