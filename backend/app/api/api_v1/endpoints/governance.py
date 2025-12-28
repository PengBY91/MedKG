from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from app.services.data_governance_service import DataGovernanceService
from app.core.auth import get_current_user

router = APIRouter()
governance_service = DataGovernanceService()

# Pydantic models
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

class QualityRuleCreate(BaseModel):
    id: str
    name: str
    condition: str
    description: Optional[str] = ""
    severity: str = "warning"

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

@router.get("/quality/report")
async def get_quality_report(
    current_user: dict = Depends(get_current_user)
):
    """Get data quality report for tenant."""
    report = await governance_service.get_quality_report(
        tenant_id=current_user.get("tenant_id", "default")
    )
    return report


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

@router.post("/quality/rules")
async def add_quality_rule(
    rule_data: QualityRuleCreate,
    current_user: dict = Depends(get_current_user)
):
    """Register a new data quality rule."""
    from app.services.quality_rule_engine import quality_engine, QualityRule
    rule = QualityRule(**rule_data.dict())
    quality_engine.add_rule(rule)
    return {"status": "success", "rule_id": rule.id}

@router.post("/catalog/scan")
async def scan_catalog(
    connection_info: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """Scan a data source and register new assets."""
    assets = await governance_service.scan_assets(connection_info)
    return {"scanned_assets": assets}



# --- Phase 5: Human-in-the-Loop Review API ---
from app.services.governance_service import governance_service as review_service

@router.get("/reviews/pending")
async def get_pending_reviews(
    current_user: dict = Depends(get_current_user)
):
    """Get pending governance review tasks."""
    return await review_service.get_pending_reviews()

@router.post("/reviews/{task_id}/decision")
async def submit_review_decision(
    task_id: str,
    decision: str = Query(..., regex="^(approve|reject|correct)$"),
    corrected_data: Optional[dict] = Body(None),
    current_user: dict = Depends(get_current_user)
):
    """Submit human decision for a review task."""
    result = await review_service.submit_review(
        task_id, 
        decision, 
        corrected_data, 
        reviewer=current_user.get("username", "unknown")
    )
    return {"status": "success", "task_status": result}
