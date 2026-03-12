from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_store, require_roles
from app.db.store import BaseStore
from app.models.schemas import UserInDB, UserPublic, UserRole, UserRoleUpdate
from app.routes.auth import to_public_user
from app.services.audit import log_action

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[UserPublic])
def list_users(
    _: UserInDB = Depends(require_roles({UserRole.admin, UserRole.manager})),
    store: BaseStore = Depends(get_store),
) -> list[UserPublic]:
    users = store.list_users()
    return [to_public_user(user) for user in users]


@router.patch("/{user_id}/role", response_model=UserPublic)
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
