from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user, get_store
from app.core.security import create_access_token, hash_password, verify_password
from app.db.store import BaseStore
from app.models.schemas import (
    TokenResponse,
    UserCreate,
    UserInDB,
    UserLogin,
    UserPublic,
    UserRole,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def to_public_user(user: UserInDB) -> UserPublic:
    return UserPublic(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        created_at=user.created_at,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, store: BaseStore = Depends(get_store)) -> TokenResponse:
    existing = store.get_user_by_email(payload.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered.")

    # Bootstrap pattern: first registered user becomes admin.
    role = UserRole.admin if store.user_count() == 0 else UserRole.tester
    user = UserInDB(
        name=payload.name,
        email=payload.email,
        role=role,
        password_hash=hash_password(payload.password),
    )
    created = store.create_user(user)
    token = create_access_token(created.id)
    return TokenResponse(access_token=token, user=to_public_user(created))


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, store: BaseStore = Depends(get_store)) -> TokenResponse:
    user = store.get_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=to_public_user(user))


@router.get("/me", response_model=UserPublic)
def me(current_user: UserInDB = Depends(get_current_user)) -> UserPublic:
    return to_public_user(current_user)
