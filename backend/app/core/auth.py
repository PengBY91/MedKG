from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# Configuration
SECRET_KEY = "your-secret-key-change-in-production"  # TODO: Move to env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# Mock user database
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Administrator",
        "email": "admin@medical.gov",
        "hashed_password": pwd_context.hash("admin123"),
        "role": "admin"
    },
    "reviewer": {
        "username": "reviewer",
        "full_name": "Medical Reviewer",
        "email": "reviewer@medical.gov",
        "hashed_password": pwd_context.hash("reviewer123"),
        "role": "reviewer"
    }
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        print(f"[AUTH] Validating token: {token[:20]}...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            print("[AUTH] Token sub is None")
            raise credentials_exception
        print(f"[AUTH] Token sub: {username}")
    except JWTError as e:
        print(f"[AUTH] JWT Decode Error: {str(e)}")
        raise credentials_exception

    
    user = fake_users_db.get(username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user
