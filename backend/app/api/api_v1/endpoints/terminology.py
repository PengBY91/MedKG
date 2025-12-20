from fastapi import APIRouter, Body, UploadFile, File, Depends
from typing import List
from app.services.terminology_service import terminology_service
from app.services.governance_service import governance_service
from app.core.auth import get_current_user

from app.services.knowledge_store_service import knowledge_store

router = APIRouter()

@router.get("/")
async def list_terms():
    """List all standardized terminology mappings."""
    return await knowledge_store.get_all_terms()

@router.delete("/{term}")
async def delete_term(term: str):
    """Delete a terminology mapping."""
    await knowledge_store.delete_term(term)
    return {"status": "success"}

@router.post("/upload")
async def upload_terms(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload terminology file (CSV/TXT) for bulk normalization.
    Creates a 'term_review' task.
    """
    content = await file.read()
    text = content.decode("utf-8")
    lines = [t.strip() for t in text.splitlines() if t.strip()]
    if lines and "OriginalTerm" in lines[0]:
        terms = lines[1:]
    else:
        terms = lines
    
    # Create Review Task
    # We mock the normalization result here or let the worker do it.
    # For this flow, we'll store the raw terms in the review task 
    # and let the Review UI trigger the "Auto-Normalize" (using normalise endpoint) 
    # OR we pre-normalize here. Let's pre-normalize a few for demo.
    
    normalized_results = await terminology_service.normalize(terms[:5]) # Normalize first 5 for preview
    
    task_data = {
        "filename": file.filename,
        "total_terms": len(terms),
        "entities": [
            {"term": r["term"], "suggestion": r.get("code", "UNKNOWN"), "confidence": r.get("confidence", 0.0)}
            for r in normalized_results
        ]
        # In a real app, we'd process all async
    }
    
    task_id = await governance_service.create_review_task(
        doc_id=f"term-batch-{file.filename}",
        extraction_result=task_data,
        task_type="term_review"
    )
    
    return {"task_id": task_id, "message": "Batch uploaded for review"}

@router.post("/normalize")
async def normalize_terms(terms: List[str] = Body(..., embed=True)):
    """
    Normalize clinical terms to standard codes using LLM + Vector Search.
    """
    return await terminology_service.normalize(terms)

@router.post("/feedback")
async def submit_feedback(
    term: str = Body(...),
    suggested_code: str = Body(...),
    reviewer_id: str = Body(...),
    status: str = Body(..., regex="^(APPROVED|REJECTED)$")
):
    """
    Submit human review feedback for terminology mapping.
    This will be used to improve future mappings (few-shot learning).
    """
    # Persist the approved mapping
    if status == "APPROVED":
        await knowledge_store.add_terms([{"term": term, "code": suggested_code, "status": "APPROVED"}])
        
    return {
        "status": "success",
        "message": f"Feedback recorded for term '{term}'",
        "data": {
            "term": term,
            "suggested_code": suggested_code,
            "reviewer_id": reviewer_id,
            "review_status": status
        }
    }



