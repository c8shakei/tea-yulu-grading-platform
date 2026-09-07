"""Authentication module: JWT + bcrypt password hashing."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from src.backend import database as db
from src.backend.config import ACCESS_TOKEN_EXPIRE, JWT_ALGORITHM, JWT_SECRET

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class UserRegister(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    user_id: int
    username: str
    role: str


class TokenOut(BaseModel):
    user_id: int
    username: str
    token: str


class MessageOut(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def _create_access_token(user_id: int, username: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + ACCESS_TOKEN_EXPIRE
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _decode_token(token: Optional[str]) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[Dict[str, Any]]:
    """Dependency to resolve current user from JWT. Returns None for anonymous requests."""
    payload = _decode_token(token)
    if not payload:
        return None
    user_id = int(payload.get("sub", 0))
    user = db.get_user_by_id(user_id)
    return user


async def require_user(token: Optional[str] = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """Dependency that requires a valid login token."""
    payload = _decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = int(payload.get("sub", 0))
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


def _resp(data: Any, message: str = "ok", code: int = 0) -> Dict[str, Any]:
    return {"code": code, "message": message, "data": data}


@router.post("/auth/register")
async def register(body: UserRegister):
    """Register a new user."""
    if not body.username or not body.password:
        raise HTTPException(status_code=400, detail="username and password are required")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="password must be at least 6 characters")
    existing = db.get_user_by_username(body.username)
    if existing:
        raise HTTPException(status_code=409, detail="username already exists")
    user_id = db.create_user(body.username, _hash_password(body.password))
    token = _create_access_token(user_id, body.username, "user")
    return _resp(TokenOut(user_id=user_id, username=body.username, token=token).model_dump())


@router.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and return JWT token."""
    user = db.get_user_by_username(form_data.username)
    if not user or not _verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = _create_access_token(user["id"], user["username"], user["role"])
    return _resp(TokenOut(user_id=user["id"], username=user["username"], token=token).model_dump())


@router.get("/auth/me")
async def me(current_user: Dict[str, Any] = Depends(require_user)):
    """Get current logged-in user info."""
    return _resp(UserOut(user_id=current_user["id"], username=current_user["username"], role=current_user["role"]).model_dump())


@router.post("/auth/logout")
async def logout(current_user: Dict[str, Any] = Depends(require_user)):
    """Logout: client should discard token. Server simply acknowledges."""
    return _resp({"message": "logged out"})
