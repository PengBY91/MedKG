from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

class Tenant:
    """Tenant model for multi-tenancy support."""
    def __init__(
        self,
        name: str,
        code: str,
        tenant_type: str = "hospital",
        config: Optional[Dict] = None
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.code = code
        self.type = tenant_type
        self.status = "active"
        self.config = config or {}
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()

class TenantService:
    """Tenant management service for platform multi-tenancy."""
    
    def __init__(self):
        # Mock tenant database (in production, use PostgreSQL)
        self.tenants: Dict[str, Tenant] = {}
        
        # Create default tenant
        default_tenant = Tenant(
            name="示范医院",
            code="DEMO_HOSPITAL",
            tenant_type="hospital",
            config={
                "max_users": 100,
                "features": ["terminology", "rules", "explanation"],
                "storage_quota_gb": 50
            }
        )
        self.tenants[default_tenant.id] = default_tenant

        
        # 2. Insurance Bureau Tenant
        bureau_tenant = Tenant(
            name="市医疗保障局",
            code="INSURANCE_BUREAU",
            tenant_type="government",
            config={
                "max_users": 500,
                "features": ["terminology", "rules", "policy", "governance"],
                "is_admin_tenant": True
            }
        )
        self.tenants[bureau_tenant.id] = bureau_tenant
        
        # 3. Community Health Center
        community_tenant = Tenant(
            name="中心城社区卫生服务中心",
            code="COMMUNITY_HEALTH",
            tenant_type="clinic",
            config={
                "max_users": 50,
                "features": ["terminology", "explanation"],
                "storage_quota_gb": 10
            }
        )
        self.tenants[community_tenant.id] = community_tenant

    
    async def create_tenant(self, tenant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new tenant."""
        # Check if code exists
        for tenant in self.tenants.values():
            if tenant.code == tenant_data["code"]:
                raise ValueError("Tenant code already exists")
        
        tenant = Tenant(
            name=tenant_data["name"],
            code=tenant_data["code"],
            tenant_type=tenant_data.get("type", "hospital"),
            config=tenant_data.get("config", {})
        )
        
        self.tenants[tenant.id] = tenant
        return self._tenant_to_dict(tenant)
    
    async def get_tenants(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get tenant list with pagination."""
        tenants = list(self.tenants.values())
        
        # Filter by status
        if status:
            tenants = [t for t in tenants if t.status == status]
        
        # Sort by created_at
        tenants.sort(key=lambda x: x.created_at, reverse=True)
        
        # Pagination
        tenants = tenants[skip:skip + limit]
        
        return [self._tenant_to_dict(t) for t in tenants]
    
    async def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get tenant by ID."""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return None
        return self._tenant_to_dict(tenant)
    
    async def get_tenant_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Get tenant by code."""
        for tenant in self.tenants.values():
            if tenant.code == code:
                return self._tenant_to_dict(tenant)
        return None
    
    async def update_tenant(
        self,
        tenant_id: str,
        tenant_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update tenant information."""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return None
        
        # Update fields
        if "name" in tenant_data:
            tenant.name = tenant_data["name"]
        if "status" in tenant_data:
            tenant.status = tenant_data["status"]
        if "config" in tenant_data:
            tenant.config.update(tenant_data["config"])
        
        tenant.updated_at = datetime.utcnow().isoformat()
        
        return self._tenant_to_dict(tenant)
    
    async def delete_tenant(self, tenant_id: str) -> bool:
        """Delete tenant (soft delete by setting status to inactive)."""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return False
        
        tenant.status = "inactive"
        tenant.updated_at = datetime.utcnow().isoformat()
        return True
    
    async def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant statistics."""
        # Mock statistics
        return {
            "total_users": 25,
            "active_users": 20,
            "total_documents": 156,
            "total_rules": 45,
            "total_terms": 1200,
            "storage_used_gb": 12.5,
            "api_calls_today": 3420
        }
    
    def _tenant_to_dict(self, tenant: Tenant) -> Dict[str, Any]:
        """Convert tenant to dict."""
        return {
            "id": tenant.id,
            "name": tenant.name,
            "code": tenant.code,
            "type": tenant.type,
            "status": tenant.status,
            "config": tenant.config,
            "created_at": tenant.created_at,
            "updated_at": tenant.updated_at
        }
