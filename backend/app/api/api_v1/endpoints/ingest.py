from fastapi import APIRouter, UploadFile, File, Depends, Query, HTTPException
from typing import Optional
from app.services.enhanced_ingest_service import enhanced_ingest_service
from app.core.auth import get_current_user

router = APIRouter()

# Global service instance
ingest_service = enhanced_ingest_service

@router.post("/document")
async def ingest_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload and process a policy document (PDF/TXT).
    Tracks upload history.
    """
    result = await ingest_service.process_document(file, current_user["username"])
    return result

@router.get("/history")
async def get_upload_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get upload history with pagination and filtering.
    """
    history = await ingest_service.get_upload_history(skip=skip, limit=limit, status=status)
    return {
        "items": history,
        "total": len(history),
        "skip": skip,
        "limit": limit
    }

@router.get("/history/{upload_id}")
async def get_upload_detail(
    upload_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get upload detail by ID."""
    detail = await ingest_service.get_upload_detail(upload_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Upload record not found")
    return detail

@router.delete("/history/{upload_id}")
async def delete_upload(
    upload_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete upload record."""
    success = await ingest_service.delete_upload(upload_id)
    if not success:
        raise HTTPException(status_code=404, detail="Upload record not found")
    return {"message": "Upload record deleted successfully"}
