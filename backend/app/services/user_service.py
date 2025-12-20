from typing import List, Dict, Any, Optional
from datetime import datetime
from app.core.auth import pwd_context

class UserService:
    """User management service."""
    
    def __init__(self):
        # Mock user database (in production, use PostgreSQL)
        # Get default tenant ID from tenant service
        from app.services.tenant_service import TenantService
        tenant_svc = TenantService()
        default_tenant_id = list(tenant_svc.tenants.keys())[0] if tenant_svc.tenants else "default"
        
        self.users = {
            "admin": {
                "id": "1",
                "tenant_id": default_tenant_id,
                "username": "admin",
                "full_name": "Administrator",
                "email": "admin@medical.gov",
                "hashed_password": pwd_context.hash("admin123"),
                "role": "admin",
                "status": "active",
                "created_at": "2024-01-01T00:00:00",
                "last_login": "2024-12-19T20:00:00"
            },
            "reviewer": {
                "id": "2",
                "tenant_id": default_tenant_id,
                "username": "reviewer",
                "full_name": "Medical Reviewer",
                "email": "reviewer@medical.gov",
                "hashed_password": pwd_context.hash("reviewer123"),
                "role": "reviewer",
                "status": "active",
                "created_at": "2024-01-01T00:00:00",
                "last_login": "2024-12-19T19:00:00"
            }
        }
        self.next_id = 3
    
    async def get_users(self, skip: int = 0, limit: int = 100, role: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get user list with pagination and filtering."""
        users = list(self.users.values())
        
        # Filter by role
        if role:
            users = [u for u in users if u["role"] == role]
        
        # Pagination
        users = users[skip:skip + limit]
        
        # Remove sensitive data
        return [{k: v for k, v in user.items() if k != "hashed_password"} for user in users]
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        for user in self.users.values():
            if user["id"] == user_id:
                return {k: v for k, v in user.items() if k != "hashed_password"}
        return None
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new user."""
        # Check if username exists
        if user_data["username"] in self.users:
            raise ValueError("Username already exists")
        
        # Get tenant_id (default to first tenant if not provided)
        tenant_id = user_data.get("tenant_id")
        if not tenant_id:
            from app.services.tenant_service import TenantService
            tenant_svc = TenantService()
            tenant_id = list(tenant_svc.tenants.keys())[0] if tenant_svc.tenants else "default"
        
        # Create user
        user = {
            "id": str(self.next_id),
            "tenant_id": tenant_id,
            "username": user_data["username"],
            "full_name": user_data.get("full_name", ""),
            "email": user_data.get("email", ""),
            "hashed_password": pwd_context.hash(user_data["password"]),
            "role": user_data.get("role", "viewer"),
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "last_login": None
        }
        
        self.users[user["username"]] = user
        self.next_id += 1
        
        return {k: v for k, v in user.items() if k != "hashed_password"}
    
    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user information."""
        # Find user
        user = None
        username_key = None
        for key, u in self.users.items():
            if u["id"] == user_id:
                user = u
                username_key = key
                break
        
        if not user:
            return None
        
        # Update fields
        if "full_name" in user_data:
            user["full_name"] = user_data["full_name"]
        if "email" in user_data:
            user["email"] = user_data["email"]
        if "role" in user_data:
            user["role"] = user_data["role"]
        if "status" in user_data:
            user["status"] = user_data["status"]
        if "password" in user_data:
            user["hashed_password"] = pwd_context.hash(user_data["password"])
        
        return {k: v for k, v in user.items() if k != "hashed_password"}
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user."""
        for key, user in list(self.users.items()):
            if user["id"] == user_id:
                del self.users[key]
                return True
        return False
    
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
