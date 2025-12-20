from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from app.services.user_service import UserService
from app.core.auth import get_current_user, get_current_active_admin

router = APIRouter()
user_service = UserService()

# Pydantic models
class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    email: EmailStr
    role: str = "viewer"

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    status: Optional[str] = None
    password: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    username: str
    full_name: str
    email: str
    role: str
    status: str
    created_at: str
    last_login: Optional[str]

@router.get("")
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    role: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get user list with pagination and filtering.
    Requires authentication.
    """
    users = await user_service.get_users(skip=skip, limit=limit, role=role)
    return users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get user by ID."""
    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(get_current_active_admin)
):
    """
    Create new user.
    Requires admin role.
    """
    try:
        user = await user_service.create_user(user_data.dict())
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_active_admin)
):
    """
    Update user information.
    Requires admin role.
    """
    user = await user_service.update_user(user_id, user_data.dict(exclude_unset=True))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(get_current_active_admin)
):
    """
    Delete user.
    Requires admin role.
    """
    success = await user_service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

@router.get("/{user_id}/stats")
async def get_user_stats(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get user statistics."""
    stats = await user_service.get_user_stats(user_id)
    return stats
