from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from app.core.auth import pwd_context
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.db.models import User as UserModel, Tenant as TenantModel

class UserService:
    """User management service."""
    
    def __init__(self):
        # We'll use database sessions instead of in-memory dictionary
        self._init_default_users()

    def _init_default_users(self):
        db = SessionLocal()
        try:
            # Check for at least one tenant
            default_tenant = db.query(TenantModel).first()
            tenant_id = default_tenant.id if default_tenant else "default"
            
            defaults = [
                {"uid": "1", "username": "admin", "full_name": "Administrator", "email": "admin@medical.gov", "role": "admin"},
                {"uid": "2", "username": "reviewer", "full_name": "Medical Reviewer", "email": "reviewer@medical.gov", "role": "reviewer"}
            ]
            
            for d in defaults:
                existing = db.query(UserModel).filter(UserModel.username == d["username"]).first()
                if not existing:
                    new_user = UserModel(
                        id=str(uuid.uuid4()), # Using UUID instead of simple "1", "2"
                        tenant_id=tenant_id,
                        username=d["username"],
                        full_name=d["full_name"],
                        email=d["email"],
                        hashed_password=pwd_context.hash(f"{d['username']}123"),
                        role=d["role"],
                        status="active"
                    )
                    db.add(new_user)
            db.commit()
        finally:
            db.close()
    
    async def get_users(self, skip: int = 0, limit: int = 100, role: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get user list from database."""
        db = SessionLocal()
        try:
            query = db.query(UserModel)
            if role:
                query = query.filter(UserModel.role == role)
            
            users = query.offset(skip).limit(limit).all()
            return [self._user_to_dict(u) for u in users]
        finally:
            db.close()
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID from database."""
        db = SessionLocal()
        try:
            user = db.query(UserModel).filter(UserModel.id == user_id).first()
            return self._user_to_dict(user) if user else None
        finally:
            db.close()
            
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username for auth."""
        db = SessionLocal()
        try:
            user = db.query(UserModel).filter(UserModel.username == username).first()
            if not user:
                return None
            return {
                "id": user.id,
                "username": user.username,
                "hashed_password": user.hashed_password,
                "tenant_id": user.tenant_id,
                "role": user.role,
                "status": user.status
            }
        finally:
            db.close()
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new user in database."""
        db = SessionLocal()
        try:
            existing = db.query(UserModel).filter(UserModel.username == user_data["username"]).first()
            if existing:
                raise ValueError("Username already exists")
            
            tenant_id = user_data.get("tenant_id")
            if not tenant_id:
                default_tenant = db.query(TenantModel).first()
                tenant_id = default_tenant.id if default_tenant else "default"
                
            new_user = UserModel(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                username=user_data["username"],
                full_name=user_data.get("full_name", ""),
                email=user_data.get("email", ""),
                hashed_password=pwd_context.hash(user_data["password"]),
                role=user_data.get("role", "viewer"),
                status="active"
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return self._user_to_dict(new_user)
        finally:
            db.close()
    
    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user in database."""
        db = SessionLocal()
        try:
            user = db.query(UserModel).filter(UserModel.id == user_id).first()
            if not user:
                return None
                
            if "full_name" in user_data:
                user.full_name = user_data["full_name"]
            if "email" in user_data:
                user.email = user_data["email"]
            if "role" in user_data:
                user.role = user_data["role"]
            if "status" in user_data:
                user.status = user_data["status"]
            if "password" in user_data:
                user.hashed_password = pwd_context.hash(user_data["password"])
                
            db.commit()
            db.refresh(user)
            return self._user_to_dict(user)
        finally:
            db.close()
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user in database."""
        db = SessionLocal()
        try:
            user = db.query(UserModel).filter(UserModel.id == user_id).first()
            if not user:
                return False
            db.delete(user)
            db.commit()
            return True
        finally:
            db.close()
            
    def _user_to_dict(self, user: UserModel) -> Dict:
        return {
            "id": user.id,
            "tenant_id": user.tenant_id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "status": user.status,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics."""
        # Mock statistics
        return {
            "total_reviews": 156,
            "approved": 120,
            "rejected": 36,
            "pending": 12,
            "this_week": 23,
            "accuracy_rate": 0.92
        }
