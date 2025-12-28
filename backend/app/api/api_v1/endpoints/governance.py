from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from app.services.data_governance_service import DataGovernanceService
from app.core.auth import get_current_user

router = APIRouter()
governance_service = DataGovernanceService()

# Pydantic models
class QualityRuleCreate(BaseModel):
    id: str
    name: str
    condition: str
    description: Optional[str] = ""
    severity: str = "warning"

@router.get("/quality/report")
async def get_quality_report(
    current_user: dict = Depends(get_current_user)
):
    """Get data quality report for tenant."""
    report = await governance_service.get_quality_report(
        tenant_id=current_user.get("tenant_id", "default")
    )
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
