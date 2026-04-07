from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decode_access_token
from app.db.store import BaseStore
from app.models.schemas import UserInDB, UserRole
from app.services.realtime import RealtimePublisher

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_store(request: Request) -> BaseStore:
    return request.app.state.store


def get_realtime_publisher(request: Request) -> RealtimePublisher:
    hub = getattr(request.app.state, "issues_ws_hub", None)
    event_loop = getattr(request.app.state, "main_event_loop", None)
    return RealtimePublisher(hub=hub, event_loop=event_loop)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    store: BaseStore = Depends(get_store),
) -> UserInDB:
    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )

    user = store.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )
    return user


def require_roles(allowed_roles: set[UserRole]) -> Callable[[UserInDB], UserInDB]:
    def _role_guard(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
        return current_user

    return _role_guard
