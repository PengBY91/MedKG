from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from app.core.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter()

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "username": user["username"],
            "full_name": user["full_name"],
            "role": user["role"]
        }
    }

@router.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """
    Get current user information.
    """
    return {
        "username": current_user["username"],
        "full_name": current_user["full_name"],
        "email": current_user["email"],
        "role": current_user["role"]
    }
