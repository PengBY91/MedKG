from fastapi import APIRouter, Depends, HTTPException, Query, Body, File, UploadFile
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from app.services.data_governance_service import DataGovernanceService
from app.services.examination_kg_service import examination_kg_service
from app.services.examination_kg_importer import examination_kg_importer
from app.core.auth import get_current_user

router = APIRouter()
governance_service = DataGovernanceService()

# Pydantic models for Assets
class AssetCreate(BaseModel):
    name: str
    type: str
    owner_id: str
    description: Optional[str] = ""
    metadata: Optional[dict] = {}
    tags: Optional[List[str]] = []

class AssetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[dict] = None
    tags: Optional[List[str]] = None
    steward_id: Optional[str] = None

# --- Asset Catalog Routes ---

@router.get("/assets")
async def get_assets(
    asset_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get data assets with filtering."""
    assets = await governance_service.get_assets(
        tenant_id=current_user.get("tenant_id", "default"),
        asset_type=asset_type,
        skip=skip,
        limit=limit
    )
    return {"items": assets}

@router.get("/assets/{asset_id}")
async def get_asset(
    asset_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get asset by ID."""
    asset = await governance_service.get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@router.post("/assets")
async def create_asset(
    asset_data: AssetCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create new data asset."""
    data = asset_data.dict()
    data["tenant_id"] = current_user.get("tenant_id", "default")
    asset = await governance_service.create_asset(data)
    return asset

@router.put("/assets/{asset_id}")
async def update_asset(
    asset_id: str,
    asset_data: AssetUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update asset information."""
    asset = await governance_service.update_asset(
        asset_id,
        asset_data.dict(exclude_unset=True)
    )
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@router.get("/assets/{asset_id}/lineage")
async def get_asset_lineage(
    asset_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get asset lineage (upstream and downstream)."""
    lineage = await governance_service.get_lineage(asset_id)
    if "error" in lineage:
        raise HTTPException(status_code=404, detail=lineage["error"])
    return lineage

@router.post("/assets/{asset_id}/quality-check")
async def run_quality_check(
    asset_id: str,
    data: List[Dict[str, Any]] = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """Run quality rules on provided data and update asset information."""
    report = await governance_service.run_quality_check(asset_id, data)
    if "error" in report:
        raise HTTPException(status_code=404, detail=report["error"])
    return report

@router.post("/scan")
async def scan_catalog(
    connection_info: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """Scan a data source and register new assets."""
    assets = await governance_service.scan_assets(connection_info)
    return {"scanned_assets": assets}


# --- Ontology (Knowledge Graph) Routes ---

ontology_router = APIRouter()

@ontology_router.get("/")
async def get_ontology_info():
    """Get knowledge graph ontology information."""
    await examination_kg_service.initialize()
    stats = await examination_kg_service.get_graph_stats()
    tree = await examination_kg_service.get_complete_tree()
    return {
        "success": True,
        "ontology": {**stats, "tree": tree}
    }

@ontology_router.post("/import")
async def import_ontology_data(
    file: UploadFile = File(...),
    clear_existing: bool = Query(default=False)
):
    """Import examination ontology data from CSV file into Neo4j."""
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name
    
    try:
        stats = await examination_kg_importer.import_from_csv(tmp_path, clear_existing=clear_existing)
        return {"success": True, "stats": stats}
    finally:
        os.unlink(tmp_path)

@ontology_router.get("/graph/stats")
async def get_graph_stats():
    await examination_kg_service.initialize()
    stats = await examination_kg_service.get_graph_stats()
    return {"success": True, "stats": stats}

@ontology_router.get("/graph/tree")
async def get_graph_tree():
    await examination_kg_service.initialize()
    tree = await examination_kg_service.get_complete_tree()
    return {"success": True, "tree": tree}

# Include ontology router into catalog
router.include_router(ontology_router, prefix="/ontology", tags=["ontology"])
