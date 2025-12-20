from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from app.services.tenant_service import TenantService
from app.core.auth import get_current_user, get_current_active_admin

router = APIRouter()
tenant_service = TenantService()

# Pydantic models
class TenantCreate(BaseModel):
    name: str
    code: str
    type: str = "hospital"
    config: Optional[dict] = None

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    config: Optional[dict] = None

class TenantResponse(BaseModel):
    id: str
    name: str
    code: str
    type: str
    status: str
    config: dict
    created_at: str
    updated_at: str

@router.get("")
async def get_tenants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get tenant list with pagination.
    Requires authentication.
    """
    tenants = await tenant_service.get_tenants(skip=skip, limit=limit, status=status)
    return tenants

@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get tenant by ID."""
    tenant = await tenant_service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

@router.get("/code/{code}", response_model=TenantResponse)
async def get_tenant_by_code(
    code: str,
    current_user: dict = Depends(get_current_user)
):
    """Get tenant by code."""
    tenant = await tenant_service.get_tenant_by_code(code)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

@router.post("")
async def create_tenant(
    tenant_data: TenantCreate,
    current_user: dict = Depends(get_current_active_admin)
):
    """
    Create new tenant.
    Requires admin role.
    """
    try:
        tenant = await tenant_service.create_tenant(tenant_data.dict())
        return tenant
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    tenant_data: TenantUpdate,
    current_user: dict = Depends(get_current_active_admin)
):
    """
    Update tenant information.
    Requires admin role.
    """
    tenant = await tenant_service.update_tenant(tenant_id, tenant_data.dict(exclude_unset=True))
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

@router.delete("/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    current_user: dict = Depends(get_current_active_admin)
):
    """
    Delete tenant (soft delete).
    Requires admin role.
    """
    success = await tenant_service.delete_tenant(tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"message": "Tenant deleted successfully"}

@router.get("/{tenant_id}/stats")
async def get_tenant_stats(
    tenant_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get tenant statistics."""
    stats = await tenant_service.get_tenant_stats(tenant_id)
    return stats
