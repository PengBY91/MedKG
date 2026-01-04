"""
KAG API Endpoints for MedKG
Provides REST API for knowledge graph construction and Q&A
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import tempfile
import logging

from app.services.kag_medical_builder import kag_builder
from app.services.kag_solver_service import kag_solver

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/kag", tags=["KAG"])

# Request/Response Models
class QueryRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None

class QueryResponse(BaseModel):
    status: str
    answer: Optional[str]
    reasoning_trace: Optional[List[Dict]] = []
    sources: Optional[List[Dict]] = []
    metadata: Optional[Dict] = {}
    message: Optional[str] = None

class BuildResponse(BaseModel):
    status: str
    file: str
    details: Optional[str] = None
    message: Optional[str] = None

# Endpoints

@router.post("/build/document", response_model=BuildResponse)
async def build_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    doc_id: Optional[str] = None
):
    """
    Upload and process a medical document into the knowledge graph
    
    - **file**: PDF, TXT, or other supported document
    - **doc_id**: Optional document identifier
    """
    try:
        # Save uploaded file temporarily
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        logger.info(f"Processing uploaded file: {file.filename} -> {tmp_path}")
        
        # Build document (synchronous for now, can be made async)
        result = kag_builder.build_document(tmp_path)
        
        # Schedule cleanup
        background_tasks.add_task(os.unlink, tmp_path)
        
        return BuildResponse(
            status=result.get("status", "success"),
            file=file.filename,
            details=result.get("details"),
            message=f"Document '{file.filename}' processed successfully"
        )
        
    except Exception as e:
        logger.error(f"Error building document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=QueryResponse)
async def query_knowledge_graph(request: QueryRequest):
    """
    Query the medical knowledge graph using natural language
    
    - **query**: Natural language question
    - **context**: Optional context (patient info, constraints, etc.)
    
    Returns answer with reasoning trace and sources
    """
    try:
        result = await kag_solver.solve_query(
            query=request.query,
            context=request.context
        )
        
        return QueryResponse(**result)
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """
    Check if KAG services are healthy
    """
    builder_status = "ok" if kag_builder else "not_initialized"
    solver_status = "ok" if kag_solver.solver_runner else "not_initialized"
    
    return {
        "status": "healthy",
        "services": {
            "builder": builder_status,
            "solver": solver_status
        }
    }

@router.get("/stats")
async def get_stats():
    """
    Get knowledge graph statistics
    """
    # TODO: Implement actual stats from OpenSPG
    return {
        "entities": 0,
        "relations": 0,
        "documents": 0
    }
