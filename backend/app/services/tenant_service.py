from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import json
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.db.models import Tenant as TenantModel

# The Tenant class is replaced by TenantModel

class TenantService:
    """Tenant management service for platform multi-tenancy."""
    
    def __init__(self):
        # We'll use database sessions instead of in-memory dictionary
        # Initialize default tenants if not exists
        self._init_default_tenants()

    def _init_default_tenants(self):
        db = SessionLocal()
        try:
            defaults = [
                {"name": "示范医院", "code": "DEMO_HOSPITAL", "type": "hospital", "config": {"max_users": 100, "features": ["terminology", "rules", "explanation"]}},
                {"name": "市医疗保障局", "code": "INSURANCE_BUREAU", "type": "government", "config": {"max_users": 500, "features": ["terminology", "rules", "policy", "governance"], "is_admin_tenant": True}},
                {"name": "中心城社区卫生服务中心", "code": "COMMUNITY_HEALTH", "type": "clinic", "config": {"max_users": 50, "features": ["terminology", "explanation"]}}
            ]
            for d in defaults:
                existing = db.query(TenantModel).filter(TenantModel.code == d["code"]).first()
                if not existing:
                    new_tenant = TenantModel(
                        id=str(uuid.uuid4()),
                        name=d["name"],
                        code=d["code"],
                        type=d["type"],
                        config=json.dumps(d["config"])
                    )
                    db.add(new_tenant)
            db.commit()
        finally:
            db.close()

    
    async def create_tenant(self, tenant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new tenant in database."""
        db = SessionLocal()
        try:
            existing = db.query(TenantModel).filter(TenantModel.code == tenant_data["code"]).first()
            if existing:
                raise ValueError("Tenant code already exists")
            
            tenant = TenantModel(
                id=str(uuid.uuid4()),
                name=tenant_data["name"],
                code=tenant_data["code"],
                type=tenant_data.get("type", "hospital"),
                config=json.dumps(tenant_data.get("config", {}))
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
            return self._tenant_to_dict(tenant)
        finally:
            db.close()
    
    async def get_tenants(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get tenant list from database."""
        db = SessionLocal()
        try:
            query = db.query(TenantModel)
            if status:
                query = query.filter(TenantModel.status == status)
            
            tenants = query.order_by(TenantModel.created_at.desc()).offset(skip).limit(limit).all()
            return [self._tenant_to_dict(t) for t in tenants]
        finally:
            db.close()
    
    async def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get tenant by ID from database."""
        db = SessionLocal()
        try:
            tenant = db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
            return self._tenant_to_dict(tenant) if tenant else None
        finally:
            db.close()
    
    async def get_tenant_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Get tenant by code from database."""
        db = SessionLocal()
        try:
            tenant = db.query(TenantModel).filter(TenantModel.code == code).first()
            return self._tenant_to_dict(tenant) if tenant else None
        finally:
            db.close()
    
    async def update_tenant(
        self,
        tenant_id: str,
        tenant_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update tenant in database."""
        db = SessionLocal()
        try:
            tenant = db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
            if not tenant:
                return None
            
            if "name" in tenant_data:
                tenant.name = tenant_data["name"]
            if "status" in tenant_data:
                tenant.status = tenant_data["status"]
            if "config" in tenant_data:
                current_config = json.loads(tenant.config) if tenant.config else {}
                current_config.update(tenant_data["config"])
                tenant.config = json.dumps(current_config)
            
            db.commit()
            db.refresh(tenant)
            return self._tenant_to_dict(tenant)
        finally:
            db.close()
    
    async def delete_tenant(self, tenant_id: str) -> bool:
        """Soft delete tenant in database."""
        db = SessionLocal()
        try:
            tenant = db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
            if not tenant:
                return False
            
            tenant.status = "inactive"
            db.commit()
            return True
        finally:
            db.close()
    
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
    
    def _tenant_to_dict(self, tenant: TenantModel) -> Dict[str, Any]:
        """Convert tenant model to dict."""
        return {
            "id": tenant.id,
            "name": tenant.name,
            "code": tenant.code,
            "type": tenant.type,
            "status": tenant.status,
            "config": json.loads(tenant.config) if tenant.config else {},
            "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
            "updated_at": tenant.updated_at.isoformat() if tenant.updated_at else None
        }
