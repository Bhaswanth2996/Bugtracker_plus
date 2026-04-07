from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_user, get_store, require_roles
from app.db.store import BaseStore
from app.models.schemas import UserInDB, UserPublic, UserRole, UserRoleUpdate, UserUpdateProfile
from app.routes.auth import to_public_user
from app.services.audit import log_action

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserPublic])
def list_users(
    _: UserInDB = Depends(require_roles({UserRole.admin, UserRole.project_manager})),
    store: BaseStore = Depends(get_store),
) -> list[UserPublic]:
    return [to_public_user(user) for user in store.list_users()]


@router.get("/{user_id}", response_model=UserPublic)
def get_user(
    user_id: str,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> UserPublic:
    if current_user.id != user_id and current_user.role not in {UserRole.admin, UserRole.project_manager}:
        raise HTTPException(status_code=403, detail="Insufficient permissions.")
    user = store.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return to_public_user(user)


@router.put("/me/profile", response_model=UserPublic)
def update_my_profile(
    payload: UserUpdateProfile,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> UserPublic:
    updates = payload.model_dump(exclude_none=True)
    name = updates.pop("name", None)
    updated = store.update_user_profile(current_user.id, updates, name=name)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found.")
    log_action(
        store,
        actor=current_user,
        action="user.profile.updated",
        entity_type="user",
        entity_id=current_user.id,
        details={"fields": list(updates.keys()) + (["name"] if name else [])},
    )
    return to_public_user(updated)


@router.put("/{user_id}/role", response_model=UserPublic)
def update_user_role(
    user_id: str,
    payload: UserRoleUpdate,
    current_user: UserInDB = Depends(require_roles({UserRole.admin})),
    store: BaseStore = Depends(get_store),
) -> UserPublic:
    updated = store.update_user_role(user_id, payload.role)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found.")
    log_action(
        store,
        actor=current_user,
        action="user.role.updated",
        entity_type="user",
        entity_id=user_id,
        details={"role": payload.role.value},
    )
    return to_public_user(updated)
